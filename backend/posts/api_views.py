from django.core.cache import cache  
from django.db.models import Count, Exists, OuterRef, Q  
from django.shortcuts import get_object_or_404  
from rest_framework import generics, permissions, status  
from rest_framework.pagination import PageNumberPagination  
from rest_framework.views import APIView  
from rest_framework.response import Response  
from rest_framework.exceptions import PermissionDenied, NotFound  
from .models import Post, Comment, Collection, Tag, PostReport, PostImage, CommentReport, PostColor  
from .serializers import (  
    PostSerializer, PostUpdateSerializer, CommentSerializer,
    CollectionSerializer, CollectionDetailSerializer, TagSerializer,
    extract_tags, PostMiniSerializer, PostReportSerializer, PostImageSerializer,
    CommentReportSerializer,
)
from accounts.permissions import IsModerator  


class PostPagination(PageNumberPagination):  
    page_size = 20  
    page_size_query_param = 'page_size'  
    max_page_size = 100  


def annotate_posts(qs, user):  
    qs = qs.select_related('author', 'repost_of__author').annotate(  
        _likes_count=Count('likes', distinct=True),  
        _comments_count=Count('comments', distinct=True),  
        _reposts_count=Count('reposted_by', distinct=True),  
    )
    if user.is_authenticated:  
        qs = qs.annotate(
            _is_liked=Exists(user.liked_posts.filter(pk=OuterRef('pk'))),  
            _is_reposted=Exists(user.reposted_posts.filter(pk=OuterRef('pk'))),  
        )
    return qs.prefetch_related('tags', 'colors')  


class PostListCreateAPI(generics.ListCreateAPIView):  
    serializer_class = PostSerializer  
    pagination_class = PostPagination  

    def get_queryset(self):  
        user = self.request.user
        qs = Post.objects.filter(status='published')  

        feed = self.request.query_params.get('feed')  
        if feed == 'following' and user.is_authenticated:
            followed_ids = user.following.values_list('id', flat=True)  
            qs = qs.filter(author__in=followed_ids)  

        q = self.request.query_params.get('q')  
        if q:
            qs = qs.filter(caption__icontains=q)  

        author_filter = self.request.query_params.get('author')  
        if author_filter and feed == 'following':
            qs = qs.filter(author__username=author_filter)

        if user.is_authenticated:  
            from accounts.models import Block
            excluded = list(Block.objects.filter(blocker=user).values_list('blocked_id', flat=True))  
            excluded += list(Block.objects.filter(blocked=user).values_list('blocker_id', flat=True))  
            if excluded:
                qs = qs.exclude(author_id__in=excluded)  

        _COLOR_RANGES = {  
            'red':    (345, 15,  True),   
            'orange': (15,  45,  False),
            'yellow': (45,  75,  False),
            'green':  (75,  165, False),
            'cyan':   (165, 210, False),
            'blue':   (210, 255, False),
            'purple': (255, 345, False),
        }
        color_name = self.request.query_params.get('color')  
        if color_name:
            if color_name in _COLOR_RANGES:
                lo, hi, wraps = _COLOR_RANGES[color_name]  
                sat_gt = {'colors__saturation__gt': 0}  
                if wraps:  
                    qs = qs.filter(Q(colors__hue__gte=lo) | Q(colors__hue__lte=hi), **sat_gt).distinct()
                else:  
                    qs = qs.filter(colors__hue__gte=lo, colors__hue__lte=hi, **sat_gt).distinct()
            elif color_name == 'black':  
                qs = qs.filter(colors__saturation=0, colors__lightness__lt=25).distinct()
            elif color_name == 'white':  
                qs = qs.filter(colors__saturation=0, colors__lightness__gt=75).distinct()
            elif color_name == 'gray':  
                qs = qs.filter(colors__saturation=0, colors__lightness__gte=25, colors__lightness__lte=75).distinct()

        qs = annotate_posts(qs, user)  
        sort = self.request.query_params.get('sort', 'new')  
        if sort == 'popular':
            return qs.order_by('-_likes_count', '-created_at')  
        if sort == 'popular_asc':
            return qs.order_by('_likes_count', '-created_at')  
        if sort == 'discussed':
            return qs.order_by('-_comments_count', '-created_at')  
        if sort == 'old':
            return qs.order_by('created_at')  
        return qs.order_by('-created_at')  

    def perform_create(self, serializer):  
        req_status = self.request.data.get('status', 'moderation')  
        final_status = 'draft' if req_status == 'draft' else 'moderation'  
        image_file = self.request.FILES.get('image')  
        video_file = self.request.FILES.get('video')  
        if video_file:
            media_type = 'video'  
        elif image_file and image_file.content_type == 'image/gif':  
            media_type = 'gif'
        else:
            media_type = 'image'  
        post = serializer.save(author=self.request.user, status=final_status, media_type=media_type)  
        tags = extract_tags(post.caption)  
        if tags:
            post.tags.set(tags)  
        for i, img in enumerate(self.request.FILES.getlist('images')):  
            PostImage.objects.create(post=post, image=img, order=i)  
        if final_status == 'moderation':  
            try:
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                async_to_sync(get_channel_layer().group_send)(
                    'notif_moderators',  
                    {'type': 'moderation_new', 'post_id': post.id},  
                )
            except Exception:  
                pass


