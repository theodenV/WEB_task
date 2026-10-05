import json  
from channels.generic.websocket import AsyncWebsocketConsumer  
from asgiref.sync import sync_to_async  
from django.core.cache import cache  


def _set_online(user_id):  
    cache.set(f'online_{user_id}', 1, timeout=None)  


def _clear_online(user_id):  
    from django.utils.timezone import now  
    cache.set(f'online_time_{user_id}', now().isoformat(), timeout=30 * 24 * 3600)  
    cache.delete(f'online_{user_id}')  


class NotificationsConsumer(AsyncWebsocketConsumer):  
    async def connect(self):  
        self.user = self.scope['user']  
        if not self.user.is_authenticated:  
            await self.close()  
            return  
        self.group_name = f'notif_{self.user.id}'  
        await self.channel_layer.group_add(self.group_name, self.channel_name)  
        if self.user.is_staff or getattr(self.user, 'is_moderator', False):  
            await self.channel_layer.group_add('notif_moderators', self.channel_name)  
        await sync_to_async(_set_online)(self.user.id)  
        await self.accept()  

    async def disconnect(self, close_code):  
        if hasattr(self, 'group_name'):  
            await self.channel_layer.group_discard(self.group_name, self.channel_name)  
        if hasattr(self, 'user') and self.user.is_authenticated:  
            if self.user.is_staff or getattr(self.user, 'is_moderator', False):  
                await self.channel_layer.group_discard('notif_moderators', self.channel_name)  
            await sync_to_async(_clear_online)(self.user.id)  

    async def receive(self, text_data):  
        pass  

    async def notification_send(self, event):  
        await self.send(text_data=json.dumps({  
            'type': 'notification',  
            'id': event.get('id'),  
            'actor': event.get('actor'),  
            'actor_avatar': event.get('actor_avatar'),  
            'notif_type': event.get('notif_type'),  
            'post_id': event.get('post_id'),  
            'created_at': event.get('created_at'),  
        }))

    async def moderation_new(self, event):  
        await self.send(text_data=json.dumps({  
            'notif_type': 'moderation_new',  
            'post_id': event.get('post_id'),  
        }))

    async def chat_notify(self, event):  
        await self.send(text_data=json.dumps({  
            'notif_type': 'chat_message',  
            'sender': event.get('sender'),  
        }))
