# Educational System (Edora)

Backend системы управления языковым центром / образовательной платформы.

Проект реализован на **Django + DRF**, использует **PostgreSQL**, **JWT-аутентификацию**, административную панель на базе **django-jazzmin**, и разворачивается в продакшене через **Docker + docker-compose + Nginx**.

---

## Технологический стек

- **Язык:** Python 3.12
- **Web-фреймворк:** Django 5.x
- **API:** Django REST Framework, django-filters, drf-spectacular
- **Аутентификация:** djangorestframework-simplejwt (JWT)
- **БД:** PostgreSQL 16 (в Docker)
- **Админка:** django-jazzmin
- **Сервер приложений:** Gunicorn
- **Веб-сервер:** Nginx
- **Контейнеризация:** Docker, docker-compose

---

## Архитектура проекта

Упрощённое дерево проекта:

```text
Educational_system/
├─ base/                     # Корневой Django-проект
│  ├─ __init__.py
│  ├─ asgi.py
│  ├─ settings.py            # Основные настройки проекта
│  ├─ urls.py
│  └─ wsgi.py
│
├─ Education/                # Основное приложение домена
│  ├─ __init__.py
│  ├─ admin.py               # Регистрация моделей в админке
│  ├─ apps.py
│  ├─ forms.py
│  ├─ migrations/            # Миграции (отслеживаются в git)
│  ├─ models.py              # Модели (User, Course, Group, Lesson, Attendance, Payment, ...)
│  ├─ permissions.py
│  ├─ serializers.py         # DRF-сериалайзеры
│  ├─ tests.py
│  └─ views.py               # DRF-вьюхи / бизнес-логика
│
├─ static/                   # Статические файлы проекта
│  ├─ css/
│  │  └─ jazzmin-custom.css  # Кастомизация темы Jazzmin
│  └─ images/
│     └─ new_logo.png        # Логотип для админки
│
├─ nginx/
│  └─ default.conf           # Конфиг Nginx для продакшена
│
├─ media/                    # Медиаконтент (в проде монтируется в volume)
│
├─ Dockerfile                # (опционально) dev Dockerfile
├─ Dockerfile.prod           # Боевой Dockerfile
├─ docker-compose.yml        # (если нужен dev docker-compose)
├─ docker-compose.prod.yml   # Продакшен docker-compose
│
├─ .env                      # Локальные настройки (не коммитятся)
├─ .env.prod                 # Продакшен настройки (на сервере)
│
├─ manage.py
├─ requirements.txt
└─ .gitignore
