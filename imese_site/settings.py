import os
from pathlib import Path
from django.conf import settings

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'votre-clé-secrète-ici'  # Gardez celle générée par Django

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
    # Rest Framework
    'rest_framework',
    # Vos applications
    'main',
    'formations',
    'membres',
    'ressources',
    'actualites',
    'paiements',
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

ROOT_URLCONF = 'imese_site.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        
        'DIRS': [
             BASE_DIR / 'main' / 'templates',
             BASE_DIR / 'formations' / 'templates',
             BASE_DIR / 'membres' / 'templates',
             BASE_DIR / 'ressources' / 'templates',
             BASE_DIR / 'actualites' / 'templates',
        ],
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

WSGI_APPLICATION = 'imese_site.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
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



LOGIN_URL = '/espace-membre/'
LOGIN_REDIRECT_URL = '/espace-membre/'
LOGOUT_REDIRECT_URL = '/'

# code de langue et fuseau horaire
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Créer le dossier static
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

print(f"MEDIA_ROOT: {MEDIA_ROOT}")  # Debug
print(f"MEDIA_URL: {MEDIA_URL}")    # Debug
# Pour le développement

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuration paiement SMS
SMS_API_URL = 'http://localhost:10000'  # ou ton URL de production
SMS_API_KEY = 'ton_api_key_secrete'
SMS_WEBHOOK_SECRET = 'ton_secret_webhook'

# Numéros de paiement
PAYMENT_NUMBERS = {
    'orange': '+226 54 17 93 69',
    'moov': '+226 72 68 95 58',
}

# Expiration des paiements (en minutes)
PAYMENT_EXPIRY_MINUTES = 5

# Configuration email de base
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # N'oublies pas le Gmail
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'contact@clubimese.bf'
EMAIL_HOST_PASSWORD = 'ton_mot_de_passe_email'
DEFAULT_FROM_EMAIL = 'Club IMESE <contact@clubimese.bf>'
ENABLE_PAYMENT_EMAILS = True

# Allowed hosts pour le webhook
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'ton-domaine.com',
    'www.ton-domaine.com',
    # IPs pour Forward SMS
    '34.95.123.45',  # Exemple d'IP
]

# Sécurité emails
EMAIL_TIMEOUT = 30
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None

# Pour production
if not DEBUG:
    # Utiliser variables d'environnement
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# ============================================
# CONFIGURATION FORWARD SMS WEBHOOK
# ============================================
# Clé secrète pour valider les webhooks Forward SMS
# Change cette valeur en production! Utilise une variable d'environnement
FORWARD_SMS_WEBHOOK_KEY = os.environ.get(
    'FORWARD_SMS_WEBHOOK_KEY',
    'dev-secret-key-change-this-in-production'
)

# IPs autorisées pour Forward SMS (optionnel, pour extra sécurité)
FORWARD_SMS_ALLOWED_IPS = [
    '34.95.123.45',    # Forward SMS IP (à vérifier sur leur site)
    '127.0.0.1',       # Localhost pour tests
]

# URL de redirection après paiement réussi
PAYMENT_SUCCESS_URL = 'http://votre-domaine.com/payment/success/'