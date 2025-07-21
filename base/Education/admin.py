from django.contrib import admin
from .models import User, Course, Group
from .forms import GroupAdminForm




class GroupAdmin(admin.ModelAdmin):
    form = GroupAdminForm

admin.site.register(User)
admin.site.register(Course)
admin.site.register(Group, GroupAdmin)




