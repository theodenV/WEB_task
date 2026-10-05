import json  
from channels.generic.websocket import AsyncWebsocketConsumer  
from channels.db import database_sync_to_async  
from django.contrib.auth import get_user_model  
from .models import Message  

User = get_user_model()  


class ChatConsumer(AsyncWebsocketConsumer):  
    async def connect(self):  
        self.user = self.scope['user']  
        if not self.user.is_authenticated:  
            await self.close()
            return
        self.other_username = self.scope['url_route']['kwargs']['username']  
        self.other_user = await self.get_user(self.other_username)  
        if self.other_user is None:  
            await self.close()
            return
        ids = sorted([self.user.id, self.other_user.id])  
        self.room_group_name = f'chat_{ids[0]}_{ids[1]}'  
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)  
        await self.accept()  

    async def disconnect(self, close_code):  
        if hasattr(self, 'room_group_name'):  
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)  

    async def receive(self, text_data):  
        data = json.loads(text_data)  
        msg_type = data.get('type', 'message')  

        if msg_type == 'typing':  
            await self.channel_layer.group_send(self.room_group_name, {  
                'type': 'chat_typing',  
                'sender': self.user.username,  
            })
            return  

        text = data.get('message', '').strip()  
        if not text:  
            return
        reply_to_id = data.get('reply_to_id')  
        msg = await self.save_message(text, reply_to_id)  

        reply_to_data = None  
        if msg.reply_to:  
            reply_to_data = {  
                'id': msg.reply_to.id,
                'sender': msg.reply_to.sender.username,
                'text': msg.reply_to.text[:120],  
                'image_url': None,  
            }

        await self.channel_layer.group_send(self.room_group_name, {  
            'type': 'chat_message',  
            'msg_id': msg.id,  
            'message': text,  
            'sender': self.user.username,  
            'timestamp': msg.timestamp.isoformat(),  
            'reply_to': reply_to_data,  
        })
        await self.channel_layer.group_send(  
            f'notif_{self.other_user.id}',  
            {'type': 'chat_notify', 'sender': self.user.username},  
        )

    async def chat_message(self, event):  
        await self.send(text_data=json.dumps({  
            'type': 'message',  
            'msg_id': event.get('msg_id'),
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
            'reply_to': event.get('reply_to'),
        }))

    async def chat_typing(self, event):  
        if event['sender'] != self.user.username:  
            await self.send(text_data=json.dumps({
                'type': 'typing',  
                'sender': event['sender'],  
            }))

    @database_sync_to_async  
    def get_user(self, username):  
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None  

    @database_sync_to_async  
    def save_message(self, text, reply_to_id=None):  
        msg = Message.objects.create(  
            sender=self.user,  
            recipient=self.other_user,  
            text=text,  
            reply_to_id=reply_to_id,  
        )
        if reply_to_id:  
            msg.reply_to = Message.objects.select_related('sender').filter(id=reply_to_id).first()  
        return msg  
