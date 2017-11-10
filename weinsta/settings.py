"""
Django settings for weinsta project.

Generated by 'django-admin startproject' using Django 1.11.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'rl&6=$$^=gx$*zlmtj2hdywia!ue!@qyy0=xet1kkyizg7-2m9'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    'allauth.socialaccount.providers.instagram',
    'allauth.socialaccount.providers.weibo',
    'allauth.socialaccount.providers.twitter',

    'weinsta',
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

ROOT_URLCONF = 'weinsta.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',     # for media
            ],
        },
    },
]

WSGI_APPLICATION = 'weinsta.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

# -------- allauth settings --------

ACCOUNT_USERNAME_MIN_LENGTH = 4
ACCOUNT_USERNAME_BLACKLIST = ['admin', 'weinsta', 'instgram', 'weibo', 'wechat', 'root', 'staff', 'notification',
                              'subscription', 'system', 'bill', 'account']
SOCIALACCOUNT_AUTO_SIGNUP = False

ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True


# -------- added settings --------

SITE_ID = 1

PROXIES = {}

MEDIA_URL = '/m/'
MEDIA_ROOT = os.path.abspath('/opt/data')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]


SOCIALACCOUNT_PROVIDERS = {
    'instagram': {
        'SCOPE': ['basic', 'public_content', 'follower_list', 'comments', 'relationships', 'likes']
    }
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)-8s [%(asctime)s] [%(process)-6d] [%(threadName)-8s] %(name)-30s [%(lineno)d] %(message)s'
        },
        'simple': {
            'format': '%(levelname)-8s [%(asctime)s] %(name)-30s [%(lineno)d] %(message)s'
        },
        'colored': {
            'format': '%(levelname)-8s [%(asctime)s] %(name)s.%(funcName)s [%(lineno)d] %(message)s',
            # color reference: https://pypi.python.org/pypi/termcolor
            # 'LEVEL': ('fg-color', 'bg-color', ['attr1', 'attr2', ...])
            '()': 'pyutils.logger.ColorFormatter',
            'colors': {
                'TRACE': ('grey', None, []),
                'DEBUG': ('grey', None, ['bold']),
                'INFO': (None, None, []),
                'WARNING': ('yellow', None, []),
                'ERROR': ('red', None, []),
                'CRITICAL': ('red', 'white', []),

            }
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'colored'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'weinsta': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        # 'services': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG' if DEBUG else 'WARNING',
        # },
        # 'tweepy': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG' if DEBUG else 'WARNING',
        # },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
    },
}


CACHES = {
    # 'default': {
    #     'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    #     'TIMEOUT': 600,     # seconds
    #     'OPTIONS': {
    #         'MAX_ENTRIES': 1000
    #     }
    # },
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.abspath(os.path.join(MEDIA_ROOT, 'cache')),
        'TIMEOUT': 3600,     # seconds
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    },
    # # python manage.py createcachetable
    # 'db': {
    #     'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
    #     'LOCATION': 'weinsta_cache',
    # },
    # 'memcache': {
    #     'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    #     'LOCATION': [
    #         '172.19.26.240:11211',
    #         '172.19.26.242:11212',
    #         '172.19.26.244:11213',
    #     ]
    # }
}
MIDDLEWARE.insert(0, 'django.middleware.cache.UpdateCacheMiddleware')
MIDDLEWARE.append('django.middleware.cache.FetchFromCacheMiddleware')
CACHE_MIDDLEWARE_SECONDS = 3600

