from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-1-ja)s(_sbcz9y&gs!57aqt!ebiod#kw4g$7l*nl%*9+_5m2$9"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Removing debug for the purposes of quickly shipping an image
# DEBUG = False
# Needs work
try:
    from .local import *
except ImportError:
    pass
