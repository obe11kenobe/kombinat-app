from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Эта строка говорит: "Все запросы на главный адрес сайта (http://127.0.0.1:8000/)
    # перенаправляй в файл urls.py нашего приложения main"
    path('', include('main.urls')),
]
