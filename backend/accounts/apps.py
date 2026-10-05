from django.apps import AppConfig  


class AccountsConfig(AppConfig):  
    default_auto_field = 'django.db.models.BigAutoField'  
    name = 'accounts'  

    def ready(self):  
        from . import signals as _s  
        _s.connect_signals()  
