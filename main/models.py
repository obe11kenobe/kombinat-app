from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings


class Department(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название отдела')

    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_department',
        verbose_name='Руководитель'
    )

    def __str__(self):
        return self.name

class User(AbstractUser):
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Отдел'
    )
    patronymic = models.CharField(max_length=150, blank=True, verbose_name='Отчество')

    # ИСПРАВЛЕНИЕ: Добавьте эти два поля для решения конфликта
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name='custom_user_set',  # Уникальное имя обратной связи
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_permissions_set',  # Уникальное имя обратной связи
        related_query_name='user',
    )

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    def __str__(self):
        return self.get_full_name() or self.username

class Task(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        IN_PROGRESS = 'in_progress', 'В работе'
        COMPLETED = 'completed', 'Выполнена'
        CANCELED = 'canceled', 'Отменена'

    class Priority(models.TextChoices):
        LOW = 'low', 'Низкий'
        MEDIUM = 'medium', 'Средний'
        HIGH = 'high', 'Высокий'

    title = models.CharField(max_length=200, verbose_name='Заголовок задачи')
    description = models.TextField(verbose_name='Описание задачи', blank=True)
    status = models.CharField(max_length=20,
                              choices=Status.choices,
                              default=Status.NEW,
                              verbose_name='Статус')
    priority = models.CharField(max_length=20,
                                choices=Priority.choices,
                                default=Priority.MEDIUM,
                                verbose_name='Приоритет')
    deadline = models.DateField(verbose_name='Срок выполнения', blank=True, null=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='authored_tasks',
                               verbose_name='Автор')
    assignee = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='assigned_tasks',
                               verbose_name='Исполнитель')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')


    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']  # Сортировка по умолчанию - сначала новые

    def __str__(self):
        return self.title

class Request(models.Model):
    class RequestType(models.TextChoices):
        HARDWARE = 'hw', 'Оборудование'
        SOFTWARE = 'sw', 'Программное обеспечение'

    class RequestStatus(models.TextChoices):
        NEW = 'new', 'Новая'
        APPROVED = 'approved', 'Одобрена руководителем'
        REJECTED = 'rejected', 'Отклонена'

    # 1. Добавляем недостающее поле 'title'
    title = models.CharField(max_length=255, verbose_name='Наименование')

    # 2. Добавляем недостающее поле 'justification' (Обоснование)
    justification = models.TextField(verbose_name='Обоснование', blank=True)

    # 3. Исправляем поле 'request_type'
    request_type = models.CharField(
        max_length=20,
        choices=RequestType.choices, # Указываем правильные choices
        verbose_name='Тип заявки'
    )

    # 4. Добавляем недостающее поле 'status'
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.NEW,
        verbose_name='Статус заявки'
    )

    requester = models.ForeignKey(User,
                                  on_delete=models.CASCADE,
                                  verbose_name='Автор заявки')
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        verbose_name='Отдел-исполнитель'
    )
    assignee = models.ForeignKey(User,
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 blank=True,
                                 verbose_name='Исполнитель',
                                 related_name='assigned_requests')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        # Также исправим отображение, чтобы было информативно
        return f'Заявка №{self.pk} на {self.title}'

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments', verbose_name='Задача')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Автор')
    text = models.TextField(verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

class Attachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name