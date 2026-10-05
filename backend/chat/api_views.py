from django.contrib.auth import get_user_model  
from django.core.cache import cache  
from django.db.models import Q, Max, Subquery, OuterRef  
from django.shortcuts import get_object_or_404  
from rest_framework import generics, permissions  
from rest_framework.views import APIView  
from rest_framework.response import Response  
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser  
from .models import Message  
from .serializers import MessageSerializer  

User = get_user_model()  


class InboxAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]  

    def get(self, request):
        user = request.user  
        sent = Message.objects.filter(sender=user).values_list('recipient_id', flat=True)  
        recv = Message.objects.filter(recipient=user).values_list('sender_id', flat=True)  
        partner_ids = set(sent) | set(recv)  

        result = []  
        for partner in User.objects.filter(id__in=partner_ids).select_related():  
            last_msg = Message.objects.filter(  
                Q(sender=user, recipient=partner) | Q(sender=partner, recipient=user)  
            ).order_by('-timestamp').first()  
            avatar_url = None  
            if partner.avatar:  
                avatar_url = request.build_absolute_uri(partner.avatar.url)  
            last_online_cached = cache.get(f'online_time_{partner.id}')  
            last_online = last_online_cached or (partner.last_login.isoformat() if partner.last_login else None)  
            result.append({  
                'id': partner.id,
                'username': partner.username,
                'first_name': partner.first_name,
                'avatar': avatar_url,
                'last_message': last_msg.text if last_msg else '',  
                'last_image': bool(last_msg and last_msg.image),  
                'last_timestamp': last_msg.timestamp.isoformat() if last_msg else None,  
                'is_online': bool(cache.get(f'online_{partner.id}')),  
                'last_online': last_online,  
            })
        result.sort(key=lambda x: x['last_timestamp'] or '', reverse=True)  
        return Response(result)


class ConversationAPI(generics.ListAPIView):  
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        other = get_object_or_404(User, username=self.kwargs['username'])  
        return Message.objects.filter(  
            Q(sender=self.request.user, recipient=other) | Q(sender=other, recipient=self.request.user)  
        ).select_related('reply_to__sender')  


class MessageDeleteAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        msg = get_object_or_404(Message, pk=pk, sender=request.user)  
        msg.delete()  
        return Response(status=204)  


class SendImageAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  

    def post(self, request, username):
        other = get_object_or_404(User, username=username)  
        image = request.FILES.get('image')  
        if not image:  
            return Response({'detail': 'Файл не передан'}, status=400)
        msg = Message.objects.create(sender=request.user, recipient=other, image=image)  
        return Response(MessageSerializer(msg, context={'request': request}).data)  
