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


class GroupAdmin(admin.ModelAdmin):
    form = GroupAdminForm
    filter_horizontal = ("students",)


admin.site.register(User, UserAdmin)
admin.site.register(Course)
admin.site.register(Group, GroupAdmin)