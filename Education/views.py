from django.shortcuts import render
from Education.models import Group, Course, Lesson, Attendance, Role, User
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.exceptions import PermissionDenied, ValidationError
from .serializers import UserSerializer, CourseSerializer, GroupSerializer, LessonSerializer, AttendanceSerializer

User = get_user_model()

# -----------------------
# Пермишены
# -----------------------
class IsAdminUserRole(BasePermission):
    """Доступ только для админов (role=admin, staff или superuser)."""
    def has_permission(self, request, view):
        u = request.user
        return bool(
            u and (u.is_superuser or u.is_staff or getattr(u, "role", None) == Role.ADMIN)
        )

# -----------------------
# Пользователи
# -----------------------
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all().order_by("id")

    def get_queryset(self):
        user = self.request.user

        if user.role == Role.ADMIN:
            return User.objects.all()

        elif user.role == Role.TEACHER:
            return User.objects.filter(
                role=Role.STUDENT,
                student_groups__course__teacher=user
            ).distinct()

        elif user.role == Role.STUDENT:
            return User.objects.filter(
                student_groups__in=user.student_groups.all()
            ).distinct()

        return User.objects.none()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsAdminUserRole()]
        return [IsAuthenticated()]

    def perform_update(self, serializer):
        u = self.request.user
        if not (u.is_superuser or u.is_staff or getattr(u, "role", None) == Role.ADMIN):
            raise PermissionDenied("Только администратор может изменять пользователей.")
        serializer.save()

    def perform_destroy(self, instance):
        u = self.request.user
        if not (u.is_superuser or u.is_staff or getattr(u, "role", None) == Role.ADMIN):
            raise PermissionDenied("Только администратор может удалять пользователей.")
        instance.delete()

# -----------------------
# Группы
# -----------------------
class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == Role.ADMIN:
            return Group.objects.all()
        elif user.role == Role.TEACHER:
            return Group.objects.filter(course__teacher=user)
        else:  # student
            return Group.objects.filter(students=user)

    def perform_create(self, serializer):
        students = serializer.validated_data.get('students') or []
        invalid_users = [user.username for user in students if user.role in [Role.TEACHER, Role.ADMIN]]
        if invalid_users:
            raise ValidationError(
                f"Эти пользователи не студенты и не могут быть добавлены: {', '.join(invalid_users)}"
            )
        serializer.save()

    def perform_update(self, serializer):
        students = serializer.validated_data.get('students') or []
        invalid_users = [user.username for user in students if user.role in [Role.TEACHER, Role.ADMIN]]
        if invalid_users:
            raise ValidationError(
                f"Эти пользователи не студенты и не могут быть добавлены: {', '.join(invalid_users)}"
            )
        serializer.save()

# -----------------------
# Курсы
# -----------------------
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == Role.ADMIN:
            return Course.objects.all()
        elif user.role == Role.TEACHER:
            return Course.objects.filter(teacher=user)
        elif user.role == Role.STUDENT:
            return Course.objects.filter(groups__students=user).distinct()
        return Course.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != Role.ADMIN:
            raise PermissionDenied("Только администратор может создавать курсы.")
        serializer.save()

    def perform_update(self, serializer):
        if self.request.user.role != Role.ADMIN:
            raise PermissionDenied("Только администратор может изменять курсы.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role != Role.ADMIN:
            raise PermissionDenied("Только администратор может удалять курсы.")
        instance.delete()

# -----------------------
# Уроки
# -----------------------
class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == Role.ADMIN or user.is_superuser or user.is_staff:
            return Lesson.objects.all()
        elif user.role == Role.TEACHER:
            return Lesson.objects.filter(teacher=user)
        elif user.role == Role.STUDENT:
            return Lesson.objects.filter(group__students=user)
        return Lesson.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in [Role.TEACHER, Role.ADMIN]:
            raise PermissionDenied("У вас нет прав для создания урока.")
        if user.role == Role.TEACHER:
            serializer.save(teacher=user)
        else:
            serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if user.role == Role.ADMIN:
            serializer.save()
        elif user.role == Role.TEACHER:
            if serializer.instance.teacher != user:
                raise PermissionDenied("Вы можете редактировать только свои уроки.")
            serializer.save()
        else:
            raise PermissionDenied("У вас нет прав для редактирования урока.")

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role == Role.ADMIN:
            instance.delete()
        elif user.role == Role.TEACHER:
            if instance.teacher != user:
                raise PermissionDenied("Вы можете удалять только свои уроки.")
            instance.delete()
        else:
            raise PermissionDenied("У вас нет прав для удаления урока.")

# -----------------------
# Посещаемость
# -----------------------
class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == Role.ADMIN:
            return Attendance.objects.all()
        elif user.role == Role.TEACHER:
            return Attendance.objects.filter(lesson__teacher=user)
        elif user.role == Role.STUDENT:
            return Attendance.objects.filter(student=user)
        return Attendance.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role not in [Role.ADMIN, Role.TEACHER]:
            raise PermissionDenied("У вас нет прав для добавления посещаемости.")
        serializer.save()

    def perform_update(self, serializer):
        if self.request.user.role == Role.ADMIN:
            serializer.save()
        elif self.request.user.role == Role.TEACHER:
            if serializer.instance.lesson.teacher != self.request.user:
                raise PermissionDenied("Вы можете редактировать только посещаемость своих уроков.")
            serializer.save()
        else:
            raise PermissionDenied("У вас нет прав для редактирования посещаемости.")

    def perform_destroy(self, instance):
        if self.request.user.role == Role.ADMIN:
            instance.delete()
        elif self.request.user.role == Role.TEACHER:
            if instance.lesson.teacher != self.request.user:
                raise PermissionDenied("Вы можете удалять только посещаемость своих уроков.")
            instance.delete()
