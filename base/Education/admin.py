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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_authenticated and user.role == 'student':
            return qs.filter(students=user)
        return qs

class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('username', 'full_name', 'email', 'phone', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {'fields': ('full_name', 'email', 'phone', 'role')}),
        ('Права доступа', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'full_name', 'email', 'phone', 'role', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'full_name', 'username', 'phone')
    ordering = ('id',)


admin.site.register(User, UserAdmin)
admin.site.register(Course)
admin.site.register(Group, GroupAdmin)

admin.site.site_header ='Learning-center'
admin.site.site_title ='www.global.com'
admin.site.index_title ='Welcome to the Learning-center official site'