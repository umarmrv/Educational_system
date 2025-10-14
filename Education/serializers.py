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
from Education.models import Group, Course
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

from rest_framework import serializers
from Education.models import Course, User

class CourseSerializer(serializers.ModelSerializer):
    # Поле для приема teacher как ID (по умолчанию)
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='teacher'),  # Только пользователи с ролью teacher
        required=False,
        write_only=True  # При отправке данных, но не в ответе
    )
    # Поле для отображения имени учителя в ответе
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)

    class Meta:
        model = Course
        fields = ['title', 'description', 'teacher', 'teacher_name']

    def to_internal_value(self, data):
        # Если в поле teacher передано имя (строка), а не ID, пытаемся найти учителя по имени
        if isinstance(data.get('teacher'), str):
            try:
                user = User.objects.get(username=data['teacher'], role='teacher')
                data['teacher'] = user.id  # Заменяем имя на ID
            except User.DoesNotExist:
                raise serializers.ValidationError({'teacher': 'Учитель с таким именем не найден'})
        return super().to_internal_value(data)

from rest_framework import serializers
from .models import Attendance

class AttendanceSerializer(serializers.ModelSerializer):
    student = serializers.CharField(source='student.full_name', read_only=True)
    lesson = serializers.CharField(source='lesson.topic', read_only=True) 
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
        # Создаём Lesson
        lesson = super().create(validated_data)

        # Получаем всех студентов из группы
        group = lesson.group
        students = group.students.filter(role='student')  # фильтрация по роли

        # Создаём attendance со статусом 'present'
        attendances = [
            Attendance(student=student, lesson=lesson, status='present')
            for student in students
        ]

        Attendance.objects.bulk_create(attendances)

        return lesson
