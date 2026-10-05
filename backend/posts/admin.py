from django.contrib import admin  
from .models import Post, Comment  


@admin.register(Post)  
class PostAdmin(admin.ModelAdmin):  
    list_display = ('id', 'author', 'caption', 'status', 'created_at')  
    list_filter = ('status', 'created_at')  
    search_fields = ('caption', 'author__username')  
    actions = ['approve_posts', 'return_posts']  

    @admin.action(description='Одобрить выбранные посты')  
    def approve_posts(self, request, queryset):  
        queryset.update(status='published')  

    @admin.action(description='Вернуть на доработку')  
    def return_posts(self, request, queryset):  
        queryset.update(status='returned')  


admin.site.register(Comment)  
