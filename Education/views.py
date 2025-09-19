from django.shortcuts import render

from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.exceptions import PermissionDenied

from .serializers import UserSerializer

User = get_user_model()

class IsAdminUserRole(BasePermission):
    """
    Даёт доступ, если пользователь суперюзер, staff или role=admin.
    """
    def has_permission(self, request, view):
        u = request.user
        return bool(u and (u.is_superuser or u.is_staff or getattr(u, "role", None) == "admin"))

class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD по пользователям.
    - Admin: полный доступ.
    - Обычный пользователь: может смотреть только себя; менять/создавать/удалять — нельзя.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all().order_by("id")

    def get_queryset(self):
        u = self.request.user
        if u.is_superuser or u.is_staff or getattr(u, "role", None) == "admin":
            return super().get_queryset()
        # не admin — только себя
        return User.objects.filter(pk=u.pk)

    def get_permissions(self):
        # На запись (create/update/destroy) пускаем только админов.
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminUserRole()]
        return [IsAuthenticated()]

    # Дополнительно защитим non-admin от изменения И своего профиля тоже (по ТЗ)
    def perform_update(self, serializer):
        u = self.request.user
        if not (u.is_superuser or u.is_staff or getattr(u, "role", None) == "admin"):
            raise PermissionDenied("Только администратор может изменять пользователей.")
        serializer.save()

    def perform_destroy(self, instance):
        u = self.request.user
        if not (u.is_superuser or u.is_staff or getattr(u, "role", None) == "admin"):
            raise PermissionDenied("Только администратор может удалять пользователей.")
        instance.delete()
