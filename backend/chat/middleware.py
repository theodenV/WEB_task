from urllib.parse import parse_qs  
from channels.db import database_sync_to_async  
from channels.middleware import BaseMiddleware  
from django.contrib.auth.models import AnonymousUser  


@database_sync_to_async  
def get_user_from_token(token_key):  
    from rest_framework.authtoken.models import Token  
    try:
        return Token.objects.select_related('user').get(key=token_key).user  
    except Token.DoesNotExist:  
        return AnonymousUser()  


@database_sync_to_async  
def get_user_from_ticket(ticket):  
    from django.core.cache import cache  
    from django.contrib.auth import get_user_model
    user_id = cache.get(f'ws_ticket:{ticket}')  
    if not user_id:  
        return AnonymousUser()
    cache.delete(f'ws_ticket:{ticket}')  
    try:
        return get_user_model().objects.get(pk=user_id)  
    except Exception:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):  
    async def __call__(self, scope, receive, send):  
        query = parse_qs(scope['query_string'].decode())  
        ticket = query.get('ws_ticket', [None])[0]  
        token_key = query.get('token', [None])[0]  
        if ticket:  
            scope['user'] = await get_user_from_ticket(ticket)  
        elif token_key:  
            scope['user'] = await get_user_from_token(token_key)
        return await super().__call__(scope, receive, send)  