class PostDetailAPI(generics.RetrieveUpdateDestroyAPIView):  
    queryset = Post.objects.select_related('author', 'repost_of__author').prefetch_related('tags', 'images')  

    def get_serializer_class(self):  
        if self.request.method in ('PUT', 'PATCH'):
            return PostUpdateSerializer  
        return PostSerializer  

    def update(self, request, *args, **kwargs):  
        post = self.get_object()
        if post.author != request.user:  
            return Response({'detail': 'Можно редактировать только свои посты'}, status=status.HTTP_403_FORBIDDEN)
        kwargs['partial'] = True  
        response = super().update(request, *args, **kwargs)  
        tags_data = request.data.get('tags', None)  
        if isinstance(tags_data, list):  
            tag_objects = []
            for name in tags_data:
                name = str(name).lower().strip().lstrip('#')
                from django.utils.text import slugify as _slugify
                slug = _slugify(name, allow_unicode=True)  
                if slug:
                    from .models import Tag as _Tag
                    tag, _ = _Tag.objects.get_or_create(slug=slug, defaults={'name': name})
                    tag_objects.append(tag)
            post.tags.set(tag_objects)  
        else:  
            new_caption = request.data.get('caption', post.caption)
            post.tags.set(extract_tags(new_caption))
        return response

    def destroy(self, request, *args, **kwargs):  
        post = self.get_object()
        if post.author != request.user:  
            return Response({'detail': 'Можно удалять только свои посты'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)  


class LikeToggleAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        if request.user in post.likes.all():  
            post.likes.remove(request.user)
            liked = False
        else:  
            post.likes.add(request.user)
            liked = True
        return Response({'liked': liked, 'likes_count': post.likes.count()})  


class CommentPagination(PageNumberPagination):  
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CommentListCreateAPI(generics.ListCreateAPIView):  
    serializer_class = CommentSerializer
    pagination_class = CommentPagination

    def get_queryset(self):
        return Comment.objects.filter(
            post_id=self.kwargs['pk'],  
            parent__isnull=True  
        ).select_related('author').prefetch_related('replies__author', 'likes')  

    def get_serializer_context(self):  
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def perform_create(self, serializer):  
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        author = post.author
        requester = self.request.user
        privacy = author.comment_privacy  
        if privacy == 'none' and requester != author:  
            raise PermissionDenied('Автор запретил комментарии.')
        if privacy == 'following' and requester != author:  
            if not author.followers.filter(pk=requester.pk).exists():  
                raise PermissionDenied('Только подписчики могут комментировать.')
        serializer.save(author=requester, post_id=self.kwargs['pk'])  


class CommentLikeToggleAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, comment_pk):
        comment = get_object_or_404(Comment, pk=comment_pk, post_id=pk)  
        if request.user in comment.likes.all():
            comment.likes.remove(request.user)
            liked = False
        else:
            comment.likes.add(request.user)
            liked = True
        return Response({'liked': liked, 'likes_count': comment.likes.count()})


class RepostAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk, status='published')  
        if request.user in post.reposted_by.all():  
            post.reposted_by.remove(request.user)
            reposted = False
        else:  
            post.reposted_by.add(request.user)
            reposted = True
        return Response({'reposted': reposted, 'reposts_count': post.reposted_by.count()})


class CollectionListCreateAPI(generics.ListCreateAPIView):  
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.collections.all()  

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)  


