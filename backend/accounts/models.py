from django.conf import settings  
from django.contrib.auth.models import AbstractUser  
from django.db import models  


class User(AbstractUser):  
    phone = models.CharField(max_length=20, blank=True)  
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)  
    cover = models.ImageField(upload_to='covers/', blank=True, null=True)  
    bio = models.TextField(blank=True)  
    following = models.ManyToManyField(  
        'self',  
        symmetrical=False,  
        related_name='followers',  
        blank=True,  
    )
    birth_date = models.DateField(null=True, blank=True)  

    is_banned = models.BooleanField(default=False)  
    ban_reason = models.TextField(blank=True)  

    is_private = models.BooleanField(default=False)  

    dm_privacy = models.CharField(  
        max_length=10,
        choices=[('all', 'Все'), ('following', 'Подписчики'), ('none', 'Никто')],  
        default='all',  
    )
    comment_privacy = models.CharField(  
        max_length=10,
        choices=[('all', 'Все'), ('following', 'Подписчики'), ('none', 'Никто')],  
        default='all',  
    )

    @property  
    def is_moderator(self):  
        return self.is_staff or self.groups.filter(name='Moderators').exists()  


class Block(models.Model):  
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocking', on_delete=models.CASCADE)  
    blocked = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocked_by', on_delete=models.CASCADE)  
    created_at = models.DateTimeField(auto_now_add=True)  

    class Meta:  
        unique_together = ('blocker', 'blocked')  


class FollowRequest(models.Model):  
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_follow_requests', on_delete=models.CASCADE)  
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_follow_requests', on_delete=models.CASCADE)  
    created_at = models.DateTimeField(auto_now_add=True)  

    class Meta:
        unique_together = ('from_user', 'to_user')  
        ordering = ['-created_at']  


class UserReport(models.Model):  
    REASON_CHOICES = [  
        ('spam', 'Спам'),
        ('inappropriate', 'Неприемлемый контент'),
        ('harassment', 'Оскорбление или травля'),
        ('fake', 'Фейковый аккаунт'),
        ('other', 'Другое'),
    ]
    STATUS_CHOICES = [  
        ('pending', 'На рассмотрении'),  
        ('resolved', 'Принята'),  
        ('dismissed', 'Отклонена'),  
    ]
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_reports_sent', on_delete=models.CASCADE)  
    reported_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reports_received', on_delete=models.CASCADE)  
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)  
    detail = models.TextField(blank=True)  
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  
    created_at = models.DateTimeField(auto_now_add=True)  

    class Meta:
        unique_together = ('reporter', 'reported_user')  
        ordering = ['created_at']  


class Notification(models.Model):  
    TYPES = [  
        ('like', 'Лайк'),          
        ('comment', 'Комментарий'), 
        ('follow', 'Подписка'),     
        ('repost', 'Репост'),       
        ('mention', 'Упоминание'),  
    ]
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')  
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')  
    type = models.CharField(max_length=20, choices=TYPES)  
    post = models.ForeignKey('posts.Post', null=True, blank=True, on_delete=models.CASCADE)  
    is_read = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)  

    class Meta:
        ordering = ['-created_at']  
