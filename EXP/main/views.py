from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, TaskCreationForm,
    RequestForm, TaskUpdateForm, CommentForm, AttachmentForm
)
from .models import Task, Request, User, Comment, Attachment
import json
from django.utils import timezone
from datetime import timedelta

# --- Аутентификация ---
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'main/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'main/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('login')

# --- Основные страницы ---
@login_required
def home_view(request):
    # Получаем задачи, назначенные пользователю, и группируем их по статусу
    all_tasks = Task.objects.filter(assignee=request.user)

    new_tasks = all_tasks.filter(status=Task.Status.NEW)
    in_progress_tasks = all_tasks.filter(status=Task.Status.IN_PROGRESS)
    completed_tasks = all_tasks.filter(status=Task.Status.COMPLETED)

    department_employees = []
    if request.user.department:
        department_employees = User.objects.filter(department=request.user.department)

    today = timezone.now().date()
    soon_threshold = today + timedelta(days=3)

    context = {
        'new_tasks': new_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'employees': department_employees,
        'today': today,
        'soon_threshold': soon_threshold,
    }
    return render(request, 'main/home.html', context)

# --- Задачи (CRUD) ---
@login_required
def create_task_view(request):
    if request.method == 'POST':
        form = TaskCreationForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.author = request.user
            task.save()
            messages.success(request, f'Задача "{task.title}" успешно создана!')
            return redirect('home')
    else:
        form = TaskCreationForm(user=request.user)
    return render(request, 'main/create_task.html', {'form':form})

