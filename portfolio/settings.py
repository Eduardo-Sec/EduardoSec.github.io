import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-dev-only-change-in-production'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'true').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost 127.0.0.1').split()

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.csp.ContentSecurityPolicyMiddleware',
]

ROOT_URLCONF = 'portfolio.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'portfolio.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Chicago'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Content-hashed filenames (e.g. main.a3f8c9.css) so a changed file gets a
# new URL instead of relying on Cloudflare/browsers to notice bytes changed
# at the same old URL -- no more manual cache purges after every deploy.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Site metadata used in templates
SITE_TITLE = 'Eduardo Bustamante'
SITE_DESCRIPTION = (
    'Cybersecurity student at UNO and SOC Analyst Intern. '
    'Detection engineering, homelab builds, and CTF writeups.'
)
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')

CERTS_IN_PROGRESS = 2
TOOLS_AND_TECHNOLOGIES = 15
ANALYST_START_DATE = '2025-10-01'

# Production security — active only when DEBUG=false (set via env on server)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Django 4+ checks the browser's Origin/Referer against this list when
    # TLS is terminated upstream (Cloudflare) instead of on this server —
    # without it, admin logins fail CSRF checks even though everything
    # else is configured correctly.
    CSRF_TRUSTED_ORIGINS = [SITE_URL]
    SESSION_COOKIE_SAMESITE = 'Strict'
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_SSL_REDIRECT = True
    # Raised from the initial 1hr trial period to 1 day now that HTTPS has
    # run clean in production. Still holding off on INCLUDE_SUBDOMAINS (no
    # subdomains exist yet, no benefit) and PRELOAD (submitting to browser
    # preload lists takes months to reverse -- wait for a longer clean run
    # at this duration first).
    SECURE_HSTS_SECONDS = 86400
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
