from django.contrib.auth import get_user_model
from rest_framework import serializers

from Education.models import Role  # enum ролей

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Один сериализатор и на чтение, и на запись.
    - Если передан password — хэшируем и сохраняем.
    - Если password не передан при создании — сгенерируем случайный.
    """
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = (
            "id", "username", "password", "full_name", "email", "phone",
            "role", "is_active", "date_joined",
        )
        read_only_fields = ("id", "date_joined")

    def create(self, validated_data):
        pwd = validated_data.pop("password", None)
        user = User(**validated_data)
        if pwd:
            user.set_password(pwd)
        else:
            user.set_password(User.objects.make_random_password())
        user.save()
        return user

    def update(self, instance, validated_data):
        pwd = validated_data.pop("password", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if pwd:
            instance.set_password(pwd)
        instance.save()
        return instance
from rest_framework import serializers
from Education.models import Group, Course# Course ва Group моделларини импорт қилинг
from django.contrib.auth import get_user_model

User = get_user_model()

class GroupSerializer(serializers.ModelSerializer):
  
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), required=False, allow_null=True)
    students = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)

    class Meta:
        model = Group
        fields = ['id', 'name', 'course', 'students']




from rest_framework import serializers
from Education.models import Course  # ёки қаерда бўлса
from django.contrib.auth import get_user_model

User = get_user_model()

class CourseSerializer(serializers.ModelSerializer):
    teacher = serializers.SlugRelatedField(
        slug_field='full_name',
        queryset=User.objects.all()
    )

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'teacher']

from rest_framework import serializers
from .models import Attendance

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = [
            'id',
            'student',
            'lesson',
            'status',
            'comment',
        ]


# serializers.py
from rest_framework import serializers
from .models import Lesson, Attendance, Group, User

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

    def create(self, validated_data):
        lesson = super().create(validated_data)

        # Автоматик attendance яратиш
        students = lesson.group.students.all()
        created_attendances = [
            Attendance(student=student, lesson=lesson, status='absent')
            for student in students
        ]
        Attendance.objects.bulk_create(created_attendances)

        return lesson
