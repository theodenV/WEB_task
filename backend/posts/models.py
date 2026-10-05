from django.conf import settings  
from django.db import models  
from PIL import Image  


def _rgb_to_hsl(r, g, b):  
    r, g, b = r / 255.0, g / 255.0, b / 255.0  
    cmax, cmin = max(r, g, b), min(r, g, b)  
    delta = cmax - cmin  
    l = (cmax + cmin) / 2.0  
    s = 0.0 if delta == 0 else delta / (1 - abs(2 * l - 1))  
    if delta == 0:  
        h = 0.0
    elif cmax == r:  
        h = 60 * (((g - b) / delta) % 6)  
    elif cmax == g:  
        h = 60 * ((b - r) / delta + 2)  
    else:  
        h = 60 * ((r - g) / delta + 4)  
    return round(h) % 360, round(s * 100), round(l * 100)  


def _extract_colors(image_path, min_pixel_frac=0.12):  
    from PIL import Image  
    try:
        img = Image.open(image_path).convert('RGB')  
        img = img.resize((80, 80), Image.LANCZOS)  
        pixels = list(img.getdata())  
        total = len(pixels)  

        BANDS = [  
            (0,   345, 15),   
            (30,  15,  45),   
            (60,  45,  75),   
            (120, 75,  165),  
            (190, 165, 210),  
            (230, 210, 255),  
            (300, 255, 345),  
        ]

        bucket_count = {b[0]: 0 for b in BANDS}  
        bucket_pixels = {b[0]: [] for b in BANDS}  

        for r, g, b in pixels:  
            h, s, l = _rgb_to_hsl(r, g, b)  
            if s < 25 or l < 8 or l > 75:  
                continue
            for hue_key, lo, hi in BANDS:  
                if lo > hi:  
                    if h >= lo or h <= hi:  
                        bucket_count[hue_key] += 1
                        bucket_pixels[hue_key].append((r, g, b))
                        break
                else:  
                    if lo <= h <= hi:
                        bucket_count[hue_key] += 1
                        bucket_pixels[hue_key].append((r, g, b))
                        break

        result = []
        for hue_key, lo, hi in BANDS:
            cnt = bucket_count[hue_key]
            if cnt / total < min_pixel_frac: 
                continue
            pxs = bucket_pixels[hue_key]
            ar = sum(p[0] for p in pxs) // len(pxs)  
            ag = sum(p[1] for p in pxs) // len(pxs) 
            ab = sum(p[2] for p in pxs) // len(pxs)  
            h, s, l = _rgb_to_hsl(ar, ag, ab) 
            result.append({'hex': f'#{ar:02x}{ag:02x}{ab:02x}', 'h': h, 's': s, 'l': l,  
                           '_rank': cnt}) 

        result.sort(key=lambda x: -x.pop('_rank')) 
        if not result:
            avg_l = sum(_rgb_to_hsl(r, g, b)[2] for r, g, b in pixels) / total
            if avg_l < 25: 
                result = [{'hex': '#1a1a1a', 'h': 0, 's': 0, 'l': int(avg_l)}]
            elif avg_l > 75:
                result = [{'hex': '#e8e8e8', 'h': 0, 's': 0, 'l': int(avg_l)}]
            else:
                result = [{'hex': '#888888', 'h': 0, 's': 0, 'l': int(avg_l)}]

        return result[:5]  
    except Exception:  
        return []


class Tag(models.Model):  
    name = models.CharField(max_length=50, unique=True)  
    slug = models.SlugField(max_length=50, unique=True)  

    def __str__(self):  
        return self.name


