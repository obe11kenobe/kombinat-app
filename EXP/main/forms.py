from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from .models import User, Department, Request, Task, Comment, Attachment

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'patronymic', 'department')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].required = True
        self.fields['department'].queryset = Department.objects.all()

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        # Добавляем поле 'department'
        fields = ['title', 'justification', 'request_type', 'department']

class TaskCreationForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assignee', 'deadline', 'priority']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Показываем только сотрудников из отдела текущего пользователя (включая руководителя)
            self.fields['assignee'].queryset = User.objects.filter(department=user.department)
        
        # Добавляем Bootstrap классы ко всем полям
        for field_name, field in self.fields.items():
            if field_name not in ['assignee', 'deadline']:  # Эти уже настроены в widgets
                field.widget.attrs.update({'class': 'form-control'})

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class TaskUpdateForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['assignee', 'deadline']
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'assignee': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Ограничиваем список исполнителей сотрудниками текущего отдела
            self.fields['assignee'].queryset = User.objects.filter(department=user.department)

class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['file']