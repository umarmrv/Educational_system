from django import forms
from .models import Group, User, Role, Lesson

class GroupAdminForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем список студентов только пользователями с role='student'
        if 'students' in self.fields:
            self.fields['students'].queryset = User.objects.filter(role=Role.STUDENT)

class LessonAdminForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'teacher' in self.fields:
            self.fields['teacher'].queryset = User.objects.filter(role=Role.TEACHER)


class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'teacher' in self.fields:
            self.fields['teacher'].queryset = User.objects.filter(role=Role.TEACHER)
