from django.contrib import admin  
from django.contrib.auth.admin import UserAdmin  
from .models import User  


class CustomUserAdmin(UserAdmin):  
    list_display = ('username', 'email', 'phone', 'is_staff')  
    fieldsets = UserAdmin.fieldsets + (  
        ('Доп. информация', {'fields': ('phone', 'avatar', 'bio')}),  
    )


admin.site.register(User, CustomUserAdmin)  
