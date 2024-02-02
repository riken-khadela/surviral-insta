"""
Django settings for surviral_avd project.

Generated by 'django-admin startproject' using Django 3.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-_h2&-=+0!try9ok)8@+)!!(o5e8s&6mjd!p350zdks=mu)@(b='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

INSTALLED_APPS = INSTALLED_APPS + [
    'django_extensions',
    "rangefilter",
    'core',
    'twbot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'surviral_avd.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'surviral_avd.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': 'Instabot',
#         'USER': 'postgres',
#         'PASSWORD': '0000',
#         'HOST':'localhost',
#         'PORT': '5432',
#     }
# }

# old_pcs = ['pc3','pc8','pc11','pc20','pkpc16','pkpc17']

# if os.getenv('PC') in old_pcs :
#     NEW_PC = False
# else : NEW_PC = True
# if NEW_PC :
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': 'Instagram2',
#             'USER': 'surviraluser',
#             'PASSWORD': 'Surviral#786',
#             'HOST': 'surviral-project.c4jxfxmbuuss.ap-southeast-1.rds.amazonaws.com',
#             'PORT': '5432'
#         }
#     }
# else :
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': 'Instagram',
#             'USER': 'surviraluser',
#             'PASSWORD': 'Surviral#786',
#             'HOST': 'surviral-project.c4jxfxmbuuss.ap-southeast-1.rds.amazonaws.com',
#             'PORT': '5432'
#         }
#     }
DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'Instagram',
            'USER': 'surviraluser',
            'PASSWORD': 'Surviral#786',
            'HOST': 'surviral-project.c4jxfxmbuuss.ap-southeast-1.rds.amazonaws.com',
            'PORT': '5432',
            'CONN_MAX_AGE' : 20,
        }
    }


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.User'

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000000
MAX_UPLOAD_SIZE = "51000000"  # from KB to MB

# avd path
AVD_DIR_PATH = os.environ.get("AVD_DIR_PATH", os.environ.get("ANDROID_AVD_HOME"))

# Remote system Number
SYSTEM_NO = ""

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587  # TLS port for Gmail
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'rikenkhadela22@gmail.com'  # Your Gmail address
EMAIL_HOST_PASSWORD = 'Riken@123'