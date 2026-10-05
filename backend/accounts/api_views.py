import uuid  
from django.contrib.auth import get_user_model  
from django.core.cache import cache  
from django.shortcuts import get_object_or_404  
from rest_framework import generics, permissions, status  
from rest_framework.views import APIView  
from rest_framework.response import Response  
from rest_framework.authtoken.models import Token  
from .models import Notification, Block, FollowRequest, UserReport  
from .serializers import (  
    RegisterSerializer, UserSerializer, UserProfileSerializer,
    MeSerializer, NotificationSerializer, UserMiniSerializer, ChangePasswordSerializer,
    FollowRequestSerializer, BlockedUserSerializer, UserReportSerializer,
)
from .permissions import IsModerator  

User = get_user_model()  


class RegisterAPI(generics.CreateAPIView):  
    serializer_class = RegisterSerializer  
    permission_classes = [permissions.AllowAny]  

    def create(self, request, *args, **kwargs):  
        serializer = self.get_serializer(data=request.data)  
        serializer.is_valid(raise_exception=True)  
        user = serializer.save()  
        token, _ = Token.objects.get_or_create(user=user)  
        return Response({'token': token.key, 'user': UserSerializer(user, context={'request': request}).data})  


class LoginAPI(APIView):  
    permission_classes = [permissions.AllowAny]  

    def post(self, request):  
        login = request.data.get('username', '').strip()  
        password = request.data.get('password', '')  
        if '@' in login:  
            try:
                found = User.objects.get(email__iexact=login)  
                login = found.username  
            except User.DoesNotExist:
                pass  
        from django.contrib.auth import authenticate  
        user = authenticate(request, username=login, password=password)  
        if not user:  
            return Response({'detail': 'Неверный логин/email или пароль'}, status=status.HTTP_400_BAD_REQUEST)
        if user.is_banned:  
            return Response({'detail': 'Ваш аккаунт заблокирован.', 'ban_reason': user.ban_reason, 'code': 'account_banned'}, status=status.HTTP_403_FORBIDDEN)
        from django.contrib.auth.models import update_last_login  
        update_last_login(None, user)  
        token, _ = Token.objects.get_or_create(user=user)  
        return Response({'token': token.key, 'user': UserSerializer(user, context={'request': request}).data})  


class MeAPI(generics.RetrieveUpdateAPIView):  
    serializer_class = MeSerializer  
    permission_classes = [permissions.IsAuthenticated]  

    def get_object(self):  
        return self.request.user  


class ChangePasswordAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        s = ChangePasswordSerializer(data=request.data)  
        s.is_valid(raise_exception=True)  
        user = request.user
        if not user.check_password(s.validated_data['old_password']):  
            return Response({'old_password': 'Неверный текущий пароль'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(s.validated_data['new_password'])  
        user.save()  
        Token.objects.filter(user=user).delete()  
        token = Token.objects.create(user=user)  
        return Response({'token': token.key})  


class UserProfileAPI(generics.RetrieveAPIView):  
    serializer_class = UserProfileSerializer  
    queryset = User.objects.all()  
    lookup_field = 'username'  


class FollowToggleAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        target = get_object_or_404(User, username=username)  
        if target == request.user:  
            return Response({'detail': 'Нельзя подписаться на себя'}, status=status.HTTP_400_BAD_REQUEST)
        if Block.objects.filter(blocker=target, blocked=request.user).exists():  
            return Response({'detail': 'Недоступно'}, status=status.HTTP_403_FORBIDDEN)
        if target in request.user.following.all():  
            request.user.following.remove(target)  
            return Response({'following': False, 'requested': False, 'followers_count': target.followers.count()})
        if target.is_private:  
            existing = FollowRequest.objects.filter(from_user=request.user, to_user=target).first()  
            if existing:  
                existing.delete()
                return Response({'following': False, 'requested': False, 'followers_count': target.followers.count()})
            FollowRequest.objects.create(from_user=request.user, to_user=target)  
            return Response({'following': False, 'requested': True, 'followers_count': target.followers.count()})
        request.user.following.add(target)  
        return Response({'following': True, 'requested': False, 'followers_count': target.followers.count()})


class NotificationListAPI(generics.ListAPIView):  
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.notifications.select_related('actor', 'post').all()[:50]  


class NotificationMarkReadAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        self.request.user.notifications.filter(is_read=False).update(is_read=True)  
        return Response({'detail': 'ok'})


class NotificationUnreadCountAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = request.user.notifications.filter(is_read=False).count()  
        return Response({'count': count})


class NotificationDeleteAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk=None):  
        if pk:  
            get_object_or_404(Notification, pk=pk, recipient=request.user).delete()  
        else:  
            request.user.notifications.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)  


class UserSearchAPI(generics.ListAPIView):  
    serializer_class = UserMiniSerializer
    permission_classes = [permissions.AllowAny]  

    def get_queryset(self):
        q = self.request.query_params.get('q', '').strip()  
        if not q:  
            return User.objects.none()  
        return User.objects.filter(username__icontains=q)[:20]  


