from django import forms
from .models import Group, User, Role

class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем список студентов только пользователями с role='student'
        self.fields['students'].queryset = User.objects.filter(role=Role.STUDENT)
