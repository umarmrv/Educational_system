from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Course, User, Group, Lesson, Attendance
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
# Форма для Attendance с валидацией
# ==========================================
class AttendanceAdminForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = '__all__'  # ✅ правильно: строка, а не кортеж

    def clean(self):
        cleaned = super().clean()
        lesson = cleaned.get("lesson")
        student = cleaned.get("student")

        if lesson and student:
            if not hasattr(lesson.group, "students") or not lesson.group.students.filter(pk=student.pk).exists():
                raise ValidationError("Этот ученик не состоит в группе, к которой относится урок.")

        return cleaned


# ===========================
# INLINE для посещаемости
# ===========================
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
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    form = LessonAdminForm
    list_display = ("topic", "date", "teacher", "group")
    list_filter = ("date", "teacher", "group")
    search_fields = ("topic", "teacher__full_name", "teacher__username", "group__name", "group__title")
    autocomplete_fields = ("teacher", "group")
    inlines = [AttendanceInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(teacher=request.user)


# =================
# GROUP ADMIN
# =================
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    form = GroupAdminForm
    filter_horizontal = ("students",)

    list_display = ("id", "display_name", "students_count")
    search_fields = ("id", "title", "name", "description")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_authenticated and getattr(user, "role", None) == "student" and hasattr(self.model, "students"):
            return qs.filter(students=user)
        return qs

    def display_name(self, obj):
        return getattr(obj, "title", None) or getattr(obj, "name", None) or str(obj)
    display_name.short_description = "Группа"

    def students_count(self, obj):
        if hasattr(obj, "students"):
            try:
                return obj.students.count()
            except Exception:
                return "-"
        return "-"
    students_count.short_description = "Студентов"


# =================
# COURSE ADMIN
# =================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm
    list_display = ("id", "display_title", "get_teacher_name")
    search_fields = ("id", "title", "name", "description", "teacher__full_name")

    def display_title(self, obj):
        return getattr(obj, "title", None) or getattr(obj, "name", None) or str(obj)
    display_title.short_description = "Курс"

    def get_teacher_name(self, obj):
        return obj.teacher.full_name if hasattr(obj, 'teacher') and obj.teacher else "-"
    get_teacher_name.short_description = 'Учитель'


# ==================
# ATTENDANCE ADMIN
# ==================
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    form = AttendanceAdminForm
    list_display = ("student", "lesson", "lesson_date", "lesson_group", "status")
    list_filter = ("status", "lesson__date", "lesson__group")  # ✅ Исправлено
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
