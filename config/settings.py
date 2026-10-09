"""
Django settings for the StoryNest blog.

Development defaults are used unless environment variables override them:
    DJANGO_SECRET_KEY, DJANGO_DEBUG (0/1), DJANGO_ALLOWED_HOSTS (comma separated)
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-me-before-deploying",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h]
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = [
    "storynest-bqxg.onrender.com",
    "localhost",
    "127.0.0.1",
]

# ---------------------------------------------------------------- Site settings
SITE_NAME = "StoryNest"
SITE_TAGLINE = "A cozy place for stories, ideas and honest notes."
AUTHOR_NAME = "Rosie"
FOOTER_STATEMENT = "Life, Styled by Rosie"
ABOUT_TEXT = (
    "Welcome to my little corner of the internet. I write about slow travel, "
    "small spaces and the things that make an ordinary day feel considered."
)
NEWSLETTER_TEXT = (
    "One note a month: new posts, favorite finds and a peek behind the scenes."
)
# Shown in the footer and on the Contact page. Replace with your own details.
CONTACT_PHONE = "123-456-7890"
CONTACT_EMAIL = "info@mysite.com"
CONTACT_ADDRESS = "500 Terry Francine Street, San Francisco, CA 94158"
SOCIAL_LINKS = [
    ("Instagram", "https://www.instagram.com/"),
    ("Pinterest", "https://www.pinterest.com/"),
    ("Facebook", "https://www.facebook.com/"),
    ("YouTube", "https://www.youtube.com/"),
]
# When True, the sign-up form offers a "let me write posts" checkbox that puts the
# new user in the Authors group. Turn it off to hand out author rights in /admin only.
ALLOW_AUTHOR_SIGNUP = True
AUTHORS_GROUP = "Authors"
POSTS_PER_PAGE = 6

# ---------------------------------------------------------------- Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "blog",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "blog.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# -------------------------------------------------------------------- Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------ Auth routes
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "blog:home"
LOGOUT_REDIRECT_URL = "blog:home"

# ---------------------------------------------------------------- Internationalisation
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------- Static and media
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Faster password hashing while running the test suite only.
import sys  # noqa: E402

if "test" in sys.argv:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
