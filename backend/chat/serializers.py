from rest_framework import serializers  
from .models import Message  


class ReplyToSerializer(serializers.ModelSerializer):  
    sender = serializers.CharField(source='sender.username', read_only=True)  
    image_url = serializers.SerializerMethodField()  

    class Meta:
        model = Message
        fields = ['id', 'sender', 'text', 'image_url']  

    def get_image_url(self, obj):  
        if not obj.image:  
            return None
        request = self.context.get('request')  
        url = obj.image.url  
        return request.build_absolute_uri(url) if request else url  


class MessageSerializer(serializers.ModelSerializer):  
    sender = serializers.CharField(source='sender.username', read_only=True)  
    image_url = serializers.SerializerMethodField()  
    reply_to = ReplyToSerializer(read_only=True)  

    class Meta:
        model = Message
        fields = ['id', 'sender', 'text', 'image_url', 'timestamp', 'reply_to']  

    def get_image_url(self, obj):  
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url
