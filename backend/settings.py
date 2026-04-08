from pathlib import Path

from .config import settings

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = settings.secret_key.get_secret_value()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = settings.debug

ALLOWED_HOSTS = [".render.com", "localhost", "127.0.0.1"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ninja_extra",
    "myapi",
    "ninja_jwt",
    "django.contrib.postgres",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=settings.db_url.get_secret_value(),
        conn_max_age=600,
        ssl_require=True
    )
}




# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = "static/"

import os                                         

MEDIA_URL= '/media/'
MEDIA_ROOT= os.path.join(BASE_DIR, 'media')

from datetime import timedelta

SIMPLE_JWT= {
    'ACCESS_TOKEN_LIFETIME':timedelta(minutes= settings.jwt_access_lifetime_mins),
    'REFRESH_TOKEN_LIFETIME': timedelta(days= 1),
    'ROTATE_REFRESH_TOKENS': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,                   
    'AUTH_HEADER_TYPES': ('Bearer',),             
}

CELERY_BROKER_URL = settings.celery_broker_url.get_secret_value()
CELERY_RESULT_BACKEND = settings.celery_broker_url.get_secret_value()
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'
CELERY_RESULT_EXPIRES = 3600
    


EMAIL_BACKEND = settings.email_backend
EMAIL_HOST = settings.email_host
EMAIL_PORT = settings.email_port
EMAIL_USE_TLS = settings.email_use_tls
EMAIL_HOST_USER = settings.email_host_user

EMAIL_HOST_PASSWORD = settings.email_host_password.get_secret_value()

## Setting up Langsmith

import os
from backend.config import settings

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key.get_secret_value()
os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint