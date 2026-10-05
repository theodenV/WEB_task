from rest_framework import permissions  


def _is_moderator(user):  
    return user.is_authenticated and (user.is_staff or user.groups.filter(name='Moderators').exists())  


class IsModerator(permissions.BasePermission):  
    def has_permission(self, request, view):  
        return _is_moderator(request.user)  
