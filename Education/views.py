from django.shortcuts import render
from Education.models import Group,Course,Lesson,Attendance,Role
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.exceptions import PermissionDenied

from .serializers import UserSerializer,CourseSerializer,GroupSerializer

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
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Group
from .serializers import GroupSerializer

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Group
from .serializers import GroupSerializer

class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
    
        if user.role == Role.ADMIN:
            return Group.objects.all()
        elif user.role == Role.TEACHER:
            # Ўқитувчига тегишли курслардаги гуруҳларни олиш
            return Group.objects.filter(course__teacher=user)
        else:
            # Талабалар учун ўз гуруҳлари
            return Group.objects.filter(students=user)

    def perform_create(self, serializer):
        students = serializer.validated_data.get('students') or []

        invalid_users = [user.username for user in students if user.role in ['teacher', 'admin']]
        if invalid_users:
            raise ValidationError(
                f"Следующие пользователи не являются студентами и не могут быть добавлены в группу: {', '.join(invalid_users)}"
            )

        serializer.save()

    def perform_update(self, serializer):
        students = serializer.validated_data.get('students') or []

        invalid_users = [user.username for user in students if user.role in ['teacher', 'admin']]
        if invalid_users:
            raise ValidationError(
                f"Следующие пользователи не являются студентами и не могут быть добавлены в группу: {', '.join(invalid_users)}"
            )

        serializer.save()

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]  # ёки AllowAny, агар барчага очиқ бўлса


from rest_framework import viewsets, permissions
from .models import Attendance
from .serializers import AttendanceSerializer

class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Attendance.objects.all()

        if user.is_superuser or user.role == "admin":
            return qs 

        if user.role == "teacher":
            return qs.filter(lesson__teacher=user)

        if user.role == "student":
            return qs.filter(student=user)

        return qs.none()


# views.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Lesson
from .serializers import LessonSerializer

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'teacher':
            return Lesson.objects.filter(teacher=user)

        elif user.role == 'student':
            return Lesson.objects.filter(group__students=user)

        return Lesson.objects.all()

    # def perform_create(self, serializer):
    def perform_create(self, serializer):
        user = self.request.user

        if user.role not in ['teacher', 'admin']:
            raise PermissionDenied("Сизда дарс яратиш ҳуқуқи йўқ!")


        if user.role == 'teacher':
            serializer.save(teacher=user)
        else:
            serializer.save()