class CollectionDetailAPI(generics.RetrieveUpdateDestroyAPIView):  
    queryset = Collection.objects.all()

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CollectionSerializer  
        return CollectionDetailSerializer  

    def get_object(self):
        collection = super().get_object()  
        if not collection.is_public and collection.owner != self.request.user:  
            raise NotFound("Коллекция не найдена")  
        return collection

    def update(self, request, *args, **kwargs):
        collection = self.get_object()
        if collection.owner != request.user:
            raise PermissionDenied("Можно редактировать только свои коллекции")
        kwargs['partial'] = True  
        return super().update(request, *args, **kwargs)

    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied("Можно удалять только свои коллекции")
        instance.delete()


class AddToCollectionAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):  
        collection = get_object_or_404(Collection, pk=pk, owner=request.user)  
        post = get_object_or_404(Post, pk=request.data.get('post'))  
        collection.posts.add(post)  
        return Response({'detail': 'Добавлено'})

    def delete(self, request, pk):  
        collection = get_object_or_404(Collection, pk=pk, owner=request.user)
        post = get_object_or_404(Post, pk=request.data.get('post'))
        collection.posts.remove(post)  
        return Response(status=status.HTTP_204_NO_CONTENT)


class ModerationQueueAPI(generics.ListAPIView):  
    serializer_class = PostMiniSerializer
    permission_classes = [IsModerator]  

    def get_queryset(self):
        from django.utils import timezone
        from datetime import timedelta
        lock_expire = timezone.now() - timedelta(minutes=10)  
        Post.objects.filter(  
            moderation_locked_at__lt=lock_expire  
        ).exclude(moderation_locked_by=None).update(  
            moderation_locked_by=None, moderation_locked_at=None  
        )
        return Post.objects.filter(status='moderation').select_related('author', 'moderation_locked_by').order_by('created_at')  

    def list(self, request, *args, **kwargs):  
        qs = self.get_queryset()
        data = []
        for post in qs:
            s = PostMiniSerializer(post, context={'request': request}).data
            locked = post.moderation_locked_by  
            s['locked_by'] = locked.username if locked else None  
            s['locked_by_me'] = locked == request.user if locked else False  
            data.append(s)
        return Response(data)


class ModerationLockAPI(APIView):  
    permission_classes = [IsModerator]

    def post(self, request, pk):  
        from django.utils import timezone
        from datetime import timedelta
        post = get_object_or_404(Post, pk=pk, status='moderation')
        lock_expire = timezone.now() - timedelta(minutes=10)
        if (post.moderation_locked_by and  
                post.moderation_locked_by != request.user and  
                post.moderation_locked_at and post.moderation_locked_at > lock_expire):  
            return Response(
                {'detail': f'Пост редактирует {post.moderation_locked_by.username}'},
                status=status.HTTP_409_CONFLICT,  
            )
        post.moderation_locked_by = request.user  
        post.moderation_locked_at = timezone.now()  
        post.save(update_fields=['moderation_locked_by', 'moderation_locked_at'])
        return Response({'detail': 'ok'})

    def delete(self, request, pk):  
        post = get_object_or_404(Post, pk=pk)
        if post.moderation_locked_by == request.user:  
            post.moderation_locked_by = None
            post.moderation_locked_at = None
            post.save(update_fields=['moderation_locked_by', 'moderation_locked_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ModerationActionAPI(APIView):  
    permission_classes = [IsModerator]

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk, status='moderation')
        if post.moderation_locked_by and post.moderation_locked_by != request.user:  
            return Response(
                {'detail': f'Пост заблокирован модератором {post.moderation_locked_by.username}'},
                status=status.HTTP_409_CONFLICT,
            )
        action = request.data.get('action')  
        if action == 'approve':  
            post.status = 'published'  
            post.rejection_reason = ''  
        elif action == 'reject':  
            post.status = 'returned'
            post.rejection_reason = request.data.get('reason', '').strip()  
        else:
            return Response({'detail': 'action must be approve or reject'}, status=status.HTTP_400_BAD_REQUEST)
        post.moderation_locked_by = None  
        post.moderation_locked_at = None
        post.save(update_fields=['status', 'moderation_locked_by', 'moderation_locked_at', 'rejection_reason'])
        return Response({'detail': 'ok', 'status': post.status})  


class PostReportAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk, status='published')  
        if post.author == request.user:  
            return Response({'detail': 'Нельзя жаловаться на свой пост'}, status=status.HTTP_400_BAD_REQUEST)
        reason = request.data.get('reason', '').strip()
        if reason not in dict(PostReport.REASON_CHOICES):  
            return Response({'detail': 'Укажите корректную причину'}, status=status.HTTP_400_BAD_REQUEST)
        _, created = PostReport.objects.get_or_create(
            reporter=request.user,
            post=post,
            defaults={'reason': reason, 'comment': request.data.get('comment', '').strip()},
        )
        if not created:  
            return Response({'detail': 'Вы уже отправляли жалобу на этот пост'}, status=status.HTTP_409_CONFLICT)
        return Response({'detail': 'Жалоба отправлена'}, status=status.HTTP_201_CREATED)  


