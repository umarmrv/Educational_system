from django.contrib import admin
from .models import User, Course, Group
from .forms import GroupAdminForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin



class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('username', 'full_name', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {'fields': ('full_name', 'email', 'phone', 'role')}),
        ('Права доступа', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'full_name', 'email', 'role', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'full_name', 'username')
    ordering = ('id',)




from django.contrib import admin
from .models import Group
from .forms import GroupAdminForm


class GroupAdmin(admin.ModelAdmin):
    form = GroupAdminForm
    filter_horizontal = ("students",)
    list_display = ("name",)

    # Все поля только для чтения
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields] + ["students"]

    # Убрать кнопки сохранения и удаления
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if not request.user.has_perm("Education.change_group"):
            extra_context["show_save"] = False
            extra_context["show_save_and_continue"] = False
            extra_context["show_save_and_add_another"] = False
            extra_context["show_delete"] = False
        return super().change_view(request, object_id, form_url, extra_context)

    # def has_view_permission(self, request, obj=None):
    #     return request.user.has_perm("Education.view_group")

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("Education.change_group")

    def has_add_permission(self, request):
        return request.user.has_perm("Education.add_group")

    def has_delete_permission(self, request, obj=None): 
        return request.user.has_perm("Education.delete_group")


admin.site.register(User, UserAdmin)
admin.site.register(Course)
admin.site.register(Group, GroupAdmin)