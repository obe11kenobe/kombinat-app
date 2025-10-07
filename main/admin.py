from django.contrib import admin
from .models import User, Department, Task, Request
from django.contrib.auth.admin import UserAdmin

# Регистрируем модель Department
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',) # Поля, которые будут отображаться в списке
    search_fields = ('name',) # Поиск по названию

# Расширяем стандартный UserAdmin для нашей кастомной модели User
class CustomUserAdmin(UserAdmin):
    # Добавляем поле 'department' в отображение и редактирование
    list_display = ('username', 'first_name', 'last_name', 'department', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('department', 'patronymic')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('department', 'patronymic')}),
    )

# Регистрируем модель Task
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'author', 'assignee', 'deadline')
    list_filter = ('status', 'priority', 'deadline') # Фильтры сбоку
    search_fields = ('title', 'description')

# Регистрируем модель Request
@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'request_type', 'status', 'requester', 'created_at')
    list_filter = ('request_type', 'status')
    search_fields = ('title', 'justification')

# Регистрируем нашу кастомную модель User с расширенными настройками
admin.site.register(User, CustomUserAdmin)