from .base import *
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DATABASES = {
   
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
       # 'USER': 'postgres',
       # 'PASSWORD': 'XzvlRcV7hHudgR0Iicx6',
       # 'HOST': 'containers-us-west-85.railway.app',
       # 'PORT': 5574,
    } 
}