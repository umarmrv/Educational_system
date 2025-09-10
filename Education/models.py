from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils    import timezone
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
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups', null=True, blank=True)
    students = models.ManyToManyField(User, related_name='student_groups')

    def __str__(self):
        return self.name



# Created models for the lessons and Attendance 

class Lesson(models.Model):
    topic = models.CharField(max_length=255)
    date = models.DateField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lessons', limit_choices_to={'role':Role.TEACHER})
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='lessons')

    def __str__(self):
        return f"{self.topic} - {self.group.name} - {self.date}"
    

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, related_name='attendances')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    comment = models.TextField(blank=True, null=True)
    class Meta:
        unique_together = ('student', 'lesson')

    def __str__(self):
        return f"{self.student.full_name} - {self.lesson.topic} - {self.status}"

