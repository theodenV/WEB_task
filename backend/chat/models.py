from django.conf import settings  
from django.db import models  


class Message(models.Model):  
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')  
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')  
    text = models.TextField(blank=True)  
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)  
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')  
    timestamp = models.DateTimeField(auto_now_add=True)  

    class Meta:
        ordering = ['timestamp']  
