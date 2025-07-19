from django.db import models
from django.contrib.auth.models import User

class Admin(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_profile")

  def __str__(self):
    return f"Admin: {self.user.username}"

class Teacher(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
  name = models.CharField(max_length=50)
  surname = models.CharField(max_length=50)
  email = models.EmailField(unique=True)

  def __str__(self):
    return f"{self.surname} {self.name} (Teacher)"

class Course(models.Model):
  title = models.CharField(max_length=100)
  description = models.TextField()
  teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name="courses")

  def __str__(self):
    return f"{self.title} (Course)"

class Group(models.Model):
  title = models.CharField(max_length=100)
  description = models.TextField()
  course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="groups")

  def __str__(self):
    return f"{self.title} (Group)"

class Student(models.Model):
  user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
  name = models.CharField(max_length=50)
  surname = models.CharField(max_length=50)
  email = models.EmailField(unique=True)
  group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, related_name="students")

  def __str__(self):
    return f"{self.name} {self.surname} (Student)"

class Lesson(models.Model):
  topic = models.CharField("Lesson topic", max_length=200)
  start_datetime = models.DateTimeField("Date and time for lesson")
  group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="lessons")
  teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name="lessons")

  def __str__(self):
    return f"{self.topic} (Lesson)"

class Attendance(models.Model):
  student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendances")
  lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="attendances")
  status = models.BooleanField(default=False)

  def __str__(self):
    status_str = "Present" if self.status else "Absent"
    return f"{self.student} - {self.lesson}: {status_str}"
