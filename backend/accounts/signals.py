import re  
from django.db.models.signals import post_save, m2m_changed  
from django.dispatch import receiver  
from posts.models import Comment  
from .models import Notification, User  


@receiver(post_save, sender=Comment)  
def notify_on_comment(sender, instance, created, **kwargs):  
    if not created:  
        return
    if instance.author != instance.post.author:  
        Notification.objects.create(  
            recipient=instance.post.author,  
            actor=instance.author,  
            type='comment',  
            post=instance.post,  
        )
    for username in set(re.findall(r'@(\w+)', instance.text)):  
        try:
            mentioned = User.objects.get(username=username)  
            if mentioned != instance.author:  
                Notification.objects.get_or_create(  
                    recipient=mentioned,  
                    actor=instance.author,  
                    type='mention',  
                    post=instance.post,  
                )
        except User.DoesNotExist:  
            pass


def _on_post_m2m_changed(notif_type, instance, action, pk_set, delete_on_remove=False):  
    if action == 'post_add' and pk_set:  
        for user_pk in pk_set:  
            if user_pk != instance.author_id:  
                Notification.objects.get_or_create(  
                    recipient=instance.author,  
                    actor_id=user_pk,  
                    type=notif_type,  
                    post=instance,  
                )
    elif delete_on_remove and action == 'post_remove' and pk_set:  
        for user_pk in pk_set:  
            Notification.objects.filter(  
                recipient=instance.author,
                actor_id=user_pk,
                type=notif_type,
                post=instance,
            ).delete()  


def on_likes_changed(sender, instance, action, pk_set, **kwargs):  
    _on_post_m2m_changed('like', instance, action, pk_set, delete_on_remove=True)  


def on_reposted_changed(sender, instance, action, pk_set, **kwargs):  
    _on_post_m2m_changed('repost', instance, action, pk_set)  


def on_following_changed(sender, instance, action, pk_set, **kwargs):  
    if action == 'post_add' and pk_set:  
        for pk in pk_set:  
            Notification.objects.create(  
                recipient_id=pk,  
                actor=instance,  
                type='follow',  
            )  


def _push_to_ws(sender, instance, created, **kwargs):  
    if not created:  
        return
    try:
        from channels.layers import get_channel_layer  
        from asgiref.sync import async_to_sync  
        from django.conf import settings as django_settings  
        _base = getattr(django_settings, 'BACKEND_BASE_URL', 'http://127.0.0.1:8000')  
        avatar_url = (_base + instance.actor.avatar.url) if instance.actor.avatar else None  
        payload = {  
            'type': 'notification_send',  
            'id': instance.id,  
            'actor': instance.actor.username,  
            'actor_avatar': avatar_url,  
            'notif_type': instance.type,  
            'post_id': instance.post_id,  
            'created_at': instance.created_at.isoformat() if instance.created_at else None,  
        }
        async_to_sync(get_channel_layer().group_send)(  
            f'notif_{instance.recipient_id}',  
            payload,  
        )
    except Exception:  
        pass


def connect_signals():  
    from posts.models import Post  
    m2m_changed.connect(on_likes_changed, sender=Post.likes.through)  
    m2m_changed.connect(on_reposted_changed, sender=Post.reposted_by.through)  
    m2m_changed.connect(on_following_changed, sender=User.following.through)  
    post_save.connect(_push_to_ws, sender=Notification)  
