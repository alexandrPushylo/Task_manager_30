SECRET_KEY = 'django-insecure-k^%zsxe3c_b=hr-34aslv97r7fd=2zsdrfi-#s*p*e8&q4=5-n'
DEBUG = True
TECH_SUPPORT_MODE = False
ALLOWED_HOSTS = ['127.0.0.1', '10.0.0.3', 'localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    },
    'archive': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'kiptechb_archive',
        'USER': 'root',
        'PASSWORD': 'aln1409',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        }
    }
}

# TELEGRAM_BOT_TOKEN = "5463845945:AAF0a-diDnIB3_JkEncKUgjdnXuRwmRYO48"
TELEGRAM_BOT_TOKEN = '7029323236:AAF2AlsHeOzF4f3cqGjXYXAwXs2ltoAvtD4'