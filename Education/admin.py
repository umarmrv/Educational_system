from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import transaction
from django.db.models import Q
from django.utils.html import format_html

from .models import User, Course, Group, Lesson, Attendance, Payment
from .forms import GroupAdminForm, LessonAdminForm, CourseAdminForm


# =========================
# USER ADMIN
# =========================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("username", "full_name", "email", "phone", "role", "is_staff", "is_active", "date_joined")
    list_filter = ("role", "is_staff", "is_active", "date_joined")

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.role == "student":
            groups = Group.objects.filter(students=request.user)
            student_ids = User.objects.filter(student_groups__in=groups).values_list("id", flat=True)
            teacher_ids = User.objects.filter(courses__groups__in=groups).values_list("id", flat=True)

            return qs.filter(
                Q(id=request.user.id) | Q(id__in=student_ids) | Q(id__in=teacher_ids)
            ).distinct()

        return qs

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
    list_display = ("display_name", "students_count")
    search_fields = ("name", "course__title")  # <-- ислоҳ шуд
    readonly_fields = ['show_lessons']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == "teacher":
            return qs.filter(course__teacher=request.user)
        if request.user.role == "student":
            return qs.filter(students=request.user)
        return qs

    def display_name(self, obj):
        return getattr(obj, "name", None) or str(obj)
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
            present_students = [a.student.full_name for a in attendances if a.status == 'present']
            absent_students = [a.student.full_name for a in attendances if a.status == 'absent']

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
    list_display = ("display_title", "get_teacher_name")
    search_fields = ("title", "name", "description", "teacher__full_name")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == "teacher":
            return qs.filter(teacher=request.user)
        return qs

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


# =========================
# INTERNAL HELPER
# =========================
def _ensure_attendance_for_lesson(lesson, *, default_status="present") -> int:
    """
    Создаёт Attendance для всех студентов lesson.group, если отсутствуют.
    Возвращает количество созданных записей.
    """
    if not getattr(lesson, "group_id", None) or not hasattr(lesson.group, "students"):
        return 0

    student_ids = list(
        lesson.group.students.only("id").values_list("id", flat=True)
    )
    if not student_ids:
        return 0

    existing_ids = set(
        Attendance.objects.filter(lesson=lesson).values_list("student_id", flat=True)
    )

    to_create = [
        Attendance(student_id=sid, lesson=lesson, status=default_status)
        for sid in student_ids
        if sid not in existing_ids
    ]
    if to_create:
        Attendance.objects.bulk_create(to_create)
    return len(to_create)


# ===============
# LESSON ADMIN
# ===============
@admin.action(description="Create attendance for all")
def create_for_all(modeladmin, request, queryset):
    created_total = 0
    for lesson in queryset.select_related("group"):
        created_total += _ensure_attendance_for_lesson(lesson)
    modeladmin.message_user(request, f"Создано записей Attendance: {created_total}")

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    form = LessonAdminForm
    list_display = ('topic', 'date', 'teacher', 'group')
    search_fields = ['topic']
    actions = [create_for_all]
    # (по желанию) показать инлайн:
    # inlines = [AttendanceInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.role == "teacher":
            return qs.filter(teacher=request.user)
        
        if request.user.role == "student":
            return qs.filter(group__students=request.user)

        return qs

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request

        if getattr(request.user, "role", None) == 'teacher' and 'teacher' in form.base_fields:
            form.base_fields['teacher'].widget = forms.HiddenInput()
            form.base_fields['teacher'].initial = request.user

        return form

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "group" and getattr(request.user, "role", None) == 'teacher':
            kwargs["queryset"] = Group.objects.filter(course__teacher=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        # выставляем teacher для роли teacher
        if getattr(request.user, "role", None) == 'teacher' and not obj.teacher_id:
            obj.teacher = request.user

        # сначала сохраняем урок, чтобы получить PK
        super().save_model(request, obj, form, change)

        # автосоздание посещаемости:
        # - при создании урока
        # - при смене группы у существующего урока
        group_changed = bool(change and hasattr(form, "changed_data") and "group" in form.changed_data)
        if not change or group_changed:
            created = _ensure_attendance_for_lesson(obj)
            if created:
                self.message_user(request, f"Посещаемость создана для студентов группы: {created} записей.")


# ==================
# ATTENDANCE ADMIN
# =================
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    form = AttendanceAdminForm
    list_editable = ('status',)
    list_display = (
        "student",
        "lesson",
        "lesson_date",
        "lesson_group",
        "status",
        "comment",
    )
    search_fields = (
        "student__full_name",
        "student__username",
        "student__email",
        "lesson__topic",
    )
    autocomplete_fields = ("student", "lesson")

    list_filter = (
        "status",
        ("lesson__date", admin.DateFieldListFilter),
    )


    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser or request.user.role == "admin":
            return qs 

        if request.user.role == "teacher":
            return qs.filter(lesson__teacher=request.user)

        if request.user.role == "student":
            return qs.filter(student=request.user)

        return qs.none()


    def lesson_date(self, obj):
        return obj.lesson.date
    lesson_date.admin_order_field = "lesson__date"
    lesson_date.short_description = "Дата урока"

    def lesson_group(self, obj):
        return obj.lesson.group
    lesson_group.admin_order_field = "lesson__group"
    lesson_group.short_description = "Группа"


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "lesson" and not request.user.is_superuser:
            if request.user.role == "teacher":
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
    
from django.contrib import admin
from django.utils.html import format_html
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('colored_student', 'group', 'course', 'cycle_index', 'amount_due', 'created_at', 'is_paid')
    list_editable = ('is_paid',)
    list_filter = ('group', 'course', 'is_paid')
    search_fields = ('student__full_name', 'group__name', 'course__title')
    search_help_text = "Поиск по имени студента, названию группы или курса"
    list_per_page = 20
    ordering = ('group__name', 'student__full_name')

    # 🔒 Показывать студенту только его собственные платежи
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.role == 'student':  # если пользователь — студент
            return queryset.filter(student=request.user)
        return queryset  # админ и учителя видят всё

    # 🚫 Запрещаем студентам изменять записи
    def has_change_permission(self, request, obj=None):
        if request.user.role == 'student':
            return False
        return super().has_change_permission(request, obj)

    # 🚫 Запрещаем студентам добавлять новые платежи
    def has_add_permission(self, request):
        if request.user.role == 'student':
            return False
        return super().has_add_permission(request)

    # 🟢 Цветное отображение имени студента
    def colored_student(self, obj):
        if obj.is_paid:
            return format_html(
                '<div style="background-color:#d4edda; padding:5px; border-radius:5px;">{}</div>',
                obj.student.full_name
            )
        return format_html(
            '<div style="background-color:#ffbabb; padding:5px; border-radius:5px;">{}</div>',
            obj.student.full_name
        )

    colored_student.short_description = 'Студент'

    class Media:
        css = {'all': ('admin/css/payment_admin.css',)}