class Post(models.Model):  
    STATUS_CHOICES = [  
        ('draft', 'Черновик'),         
        ('moderation', 'На модерации'), 
        ('published', 'Опубликован'),   
        ('returned', 'Возвращён'),      
    ]
    MEDIA_TYPE_CHOICES = [('image', 'Image'), ('gif', 'GIF'), ('video', 'Video')]  
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts')  
    image = models.ImageField(upload_to='posts/', blank=True, null=True)  
    video = models.FileField(upload_to='videos/', blank=True, null=True)  
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='image')  
    caption = models.CharField(max_length=300, blank=True)  
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='moderation')  
    created_at = models.DateTimeField(auto_now_add=True)  
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_posts', blank=True)  
    repost_of = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='reposts')  
    reposted_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='reposted_posts', blank=True)  
    tags = models.ManyToManyField(Tag, related_name='posts', blank=True)  
    moderation_locked_by = models.ForeignKey(  
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='moderation_locks',  
    )
    moderation_locked_at = models.DateTimeField(null=True, blank=True)  
    rejection_reason = models.TextField(blank=True, default='')  

    class Meta:
        ordering = ['-created_at']  

    def __str__(self):
        return f'{self.author.username}: {self.caption[:30]}'  

    def save(self, *args, **kwargs):  
        is_new_image = self.pk is None or (  
            Post.objects.filter(pk=self.pk).exclude(image=self.image).exists()  
        )
        super().save(*args, **kwargs)  
        if self.image and not self.image.name.lower().endswith('.gif'):  
            try:
                img = Image.open(self.image.path)  
                max_dim = 1200  
                if img.width > max_dim or img.height > max_dim:  
                    img.thumbnail((max_dim, max_dim), Image.LANCZOS)  
                    img.save(self.image.path, optimize=True, quality=92)  
            except Exception:  
                pass
            if is_new_image:  
                colors = _extract_colors(self.image.path)  
                PostColor.objects.filter(post=self).delete()  
                PostColor.objects.bulk_create([  
                    PostColor(post=self, hex=c['hex'], hue=c['h'], saturation=c['s'], lightness=c['l'])
                    for c in colors
                ])

class PostColor(models.Model):  
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='colors')  
    hex = models.CharField(max_length=7)  
    hue = models.SmallIntegerField()  
    saturation = models.SmallIntegerField()  
    lightness = models.SmallIntegerField()  

    class Meta:
        ordering = ['id']  


class PostReport(models.Model):  
    REASON_CHOICES = [
        ('spam', 'Спам'),
        ('inappropriate', 'Неприемлемый контент'),
        ('copyright', 'Нарушение авторских прав'),
        ('harassment', 'Оскорбление или травля'),
        ('other', 'Другое'),
    ]
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('resolved', 'Принята'),
        ('dismissed', 'Отклонена'),
    ]
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_made')  
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')  
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)  
    comment = models.TextField(blank=True)  
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reporter', 'post')  
        ordering = ['created_at']


class PostImage(models.Model):  
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')  
    image = models.ImageField(upload_to='post_images/')  
    order = models.PositiveIntegerField(default=0)  

    class Meta:
        ordering = ['order']  


class Comment(models.Model):  
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')  
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')  
    text = models.TextField()  
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_comments', blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']  

    def __str__(self):
        return f'{self.author.username}: {self.text[:30]}'

class CommentReport(models.Model):  
    REASON_CHOICES = [
        ('spam', 'Спам'),
        ('inappropriate', 'Неприемлемый контент'),
        ('harassment', 'Оскорбление или травля'),
        ('other', 'Другое'),
    ]
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('resolved', 'Принята'),
        ('dismissed', 'Отклонена'),
    ]
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comment_reports_sent', on_delete=models.CASCADE)  
    comment = models.ForeignKey(Comment, related_name='reports', on_delete=models.CASCADE)  
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)  
    detail = models.TextField(blank=True)  
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reporter', 'comment')  
        ordering = ['created_at']


class Collection(models.Model):  
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collections')  
    name = models.CharField(max_length=100)  
    is_public = models.BooleanField(default=False)  
    posts = models.ManyToManyField(Post, related_name='collections', blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  

    def __str__(self):
        return f'{self.name} ({self.owner.username})'
