from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Course, Group, Lesson, Attendance
from .forms import GroupAdminForm, LessonAdminForm, CourseAdminForm


# =========================
# USER ADMIN
# =========================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("id", "username", "full_name", "email", "phone", "role", "is_staff", "is_active", "date_joined")
    list_filter = ("role", "is_staff", "is_active", "date_joined")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Личная информация", {"fields": ("full_name", "email", "phone", "role")}),
        ("Права доступа", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "full_name", "email", "phone", "role", "password1", "password2", "is_staff", "is_active")
        }),
    )
    search_fields = ("id", "email", "full_name", "username", "phone")
    ordering = ("id",)


# ==========================================
# VALIDATION: student must belong to lesson's group
# ==========================================
class AttendanceAdminForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        lesson = cleaned.get("lesson")
        student = cleaned.get("student")

        if lesson and student:
            if not hasattr(lesson.group, "students") or not lesson.group.students.filter(pk=student.pk).exists():
                raise ValidationError("Этот ученик не состоит в группе, к которой относится урок.")

        return cleaned


# =================
# GROUP ADMIN
# =================
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    form = GroupAdminForm
    filter_horizontal = ("students",)
    list_display = ("id", "display_name", "students_count")
    search_fields = ("id", "title", "name", "description")
    readonly_fields = ['show_lessons']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser:
            return qs
        return qs.filter(course__teacher=user)

    def display_name(self, obj):
        return getattr(obj, "title", None) or getattr(obj, "name", None) or str(obj)
    display_name.short_description = "Группа"

    def students_count(self, obj):
        try:
            return obj.students.count() if hasattr(obj, "students") else "-"
        except Exception:
            return "-"
    students_count.short_description = "Студентов"

    def show_lessons(self, obj):
        lessons = obj.lessons.order_by('date')
        if not lessons.exists():
            return "Нет уроков"

        output = ""
        for lesson in lessons:
            attendances = lesson.attendances.select_related('student')

            present_students = [
                a.student.full_name for a in attendances if a.status == 'present'
            ]
            absent_students = [
                a.student.full_name for a in attendances if a.status == 'absent'
            ]

            output += f"📅 Дата: {lesson.date.strftime('%d.%m.%Y')}\n"
            output += f"📘 Тема: {lesson.topic}\n"
            output += f"✅ Присутствовали: {', '.join(present_students) if present_students else '—'}\n"
            output += f"❌ Отсутствовали: {', '.join(absent_students) if absent_students else '—'}\n"
            output += "-" * 40 + "\n"

        return output
    show_lessons.short_description = "Уроки и посещаемость"


# =================
# COURSE ADMIN
# =================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm
    list_display = ("id", "display_title", "get_teacher_name")  # добавили get_teacher_name
    search_fields = ("id", "title", "name", "description", "teacher__full_name")  # добавлен поиск по teacher

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(teacher=request.user)

    def display_title(self, obj):
        return getattr(obj, "title", None) or getattr(obj, "name", None) or str(obj)
    display_title.short_description = "Курс"

    def get_teacher_name(self, obj):
        return obj.teacher.full_name if hasattr(obj, 'teacher') and obj.teacher else "-"
    get_teacher_name.short_description = 'Учитель'


# ============================
# ATTENDANCE INLINE for LESSON
# ============================
class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    form = AttendanceAdminForm
    autocomplete_fields = ("student",)

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_obj = obj
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student" and getattr(self, "parent_obj", None):
            if hasattr(self.parent_obj.group, "students"):
                kwargs["queryset"] = self.parent_obj.group.students.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ===============
# LESSON ADMIN
# ===============

@admin.action(description="Create attendance for all")
def create_for_all(modeladmin, request, queryset):
    sum = 0
    for lesson in queryset:
        students = lesson.group.students.all()
        for student in students:
            obj, created = Attendance.objects.get_or_create(
                student=student,
                lesson=lesson,
                defaults={'status':'present'}
            )
            if created:
                sum += 1
                modeladmin.message_user(request, f"Создано {sum} записей Attendance")

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('topic', 'date', 'teacher', 'group')
    search_fields = ['topic']
    actions = [create_for_all]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == 'teacher':
            return qs.filter(teacher=request.user)
        return qs

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request

        if request.user.role == 'teacher' and 'teacher' in form.base_fields:
            form.base_fields['teacher'].widget = forms.HiddenInput()
            form.base_fields['teacher'].initial = request.user

        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "group" and request.user.role == 'teacher':
            kwargs["queryset"] = Group.objects.filter(course__teacher=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if request.user.role == 'teacher' and not obj.teacher_id:
            obj.teacher = request.user
        super().save_model(request, obj, form, change)


# ==================
# ATTENDANCE ADMIN
# ==================
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    form = AttendanceAdminForm
    list_editable = ('status',)
    list_display = ("student", "lesson", "lesson_date", "lesson_group", "status")
    list_filter = ("status", "lesson__date", "lesson__group")
    search_fields = ("student__full_name", "student__username", "student__email", "lesson__topic")
    autocomplete_fields = ("student", "lesson")

    def lesson_date(self, obj):
        return obj.lesson.date
    lesson_date.admin_order_field = "lesson__date"
    lesson_date.short_description = "Дата урока"

    def lesson_group(self, obj):
        return obj.lesson.group
    lesson_group.admin_order_field = "lesson__group"
    lesson_group.short_description = "Группа"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(lesson__teacher=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "lesson" and not request.user.is_superuser:
            kwargs["queryset"] = Lesson.objects.filter(teacher=request.user)

        if db_field.name == "student":
            lesson_id = request.GET.get("lesson")
            if lesson_id:
                try:
                    lesson = Lesson.objects.select_related("group").get(pk=lesson_id)
                    if hasattr(lesson.group, "students"):
                        kwargs["queryset"] = lesson.group.students.all()
                    else:
                        kwargs["queryset"] = User.objects.filter(role="student")
                except Lesson.DoesNotExist:
                    kwargs["queryset"] = User.objects.filter(role="student")
            else:
                kwargs["queryset"] = User.objects.filter(role="student")

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
