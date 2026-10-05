import re  
from django.utils.text import slugify  
from rest_framework import serializers  
from .models import Post, Comment, Collection, Tag, PostReport, PostImage, CommentReport, PostColor  


class TagSerializer(serializers.ModelSerializer):  
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']  


class PostImageSerializer(serializers.ModelSerializer):  
    image_url = serializers.SerializerMethodField()  

    class Meta:
        model = PostImage
        fields = ['id', 'image_url', 'order']  

    def get_image_url(self, obj):  
        request = self.context.get('request')  
        url = obj.image.url  
        return request.build_absolute_uri(url) if request else url  


class PostSerializer(serializers.ModelSerializer):  
    author = serializers.CharField(source='author.username', read_only=True)  
    author_avatar = serializers.SerializerMethodField()  
    likes_count = serializers.SerializerMethodField()  
    comments_count = serializers.SerializerMethodField()  
    reposts_count = serializers.SerializerMethodField()  
    is_liked = serializers.SerializerMethodField()  
    is_reposted = serializers.SerializerMethodField()  
    tags = TagSerializer(many=True, read_only=True)  
    extra_images = PostImageSerializer(source='images', many=True, read_only=True)  
    quoted_post = serializers.SerializerMethodField()  
    dominant_colors = serializers.SerializerMethodField()  

    def get_dominant_colors(self, obj):  
        return [{'hex': c.hex, 'h': c.hue, 's': c.saturation, 'l': c.lightness}
                for c in obj.colors.all()]  

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_avatar', 'image', 'video', 'media_type', 'caption', 'status',
            'rejection_reason', 'created_at', 'likes_count', 'comments_count',
            'reposts_count', 'is_liked', 'is_reposted', 'tags', 'extra_images', 'quoted_post',
            'dominant_colors',
        ]
        read_only_fields = ['status', 'rejection_reason', 'created_at', 'media_type']  

    def get_author_avatar(self, obj):  
        request = self.context.get('request')
        if obj.author.avatar:  
            url = obj.author.avatar.url
            return request.build_absolute_uri(url) if request else url
        return None  

    def get_likes_count(self, obj):  
        return getattr(obj, '_likes_count', obj.likes.count())  

    def get_comments_count(self, obj):  
        return getattr(obj, '_comments_count', obj.comments.count())  

    def get_reposts_count(self, obj):  
        return getattr(obj, '_reposts_count', obj.reposted_by.count())

    def get_is_liked(self, obj):  
        v = getattr(obj, '_is_liked', None)  
        if v is not None:
            return v  
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(pk=request.user.pk).exists()  
        return False  

    def get_is_reposted(self, obj):  
        v = getattr(obj, '_is_reposted', None)
        if v is not None:
            return v
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.reposted_by.filter(pk=request.user.pk).exists()
        return False

    def get_quoted_post(self, obj):  
        if not obj.repost_of_id:  
            return None
        return PostMiniSerializer(obj.repost_of, context=self.context).data  


class PostUpdateSerializer(serializers.ModelSerializer):  
    class Meta:
        model = Post
        fields = ['caption']  


class CommentSerializer(serializers.ModelSerializer):  
    author = serializers.CharField(source='author.username', read_only=True)  
    replies = serializers.SerializerMethodField()  
    likes_count = serializers.SerializerMethodField()  
    is_liked = serializers.SerializerMethodField()  

    class Meta:
        model = Comment
        fields = ['id', 'author', 'text', 'parent', 'created_at', 'replies', 'likes_count', 'is_liked']
        read_only_fields = ['author', 'created_at']  

    def get_replies(self, obj):  
        return CommentSerializer(obj.replies.all(), many=True, context=self.context).data  

    def get_likes_count(self, obj):
        return obj.likes.count()  

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(pk=request.user.pk).exists()
        return False


class CollectionSerializer(serializers.ModelSerializer):  
    owner = serializers.CharField(source='owner.username', read_only=True)  
    posts_count = serializers.IntegerField(source='posts.count', read_only=True)  
    preview_images = serializers.SerializerMethodField()  

    class Meta:
        model = Collection
        fields = ['id', 'name', 'is_public', 'owner', 'posts_count', 'preview_images', 'created_at']
        read_only_fields = ['owner', 'created_at']

    def get_preview_images(self, obj):  
        request = self.context.get('request')
        imgs = []
        for p in obj.posts.all()[:3]:  
            if p.image:  
                url = p.image.url
                imgs.append(request.build_absolute_uri(url) if request else url)
        return imgs  


class CollectionDetailSerializer(serializers.ModelSerializer):  
    owner = serializers.CharField(source='owner.username', read_only=True)
    posts = PostSerializer(many=True, read_only=True)  

    class Meta:
        model = Collection
        fields = ['id', 'name', 'is_public', 'owner', 'posts', 'created_at']
        read_only_fields = ['owner', 'created_at']


class PostMiniSerializer(serializers.ModelSerializer):  
    author = serializers.CharField(source='author.username', read_only=True)
    author_avatar = serializers.SerializerMethodField()  
    extra_images = PostImageSerializer(source='images', many=True, read_only=True)  

    class Meta:
        model = Post
        fields = ['id', 'author', 'author_avatar', 'image', 'video', 'media_type', 'caption', 'created_at', 'status', 'rejection_reason', 'extra_images']

    def get_author_avatar(self, obj):
        request = self.context.get('request')
        if obj.author.avatar:
            url = obj.author.avatar.url
            return request.build_absolute_uri(url) if request else url
        return None


class PostReportSerializer(serializers.ModelSerializer):  
    reporter = serializers.CharField(source='reporter.username', read_only=True)  
    post_id = serializers.IntegerField(source='post.id', read_only=True)  
    post_author = serializers.CharField(source='post.author.username', read_only=True)  
    post_image = serializers.SerializerMethodField()  
    post_caption = serializers.CharField(source='post.caption', read_only=True)  
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)  

    class Meta:
        model = PostReport
        fields = [
            'id', 'reporter', 'post_id', 'post_author', 'post_image', 'post_caption',
            'reason', 'reason_display', 'comment', 'status', 'created_at',
        ]

    def get_post_image(self, obj):  
        request = self.context.get('request')
        if obj.post.image:
            url = obj.post.image.url
            return request.build_absolute_uri(url) if request else url
        return None


class CommentReportSerializer(serializers.ModelSerializer):  
    reporter = serializers.CharField(source='reporter.username', read_only=True)
    comment_author = serializers.CharField(source='comment.author.username', read_only=True)  
    comment_text = serializers.CharField(source='comment.text', read_only=True)  
    post_id = serializers.IntegerField(source='comment.post_id', read_only=True)  
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)

    class Meta:
        model = CommentReport
        fields = ['id', 'reporter', 'comment_author', 'comment_text', 'post_id', 'reason', 'reason_display', 'detail', 'status', 'created_at']


def extract_tags(caption):  
    names = re.findall(r'#(\w+)', caption, re.UNICODE)
    result = []
    for name in names:
        slug = slugify(name, allow_unicode=True)  
        if slug:  
            tag, _ = Tag.objects.get_or_create(slug=slug, defaults={'name': name.lower()})  
            result.append(tag)  
    return result  
