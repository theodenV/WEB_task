import re  
from rest_framework import serializers  
from django.contrib.auth import get_user_model  
from .models import Notification, Block, FollowRequest, UserReport  

User = get_user_model()  


class UserSerializer(serializers.ModelSerializer):  
    is_moderator = serializers.BooleanField(read_only=True)  

    class Meta:  
        model = User  
        fields = [  
            'id', 'username', 'email', 'phone', 'first_name', 'last_name',
            'bio', 'avatar', 'is_staff', 'is_moderator', 'birth_date',
        ]


class MeSerializer(serializers.ModelSerializer):  
    is_moderator = serializers.BooleanField(read_only=True)  

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'first_name', 'last_name',
            'bio', 'avatar', 'cover', 'is_staff', 'is_moderator', 'birth_date',
            'is_private', 'dm_privacy', 'comment_privacy',  
        ]
        read_only_fields = ['id', 'username', 'is_staff', 'is_moderator']  


class UserMiniSerializer(serializers.ModelSerializer):  
    is_following = serializers.SerializerMethodField()  
    is_online = serializers.SerializerMethodField()  

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar', 'is_following', 'is_online']

    def get_is_following(self, obj):  
        request = self.context.get('request')  
        if request and request.user.is_authenticated:  
            return obj in request.user.following.all()  
        return False  

    def get_is_online(self, obj):  
        from django.core.cache import cache  
        return bool(cache.get(f'online_{obj.pk}'))  


class RegisterSerializer(serializers.ModelSerializer):  
    password = serializers.CharField(write_only=True, min_length=8)  
    last_name = serializers.CharField(required=False, allow_blank=True)  
    birth_date = serializers.DateField(required=False, allow_null=True)  

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password', 'first_name', 'last_name', 'birth_date']

    def validate_username(self, value):  
        if ' ' in value:  
            raise serializers.ValidationError('Без пробелов.')  
        if not re.match(r'^[A-Za-z0-9_]+$', value):  
            raise serializers.ValidationError('Только латиница, цифры и _.')
        return value  

    def validate_phone(self, value):  
        if value and not re.match(r'^\+?\d{10,15}$', value):  
            raise serializers.ValidationError('Телефон в формате +79991234567.')
        return value

    def create(self, validated_data):  
        birth_date = validated_data.pop('birth_date', None)  
        last_name = validated_data.pop('last_name', '')  
        first_name = validated_data.pop('first_name', '')  
        user = User.objects.create_user(  
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],  
            phone=validated_data.get('phone', ''),
            first_name=first_name,
            last_name=last_name,
        )
        if birth_date:  
            user.birth_date = birth_date
            user.save(update_fields=['birth_date'])  
        return user  


class UserProfileSerializer(serializers.ModelSerializer):  
    followers_count = serializers.IntegerField(source='followers.count', read_only=True)  
    following_count = serializers.IntegerField(source='following.count', read_only=True)  
    is_following = serializers.SerializerMethodField()  
    is_online = serializers.SerializerMethodField()  
    last_online = serializers.SerializerMethodField()  
    is_moderator = serializers.BooleanField(read_only=True)  
    collections = serializers.SerializerMethodField()  
    is_blocked = serializers.SerializerMethodField()  
    is_blocking_me = serializers.SerializerMethodField()  
    has_pending_request = serializers.SerializerMethodField()  

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'username', 'bio', 'avatar', 'cover', 'is_staff', 'is_moderator',
            'followers_count', 'following_count', 'is_following', 'is_online', 'last_online', 'collections',
            'is_private', 'is_blocked', 'is_blocking_me', 'has_pending_request',
            'comment_privacy', 'dm_privacy',
        ]

    def get_is_following(self, obj):  
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj in request.user.following.all()
        return False

    def get_is_online(self, obj):  
        from django.core.cache import cache
        return bool(cache.get(f'online_{obj.pk}'))

    def get_last_online(self, obj):  
        from django.core.cache import cache
        cached = cache.get(f'online_time_{obj.pk}')  
        if cached:
            return cached  
        if obj.last_login:  
            return obj.last_login.isoformat()
        return None  

    def get_collections(self, obj):  
        from posts.serializers import CollectionSerializer  
        request = self.context.get('request')
        qs = obj.collections.all()  
        if not (request and request.user.is_authenticated and request.user == obj):  
            qs = qs.filter(is_public=True)  
        return CollectionSerializer(qs, many=True, context=self.context).data  

    def get_is_blocked(self, obj):  
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user != obj:  
            return obj.blocked_by.filter(blocker=request.user).exists()  
        return False

    def get_is_blocking_me(self, obj):  
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user != obj:
            return obj.blocking.filter(blocked=request.user).exists()  
        return False

    def get_has_pending_request(self, obj):  
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user != obj:
            return obj.received_follow_requests.filter(from_user=request.user).exists()
        return False


class ChangePasswordSerializer(serializers.Serializer):  
    old_password = serializers.CharField(required=True)  
    new_password = serializers.CharField(required=True, min_length=8)  


class FollowRequestSerializer(serializers.ModelSerializer):  
    from_user = serializers.CharField(source='from_user.username', read_only=True)  
    from_user_avatar = serializers.SerializerMethodField()  

    class Meta:
        model = FollowRequest
        fields = ['id', 'from_user', 'from_user_avatar', 'created_at']

    def get_from_user_avatar(self, obj):  
        request = self.context.get('request')
        if obj.from_user.avatar:
            url = obj.from_user.avatar.url  
            return request.build_absolute_uri(url) if request else url  
        return None


class BlockedUserSerializer(serializers.ModelSerializer):  
    username = serializers.CharField(source='blocked.username', read_only=True)  
    avatar = serializers.SerializerMethodField()  

    class Meta:
        model = Block  
        fields = ['id', 'username', 'avatar', 'created_at']

    def get_avatar(self, obj):  
        request = self.context.get('request')
        if obj.blocked.avatar:
            url = obj.blocked.avatar.url
            return request.build_absolute_uri(url) if request else url
        return None


class UserReportSerializer(serializers.ModelSerializer):  
    reporter = serializers.CharField(source='reporter.username', read_only=True)  
    reported_user = serializers.CharField(source='reported_user.username', read_only=True)  
    reported_user_avatar = serializers.SerializerMethodField()  
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)  

    class Meta:
        model = UserReport
        fields = ['id', 'reporter', 'reported_user', 'reported_user_avatar', 'reason', 'reason_display', 'detail', 'status', 'created_at']

    def get_reported_user_avatar(self, obj):  
        request = self.context.get('request')
        if obj.reported_user.avatar:
            url = obj.reported_user.avatar.url
            return request.build_absolute_uri(url) if request else url
        return None


class NotificationSerializer(serializers.ModelSerializer):  
    actor = serializers.CharField(source='actor.username', read_only=True)  
    actor_avatar = serializers.SerializerMethodField()  
    post_id = serializers.IntegerField(source='post.id', read_only=True, allow_null=True)  

    class Meta:
        model = Notification
        fields = ['id', 'actor', 'actor_avatar', 'type', 'post_id', 'is_read', 'created_at']

    def get_actor_avatar(self, obj):  
        request = self.context.get('request')
        if obj.actor.avatar:
            url = obj.actor.avatar.url
            return request.build_absolute_uri(url) if request else url
        return None
