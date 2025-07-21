from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser

# Роли пользователей
class Role(models.TextChoices):
    ADMIN = 'admin', 'Админ'
    TEACHER = 'teacher', 'Учитель'
    STUDENT = 'student', 'Ученик'

# Кастомный пользователь
class User(AbstractUser):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices)

    REQUIRED_FIELDS = ['full_name', 'email', 'role']

    def __str__(self):
        return f"{self.full_name} ({self.role})"



class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')

    def __str__(self):
        return self.title




class Group(models.Model):
    name = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    students = models.ManyToManyField(User, related_name='student_groups')

    def __str__(self):
        return self.name