class ModerationReportListAPI(generics.ListAPIView):  
    serializer_class = PostReportSerializer
    permission_classes = [IsModerator]

    def get_queryset(self):
        return PostReport.objects.filter(status='pending').select_related(
            'reporter', 'post', 'post__author'  
        ).order_by('created_at')  


class ModerationReportActionAPI(APIView):  
    permission_classes = [IsModerator]

    def post(self, request, pk):
        report = get_object_or_404(PostReport, pk=pk, status='pending')  
        action = request.data.get('action')  
        if action == 'resolve':  
            report.status = 'resolved'
            report.save(update_fields=['status'])
            if request.data.get('remove_post'):  
                report.post.delete()  
                return Response({'detail': 'Принята, пост удалён'})
        elif action == 'dismiss':  
            report.status = 'dismissed'
            report.save(update_fields=['status'])
        else:
            return Response({'detail': 'action must be resolve or dismiss'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'ok'})


class CommentDetailAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk, comment_pk):  
        comment = get_object_or_404(Comment, pk=comment_pk, post_id=pk)  
        if comment.author != request.user:  
            return Response({'detail': 'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'detail': 'Текст не может быть пустым'}, status=status.HTTP_400_BAD_REQUEST)
        comment.text = text
        comment.save(update_fields=['text'])  
        return Response(CommentSerializer(comment).data)  

    def delete(self, request, pk, comment_pk):  
        comment = get_object_or_404(Comment, pk=comment_pk, post_id=pk)
        if comment.author != request.user and comment.post.author != request.user:  
            return Response({'detail': 'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TrendingTagsAPI(generics.ListAPIView):  
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        cached = cache.get('trending_tags')  
        if cached is not None:
            return cached  
        qs = list(Tag.objects.annotate(  
            pub_count=Count('posts', filter=Q(posts__status='published'), distinct=True)  
        ).filter(pub_count__gt=0).order_by('-pub_count')[:15])  
        cache.set('trending_tags', qs, timeout=3600)  
        return qs


class TagListAPI(generics.ListAPIView):  
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        q = self.request.query_params.get('q', '').strip()
        if not q:
            return Tag.objects.none()
        return Tag.objects.filter(name__icontains=q)[:10]  


class UserPostsAPI(generics.ListAPIView):  
    serializer_class = PostSerializer
    pagination_class = PostPagination

    def get_queryset(self):
        from django.contrib.auth import get_user_model
        from accounts.models import Block
        User = get_user_model()
        profile_user = get_object_or_404(User, username=self.kwargs['username'])
        requester = self.request.user
        if requester.is_authenticated and requester != profile_user:  
            if Block.objects.filter(blocker=profile_user, blocked=requester).exists():
                return Post.objects.none()
            if Block.objects.filter(blocker=requester, blocked=profile_user).exists():
                return Post.objects.none()
        if profile_user.is_private and requester != profile_user:  
            if not requester.is_authenticated or profile_user not in requester.following.all():
                return Post.objects.none()
        qs = profile_user.posts.filter(status='published', repost_of__isnull=True).order_by('-created_at')  
        return annotate_posts(qs, requester)


class UserRepostsAPI(generics.ListAPIView):  
    serializer_class = PostSerializer
    pagination_class = PostPagination

    def get_queryset(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = get_object_or_404(User, username=self.kwargs['username'])
        requester = self.request.user
        if requester.is_authenticated:
            from accounts.models import Block
            if Block.objects.filter(blocker=user, blocked=requester).exists():
                return Post.objects.none()
            if Block.objects.filter(blocker=requester, blocked=user).exists():
                return Post.objects.none()
        qs = user.reposted_posts.filter(status='published').order_by('-created_at')  
        return annotate_posts(qs, requester)


class UserLikedAPI(generics.ListAPIView):  
    serializer_class = PostSerializer
    pagination_class = PostPagination

    def get_queryset(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = get_object_or_404(User, username=self.kwargs['username'])
        requester = self.request.user
        if requester.is_authenticated:
            from accounts.models import Block
            if Block.objects.filter(blocker=user, blocked=requester).exists():
                return Post.objects.none()
            if Block.objects.filter(blocker=requester, blocked=user).exists():
                return Post.objects.none()
        qs = user.liked_posts.filter(status='published').order_by('-created_at')  
        return annotate_posts(qs, requester)


class SimilarPostsAPI(APIView):  
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        tag_ids = list(post.tags.values_list('id', flat=True))  
        if not tag_ids:  
            return Response([])
        qs = Post.objects.filter(
            status='published',
            repost_of__isnull=True,  
            tags__in=tag_ids,  
        ).exclude(pk=post.pk).distinct().order_by('-created_at')  
        qs = annotate_posts(qs, request.user)[:6]  
        return Response(PostSerializer(qs, many=True, context={'request': request}).data)


class UserDraftsAPI(generics.ListAPIView):  
    serializer_class = PostSerializer
    pagination_class = PostPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.username != self.kwargs['username']:  
            return Post.objects.none()
        qs = self.request.user.posts.filter(status='draft').order_by('-created_at')
        return annotate_posts(qs, self.request.user)


class UserReturnedPostsAPI(generics.ListAPIView):  
    serializer_class = PostMiniSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.username != self.kwargs['username']:  
            return Post.objects.none()
        return self.request.user.posts.filter(status='returned').order_by('-created_at')


class TagFeedAPI(generics.ListAPIView):  
    serializer_class = PostSerializer
    pagination_class = PostPagination

    def get_queryset(self):
        tag = get_object_or_404(Tag, slug=self.kwargs['slug'])  
        qs = Post.objects.filter(status='published', tags=tag, repost_of__isnull=True)  
        return annotate_posts(qs, self.request.user).order_by('-created_at')

    def get(self, request, *args, **kwargs):  
        tag = get_object_or_404(Tag, slug=kwargs['slug'])
        response = super().get(request, *args, **kwargs)  
        response.data['tag'] = TagSerializer(tag).data  
        return response


class CommentReportAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, comment_pk):
        comment = get_object_or_404(Comment, pk=comment_pk, post_id=pk)
        if comment.author == request.user:
            return Response({'detail': 'Нельзя жаловаться на свой комментарий'}, status=status.HTTP_400_BAD_REQUEST)
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'detail': 'Укажи причину'}, status=status.HTTP_400_BAD_REQUEST)
        _, created = CommentReport.objects.get_or_create(
            reporter=request.user, comment=comment,
            defaults={'reason': reason, 'detail': request.data.get('detail', '')},
        )
        if not created:
            return Response({'detail': 'Жалоба уже отправлена'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'ok'})


class CommentReportListAPI(generics.ListAPIView):  
    serializer_class = CommentReportSerializer
    permission_classes = [IsModerator]

    def get_queryset(self):
        return CommentReport.objects.filter(status='pending').select_related('reporter', 'comment', 'comment__author', 'comment__post')  


class CommentReportActionAPI(APIView):  
    permission_classes = [IsModerator]

    def post(self, request, pk):
        report = get_object_or_404(CommentReport, pk=pk)
        action = request.data.get('action')  
        if action == 'delete':  
            report.comment.delete()  
            return Response({'detail': 'ok'})
        if action == 'dismiss':  
            report.status = 'dismissed'
            report.save(update_fields=['status'])
            return Response({'detail': 'ok'})
        return Response({'detail': 'invalid action'}, status=status.HTTP_400_BAD_REQUEST)


class QuoteRepostAPI(APIView):  
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        original = get_object_or_404(Post, pk=pk, status='published')  
        caption = request.data.get('caption', '').strip()  
        if not caption:
            return Response({'detail': 'Добавьте текст к репосту'}, status=status.HTTP_400_BAD_REQUEST)
        post = Post.objects.create(  
            author=request.user,
            repost_of=original,  
            caption=caption,  
            status='published',  
            media_type='image',
        )
        tags = extract_tags(caption)  
        if tags:
            post.tags.set(tags)
        return Response(PostSerializer(post, context={'request': request}).data, status=status.HTTP_201_CREATED)