class FollowerListAPI(generics.ListAPIView):  
    serializer_class = UserMiniSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs['username'])  
        return user.followers.all()[:100]  


class FollowingListAPI(generics.ListAPIView):  
    serializer_class = UserMiniSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return user.following.all()[:100]


class DeleteAccountAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        request.user.delete()  
        return Response(status=status.HTTP_204_NO_CONTENT)


class WsTicketAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ticket = str(uuid.uuid4())  
        cache.set(f'ws_ticket:{ticket}', request.user.pk, timeout=30)  
        return Response({'ticket': ticket})  


class BlockToggleAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        if target == request.user:
            return Response({'detail': 'Нельзя заблокировать себя'}, status=status.HTTP_400_BAD_REQUEST)
        block = Block.objects.filter(blocker=request.user, blocked=target).first()  
        if block:  
            block.delete()  
            request.user.following.remove(target)  
            return Response({'blocked': False})
        Block.objects.create(blocker=request.user, blocked=target)  
        request.user.following.remove(target)  
        target.following.remove(request.user)  
        FollowRequest.objects.filter(from_user=request.user, to_user=target).delete()  
        FollowRequest.objects.filter(from_user=target, to_user=request.user).delete()  
        return Response({'blocked': True})


class BlockedUsersListAPI(generics.ListAPIView):  
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BlockedUserSerializer

    def get_queryset(self):
        return Block.objects.filter(blocker=self.request.user).select_related('blocked')  


class FollowRequestListAPI(generics.ListAPIView):  
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FollowRequestSerializer

    def get_queryset(self):
        return FollowRequest.objects.filter(to_user=self.request.user).select_related('from_user')


class FollowRequestActionAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        req = get_object_or_404(FollowRequest, pk=pk, to_user=request.user)  
        action = request.data.get('action')  
        if action == 'accept':  
            req.from_user.following.add(request.user)  
            req.delete()  
            return Response({'detail': 'accepted'})
        if action == 'reject':  
            req.delete()  
            return Response({'detail': 'rejected'})
        return Response({'detail': 'invalid action'}, status=status.HTTP_400_BAD_REQUEST)


class UserReportAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        if target == request.user:
            return Response({'detail': 'Нельзя жаловаться на себя'}, status=status.HTTP_400_BAD_REQUEST)
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'detail': 'Укажи причину'}, status=status.HTTP_400_BAD_REQUEST)
        _, created = UserReport.objects.get_or_create(  
            reporter=request.user, reported_user=target,  
            defaults={'reason': reason, 'detail': request.data.get('detail', '')},  
        )
        if not created:  
            return Response({'detail': 'Жалоба уже отправлена'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'ok'})


class BanUserAPI(APIView):  
    permission_classes = [IsModerator]  

    def post(self, request, username):  
        target = get_object_or_404(User, username=username)
        if target.is_staff:  
            return Response({'detail': 'Нельзя заблокировать администратора'}, status=status.HTTP_403_FORBIDDEN)
        reason = request.data.get('reason', '').strip()
        target.is_banned = True  
        target.ban_reason = reason  
        target.save(update_fields=['is_banned', 'ban_reason'])  
        Token.objects.filter(user=target).delete()  
        return Response({'detail': 'ok'})

    def delete(self, request, username):  
        target = get_object_or_404(User, username=username)
        target.is_banned = False  
        target.ban_reason = ''  
        target.save(update_fields=['is_banned', 'ban_reason'])
        return Response({'detail': 'ok'})


class AdminUserListAPI(APIView):  
    permission_classes = [IsModerator]

    def get(self, request):
        q = request.query_params.get('q', '').strip()  
        qs = User.objects.order_by('username')  
        if q:
            qs = qs.filter(username__icontains=q)
        data = [  
            {
                'id': u.id, 'username': u.username, 'email': u.email,
                'is_banned': u.is_banned, 'ban_reason': u.ban_reason,
                'is_staff': u.is_staff, 'date_joined': u.date_joined,
            }
            for u in qs[:100]  
        ]
        return Response(data)


class UserReportListAPI(generics.ListAPIView):  
    permission_classes = [IsModerator]
    serializer_class = UserReportSerializer

    def get_queryset(self):
        return UserReport.objects.filter(status='pending').select_related('reporter', 'reported_user')  


class UserReportActionAPI(APIView):  
    permission_classes = [IsModerator]

    def post(self, request, pk):
        report = get_object_or_404(UserReport, pk=pk)
        action = request.data.get('action')  
        if action == 'ban':  
            target = report.reported_user
            if not target.is_staff:  
                target.is_banned = True
                target.ban_reason = f'Нарушение правил: {report.get_reason_display()}'  
                target.save(update_fields=['is_banned', 'ban_reason'])
                Token.objects.filter(user=target).delete()  
            report.status = 'resolved'  
            report.save(update_fields=['status'])
            return Response({'detail': 'ok'})
        if action == 'dismiss':  
            report.status = 'dismissed'
            report.save(update_fields=['status'])
            return Response({'detail': 'ok'})
        return Response({'detail': 'invalid action'}, status=status.HTTP_400_BAD_REQUEST)
