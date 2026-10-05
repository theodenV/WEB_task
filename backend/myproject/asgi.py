import os  
from django.core.asgi import get_asgi_application  

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')  
django_asgi_app = get_asgi_application()  

from channels.routing import ProtocolTypeRouter, URLRouter  
from channels.auth import AuthMiddlewareStack  
from chat.middleware import TokenAuthMiddleware  
import chat.routing  
import accounts.routing  

application = ProtocolTypeRouter({  
    'http': django_asgi_app,  
    'websocket': AuthMiddlewareStack(  
        TokenAuthMiddleware(  
            URLRouter(  
                chat.routing.websocket_urlpatterns +  
                accounts.routing.websocket_urlpatterns  
            )
        )
    ),
})
