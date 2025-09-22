from django.urls import path
from . import views

urlpatterns = [
    # Аутентификация
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Задачи
    path('tasks/create/', views.create_task_view, name='create_task'),
    path('tasks/<int:pk>/', views.task_detail_view, name='task_detail'),
    path('tasks/<int:pk>/edit/', views.edit_task_view, name='edit_task'),
    path('tasks/<int:pk>/delete/', views.delete_task_view, name='delete_task'),

    # Заявки
    path('requests/', views.request_list_view, name='request_list'),
    path('requests/create/', views.create_request_view, name='create_request'),
    path('requests/<int:pk>/delete/', views.delete_request_view, name='delete_request'),

    # Кабинет руководителя
    path('manager/dashboard/', views.manager_dashboard_view, name='manager_dashboard'),

    # ДОБАВЛЕН ПУТЬ для просмотра руководителем всех задач отдела
    path('department/tasks/', views.department_tasks_view, name='department_tasks'),

    # Главная страница
    path('', views.home_view, name='home'),
]