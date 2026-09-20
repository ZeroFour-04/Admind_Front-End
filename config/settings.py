"""
Ajustes del servidor web de AdMind.

Este proyecto no tiene base de datos: todo dato se lo pide a la API de
Admind_Backend a través de `cliente_api/`.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DEBUG = True

ALLOWED_HOSTS = []


INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "apps.cuentas",
    "apps.conjuntos",
    "apps.paneles",
    "apps.reservas",
    "apps.reglas",
    "apps.anuncios",
    "apps.triage",
    "apps.unidades",
    "apps.usuarios",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Después de las sesiones: necesita leer el token guardado en ellas.
    "apps.cuentas.sesion.SesionRequeridaMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Sin base de datos. Las sesiones de este servidor se guardan en archivos
# (carpeta temporal del sistema): ahí vive el token de la API, que el navegador
# nunca ve. Al navegador solo le llega la cookie con el id de la sesión.
DATABASES = {}
SESSION_ENGINE = "django.contrib.sessions.backends.file"
SESSION_COOKIE_HTTPONLY = True


# La API de Admind_Backend. `cliente_api/` es el único que la usa.
ADMIND_API_URL = os.environ["ADMIND_API_URL"].rstrip("/")
ADMIND_API_TIEMPO_ESPERA = 10  # segundos


LANGUAGE_CODE = "es-co"

TIME_ZONE = "America/Bogota"

USE_I18N = True

USE_TZ = True


# Archivos estáticos. El sistema de diseño se sirve desde su carpeta, sin
# copiarlo: queda en /static/design-system/.
STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    ("design-system", BASE_DIR / "design-system"),
]
