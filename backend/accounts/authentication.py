from rest_framework.authentication import TokenAuthentication  
from rest_framework.exceptions import AuthenticationFailed  


class BanAwareTokenAuthentication(TokenAuthentication):  
    def authenticate_credentials(self, key):  
        user, token = super().authenticate_credentials(key)  
        if getattr(user, 'is_banned', False):  
            raise AuthenticationFailed({  
                'detail': 'Ваш аккаунт заблокирован.',  
                'ban_reason': user.ban_reason,  
                'code': 'account_banned',  
            })
        return user, token  
