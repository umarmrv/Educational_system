from rest_framework.permissions import BasePermission
from .models import Role

class GroupPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.role == Role.TEACHER:
            return view.action in ['list', 'retrieve']
        return True