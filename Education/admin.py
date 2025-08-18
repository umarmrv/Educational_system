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
# ВАЛИДАЦИЯ: студент должен быть в группе урока
# (локально, без отдельного файла)
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
            # Вариант с M2M: Group.students -> User (рекомендуется)
            if not hasattr(lesson.group, "students") or not lesson.group.students.filter(pk=student.pk).exists():
                raise ValidationError("Этот ученик не состоит в группе, к которой относится урок.")

            # Если у User вместо M2M есть FK group -> Group, используй такую проверку:
            # if getattr(student, "group_id", None) != lesson.group_id:
            #     raise ValidationError("Этот ученик не состоит в группе, к которой относится урок.")

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
    list_display = ("id", "display_title")
    search_fields = ("id", "title", "name", "description")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(teacher=request.user)

    def display_title(self, obj):
        return getattr(obj, "title", None) or getattr(obj, "name", None) or str(obj)
    display_title.short_description = "Курс"



# ============================
# ATTENDANCE INLINE под LESSON
# ============================
class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    form = AttendanceAdminForm
    autocomplete_fields = ("student",)

    def get_formset(self, request, obj=None, **kwargs):
        # parent_obj — текущий Lesson (нужен для фильтра студентов)
        self.parent_obj = obj
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Ограничим список студентов только учениками группы текущего урока
        if db_field.name == "student" and getattr(self, "parent_obj", None):
            if hasattr(self.parent_obj.group, "students"):
                kwargs["queryset"] = self.parent_obj.group.students.all()
            # Если у User FK group -> Group, можно так:
            # else:
            #     kwargs["queryset"] = User.objects.filter(group=self.parent_obj.group, role="student")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ===============
# LESSON ADMIN
# ===============
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('topic', 'date', 'teacher', 'group')
    search_fields = ['topic']  # 🔧 Мана шуни қўшиш керак!

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Передаём request в форму для валидации
        form.request = request

        # Скрываем поле teacher для учителя
        if request.user.role == 'teacher' and 'teacher' in form.base_fields:
            form.base_fields['teacher'].widget = forms.HiddenInput()
            form.base_fields['teacher'].initial = request.user

        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Ограничиваем группы учителя
        if db_field.name == "group" and request.user.role == 'teacher':
            kwargs["queryset"] = Group.objects.filter(course__teacher=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Авто-наставление teacher для учителя
        if request.user.role == 'teacher' and not obj.teacher_id:
            obj.teacher = request.user
        super().save_model(request, obj, form, change)

# ==================
# ATTENDANCE ADMIN
# ==================
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    form = AttendanceAdminForm
    list_display = ("student", "lesson", "lesson_date", "lesson_group", "status")
    list_filter = ("status", "lesson__date", "lesson__group")
    search_fields = ("student__full_name", "student__username", "student__email", "lesson__topic")
    autocomplete_fields = ("student", "lesson")

    # Удобные колонки
    def lesson_date(self, obj):
        return obj.lesson.date
    lesson_date.admin_order_field = "lesson__date"
    lesson_date.short_description = "Дата урока"

    def lesson_group(self, obj):
        return obj.lesson.group
    lesson_group.admin_order_field = "lesson__group"
    lesson_group.short_description = "Группа"

    # Учитель видит только посещаемость по своим урокам
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Если Lesson.teacher — FK на User:
        return qs.filter(lesson__teacher=request.user)
        # Если Lesson.teacher -> Teacher -> user:
        # return qs.filter(lesson__teacher__user=request.user)

    # Ограничим выбор уроков и студентов в формах
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Уроки — только уроки текущего учителя (если не суперюзер)
        if db_field.name == "lesson" and not request.user.is_superuser:
            kwargs["queryset"] = Lesson.objects.filter(teacher=request.user)
            # Если Lesson.teacher -> Teacher -> user:
            # kwargs["queryset"] = Lesson.objects.filter(teacher__user=request.user)

        # Студенты — из группы выбранного урока; если урок не передан — все с role="student"
        if db_field.name == "student":
            lesson_id = request.GET.get("lesson")
            if lesson_id:
                try:
                    lesson = Lesson.objects.select_related("group").get(pk=lesson_id)
                    if hasattr(lesson.group, "students"):
                        kwargs["queryset"] = lesson.group.students.all()
                    else:
                        # Если у User FK group -> Group:
                        # kwargs["queryset"] = User.objects.filter(group=lesson.group, role="student")
                        kwargs["queryset"] = User.objects.filter(role="student")
                except Lesson.DoesNotExist:
                    kwargs["queryset"] = User.objects.filter(role="student")
            else:
                kwargs["queryset"] = User.objects.filter(role="student")

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
