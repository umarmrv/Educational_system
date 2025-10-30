from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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


class Payment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role':Role.STUDENT}, related_name='payments')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    cycle_index = models.PositiveIntegerField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'group', 'cycle_index')
        ordering = ['group', 'student', 'cycle_index']

    def __str__(self):
        status = "✅" if self.is_paid else "❌"
        return f"{self.student.full_name} - {self.group.name} (Цикл {self.cycle_index}) {status}"


@receiver(post_save, sender=Group)
def create_payments_for_new_group(sender, instance, created, **kwargs):
    if created and instance.course and instance.students.exists():
        course = instance.course
        students = instance.students.all()
        for student in students:
            Payment.objects.create(
                student=student,
                group=instance,
                course=course,
                cycle_index=1,
                amount_due=course.price,
                is_paid=False
            )


@receiver(m2m_changed, sender=Group.students.through)
def create_payment_for_new_student(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        from decimal import Decimal
        course = instance.course
        if not course:
            return

        total_lessons = instance.lessons.count()
        current_cycle_index = total_lessons // 12 + 1
        lessons_in_current_cycle = total_lessons % 12

        for student_id in pk_set:
            student = User.objects.get(pk=student_id)

            if Payment.objects.filter(student=student, group=instance, cycle_index=current_cycle_index).exists():
                continue

            if lessons_in_current_cycle == 0:
                amount_due = course.price
            else:
                remaining_lessons = 12 - lessons_in_current_cycle
                amount_due = (Decimal(remaining_lessons) / Decimal(12)) * course.price

            Payment.objects.create(
                student=student,
                group=instance,
                course=course,
                cycle_index=current_cycle_index,
                amount_due=round(amount_due, 2),
                is_paid=False
            )


@receiver(post_save, sender=Lesson)
def create_payments_after_cycle_complete(sender, instance, created, **kwargs):
    if not created:
        return

    group = instance.group
    course = group.course
    if not course:
        return

    total_lessons = group.lessons.count()

    if total_lessons % 12 == 0:
        current_cycle_index = total_lessons // 12 + 1 
        students = group.students.all()

        for student in students:
            if Payment.objects.filter(student=student, group=group, cycle_index=current_cycle_index).exists():
                continue

            Payment.objects.create(
                student=student,
                group=group,
                course=course,
                cycle_index=current_cycle_index,
                amount_due=course.price,
                is_paid=False
            )