@login_required
def task_detail_view(request, pk):
    task = get_object_or_404(Task, pk=pk)

    # 1. ПРОВЕРКА ПРАВ ДОСТУПА
    is_author = request.user == task.author
    is_assignee = request.user == task.assignee
    is_leader = (request.user.is_staff and
                 task.author.department and
                 task.author.department == request.user.department)

    if not (is_author or is_assignee or is_leader):
        return HttpResponseForbidden("У вас нет доступа к этой задаче.")

    # 2. ОБРАБОТКА POST-ЗАПРОСОВ (когда пользователь нажимает кнопки)
    if request.method == 'POST':
        # Смена статуса
        if 'update_status' in request.POST:
            new_status = request.POST.get('status')
            if new_status in Task.Status.values:
                task.status = new_status
                task.save()
                messages.success(request, 'Статус задачи обновлён.')
            return redirect('task_detail', pk=task.pk)

        # Обновление задачи (исполнитель, срок)
        elif 'update_task' in request.POST:
            form = TaskUpdateForm(request.POST, instance=task, user=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Задача успешно обновлена.')
            return redirect('task_detail', pk=task.pk)

        # Добавление комментария
        elif 'add_comment' in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.author = request.user
                comment.task = task
                comment.save()
                messages.success(request, 'Комментарий добавлен.')
            return redirect('task_detail', pk=task.pk)

        # Добавление файла
        elif 'add_attachment' in request.POST:
            form = AttachmentForm(request.POST, request.FILES)
            if form.is_valid():
                attachment = form.save(commit=False)
                attachment.author = request.user
                attachment.task = task
                attachment.save()
                messages.success(request, 'Файл успешно добавлен.')
            return redirect('task_detail', pk=task.pk)

    # 3. ПОДГОТОВКА ДАННЫХ ДЛЯ ОТОБРАЖЕНИЯ СТРАНИЦЫ (GET-запрос)
    comments = task.comments.all()
    attachments = task.attachments.all()

    comment_form = CommentForm()
    update_form = TaskUpdateForm(instance=task, user=request.user)
    attachment_form = AttachmentForm()

    context = {
        'task': task,
        'comments': comments,
        'attachments': attachments,
        'comment_form': comment_form,
        'update_form': update_form,
        'attachment_form': attachment_form,
        'statuses': Task.Status.choices,
    }
    return render(request, 'main/task_detail.html', context)

@login_required
def edit_task_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.author != request.user:
        return HttpResponseForbidden("У вас нет прав для редактирования этой задачи.")
    if request.method == 'POST':
        form = TaskCreationForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задача успешно отредактирована.')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskCreationForm(instance=task, user=request.user)
    return render(request, 'main/edit_task.html', {'form': form, 'task': task})

@login_required
def delete_task_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if task.author != request.user:
        return HttpResponseForbidden("У вас нет прав для удаления этой задачи.")
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.error(request, f'Задача "{task_title}" была удалена.')
        return redirect('home')
    return render(request, 'main/delete_task_confirm.html', {'task': task})

# --- Заявки ---
@login_required
def request_list_view(request):
    # Доступ к списку заявок только у руководителей
    if not request.user.is_staff:
        return HttpResponseForbidden('Доступ к заявкам есть только у руководителей отделов.')
    user_requests = Request.objects.filter(requester=request.user).order_by('-created_at')
    return render(request, 'main/request_list.html', {'requests': user_requests})

@login_required
def create_request_view(request):
    # Создавать заявки могут только руководители отделов
    if not request.user.is_staff:
        return HttpResponseForbidden('Создание заявок доступно только руководителям отделов.')
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.requester = request.user
            selected_department = form.cleaned_data.get('department')
            if selected_department:
                req.department = selected_department
                if selected_department.leader:
                    req.assignee = selected_department.leader
            req.save()
            messages.success(request, f'Заявка "{req.title}" успешно создана.')
            return redirect('request_list')
    else:
        form = RequestForm()
    return render(request, 'main/create_request.html', {'form': form})

@login_required
def delete_request_view(request, pk):
    req = get_object_or_404(Request, pk=pk)
    
    # Проверяем права: автор заявки или руководитель отдела
    is_author = request.user == req.requester
    is_leader = (request.user.is_staff and 
                req.department and 
                req.department.leader == request.user)
    
    if not (is_author or is_leader):
        return HttpResponseForbidden("У вас нет прав для удаления этой заявки.")
    
    if request.method == 'POST':
        req_title = req.title
        req.delete()
        messages.error(request, f'Заявка "{req_title}" была удалена.')
        return redirect('request_list')
    
    return render(request, 'main/delete_request_confirm.html', {'request': req})

# --- Кабинет руководителя ---
@login_required
def manager_dashboard_view(request):
    if not request.user.is_staff:
        return HttpResponseForbidden('Доступ запрещён')

    # Логика для назначения заявки сотруднику
    if request.method == 'POST' and 'assign_request' in request.POST:
        request_id = request.POST.get('request_id')
        assignee_id = request.POST.get('assignee')
        if request_id and assignee_id:
            req = get_object_or_404(Request, pk=request_id)
            assignee = get_object_or_404(User, pk=assignee_id)

            if req.assignee == request.user:
                # Обновляем саму заявку
                req.assignee = assignee
                req.status = Request.RequestStatus.APPROVED  # Меняем статус на "Одобрена"
                req.save()

                # НОВАЯ ЛОГИКА: СОЗДАЁМ ЗАДАЧУ ДЛЯ СОТРУДНИКА
                Task.objects.create(
                    author=request.user,  # Автор задачи - руководитель
                    assignee=assignee,  # Исполнитель - выбранный сотрудник
                    title=f'Выполнить по заявке: {req.title}',
                    description=f'Необходимо выполнить работу по заявке от {req.requester.get_full_name()}.\n\n'
                                f'Обоснование: {req.justification}'
                )

                messages.success(request, f'Заявка "{req.title}" назначена исполнителю {assignee.get_full_name()}.')

            return redirect('manager_dashboard')

    # ... (остальной код функции для отображения страницы остаётся без изменений) ...
    pending_requests = Request.objects.filter(
        assignee=request.user,
        status=Request.RequestStatus.NEW
    ).order_by('-created_at')

    department_employees = []
    if request.user.department:
        department_employees = User.objects.filter(department=request.user.department)

    context = {
        'requests': pending_requests,
        'employees': department_employees,
    }
    return render(request, 'main/manager_dashboard.html', context)

# НОВАЯ ФУНКЦИЯ для просмотра руководителем всех задач отдела
@login_required
def department_tasks_view(request):
    if not request.user.is_staff or not request.user.department:
        return HttpResponseForbidden("Доступ есть только у руководителей отделов.")
    department_tasks = Task.objects.filter(author__department=request.user.department).order_by('-created_at')
    context = {'tasks': department_tasks, 'department': request.user.department}
    return render(request, 'main/department_tasks.html', context)

@login_required
def update_task_status_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        task_id = data.get('task_id')
        new_status = data.get('status')

        task = get_object_or_404(Task, pk=task_id)

        # Проверка прав: менять статус может только исполнитель
        if task.assignee == request.user:
            task.status = new_status
            task.save()
            return JsonResponse({'success': True})

        return JsonResponse({'success': False, 'error': 'Permission denied'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})