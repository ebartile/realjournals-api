import os
import sys
from decouple import config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY') 
APPEND_SLASH = False
API_HOST = config('API_HOST') 
ADMIN_HOST = config('ADMIN_HOST') 
ACCOUNT_HOST = config('ACCOUNT_HOST') 
TERMINAL_HOST = config('TERMINAL_HOST') 
LANDING_HOST = config('LANDING_HOST') 

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool) 

ALLOWED_HOSTS = [API_HOST, ACCOUNT_HOST, ADMIN_HOST, TERMINAL_HOST, LANDING_HOST]

ADMINS = (
    ("Emma", "ebartile@gmail.com"),
    ("Admin", "admin@realjournals.com"),
)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "django.contrib.sitemaps",
    "django.contrib.postgres",

    # Third party apps
    "djmail",
    "django_jinja",
    "django_jinja.contrib._humanize",
    "easy_thumbnails",
    "raven.contrib.django.raven_compat",
    "rest_framework",
    "django_filters",
    "drf_link_header_pagination",
    "social_django",
    "django_otp",
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_hotp',
    'django_otp.plugins.otp_email',
    'corsheaders',

    # Custom apps
    "apps",
    "apps.users.apps.UsersConfig",
    "apps.events.apps.EventsAppConfig",
    "apps.feedback.apps.FeedbackConfig",
    "apps.stats.apps.StatsConfig",
    "apps.telemetry.apps.TelemetryConfig",
    "apps.journals.apps.JournalsConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.attachments.apps.AttachmentsConfig",
    "apps.notifications.apps.NotificationsAppConfig",
    "apps.settings.apps.SettingsConfig",
    "apps.userstorage.apps.UserstorageConfig",
    "apps.timeline.apps.TimelineConfig",
    "apps.history.apps.HistoryConfig",
    "apps.references.apps.ReferencesConfig",
    "apps.transactions.apps.TransactionsConfig",
    "apps.likes.apps.LikesConfig",
    "apps.utils.apps.UtilsConfig",
    "apps.testimonials.apps.TestimonialsConfig",
]

MIDDLEWARE = [
    "apps.events.middleware.SessionIDMiddleware",

    'corsheaders.middleware.CorsMiddleware',
     
    # Default
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Added
    "django.middleware.locale.LocaleMiddleware",

    'apps.utils.middleware.UpdateUserLocationMiddleware', 

]

# For production use redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake"
    }
}

ROOT_URLCONF = 'realjournals.urls'

TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
            "match_extension": ".jinja",
        }
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        }
    },
]


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": 'django.db.backends.postgresql_psycopg2',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config("DB_PORT"),
    }
}



# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'GMT'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

# Static configuration.
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Don't forget to use absolute paths, not relative paths.
)

# Media configuration.
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

FILE_UPLOAD_PERMISSIONS = 0o644

LOGIN_URL = "https://account.realjournal.com/"

# Languages we provide translations for, out of the box.
LANGUAGES = [
    #("af", "Afrikaans"),  # Afrikaans
    # ("ar", "العربية‏"),  # Arabic
    #("ast", "Asturiano"),  # Asturian
    #("az", "Azərbaycan dili"),  # Azerbaijani
    #("bg", "Български"),  # Bulgarian
    #("be", "Беларуская"),  # Belarusian
    #("bn", "বাংলা"),  # Bengali
    #("br", "Bretón"),  # Breton
    #("bs", "Bosanski"),  # Bosnian
    # ("ca", "Català"),  # Catalan
    # ("cs", "Čeština"),  # Czech
    # ("cy", "Cymraeg"),  # Welsh
    # ("da", "Dansk"),  # Danish
    ("de", "Deutsch"),  # German
    # ("el", "Ελληνικά"),  # Greek
    ("en", "English (US)"),  # English
    # ("en-au", "English (Australia)"),  # Australian English
    # ("en-gb", "English (UK)"),  # British English
    # ("eo", "esperanta"),  # Esperanto
    # ("es", "Español"),  # Spanish
    # ("es-ar", "Español (Argentina)"),  # Argentinian Spanish
    # ("es-mx", "Español (México)"),  # Mexican Spanish
    # ("es-ni", "Español (Nicaragua)"),  # Nicaraguan Spanish
    # ("es-ve", "Español (Venezuela)"),  # Venezuelan Spanish
    # ("et", "Eesti"),  # Estonian
    # ("eu", "Euskara"),  # Basque
    # ("fa", "فارسی‏"),  # Persian
    # ("fi", "Suomi"),  # Finnish
    # ("fr", "Français"),  # French
    # ("fy", "Frysk"),  # Frisian
    # ("ga", "Irish"),  # Irish
    # ("gl", "Galego"),  # Galician
    # ("he", "עברית‏"),  # Hebrew
    # ("hi", "हिन्दी"),  # Hindi
    # ("hr", "Hrvatski"),  # Croatian
    # ("hu", "Magyar"),  # Hungarian
    # ("ia", "Interlingua"),  # Interlingua
    # ("id", "Bahasa Indonesia"),  # Indonesian
    # ("io", "IDO"),  # Ido
    # ("is", "Íslenska"),  # Icelandic
    # ("it", "Italiano"),  # Italian
    # ("ja", "日本語"),  # Japanese
    # ("ka", "ქართული"),  # Georgian
    # ("kk", "Қазақша"),  # Kazakh
    # ("km", "ភាសាខ្មែរ"),  # Khmer
    # ("kn", "ಕನ್ನಡ"),  # Kannada
    # ("ko", "한국어"),  # Korean
    # ("lb", "Lëtzebuergesch"),  # Luxembourgish
    # ("lt", "Lietuvių"),  # Lithuanian
    # ("lv", "Latviešu"),  # Latvian
    # ("mk", "Македонски"),  # Macedonian
    # ("ml", "മലയാളം"),  # Malayalam
    # ("mn", "Монгол"),  # Mongolian
    # ("mr", "मराठी"),  # Marathi
    # ("my", "မြန်မာ"),  # Burmese
    # ("nb", "Norsk (bokmål)"),  # Norwegian Bokmal
    # ("ne", "नेपाली"),  # Nepali
    # ("nl", "Nederlands"),  # Dutch
    # ("nn", "Norsk (nynorsk)"),  # Norwegian Nynorsk
    # ("os", "Ирон æвзаг"),  # Ossetic
    # ("pa", "ਪੰਜਾਬੀ"),  # Punjabi
    # ("pl", "Polski"),  # Polish
    # ("pt", "Português (Portugal)"),  # Portuguese
    # ("pt-br", "Português (Brasil)"),  # Brazilian Portuguese
    # ("ro", "Română"),  # Romanian
    # ("ru", "Русский"),  # Russian
    # ("sk", "Slovenčina"),  # Slovak
    # ("sl", "Slovenščina"),  # Slovenian
    # ("sq", "Shqip"),  # Albanian
    # ("sr", "Српски"),  # Serbian
    # ("sr-latn", "srpski"),  # Serbian Latin
    # ("sv", "Svenska"),  # Swedish
    # ("sw", "Kiswahili"),  # Swahili
    # ("ta", "தமிழ்"),  # Tamil
    # ("te", "తెలుగు"),  # Telugu
    # ("th", "ภาษาไทย"),  # Thai
    # ("tr", "Türkçe"),  # Turkish
    # ("tt", "татар теле"),  # Tatar
    # ("udm", "удмурт кыл"),  # Udmurt
    # ("uk", "Українська"),  # Ukrainian
    # ("ur", "اردو‏"),  # Urdu
    # ("vi", "Tiếng Việt"),  # Vietnamese
    # ("zh-hans", "中文(简体)"),  # Simplified Chinese
    # ("zh-hant", "中文(香港)"),  # Traditional Chinese
]

# Languages using BiDi (right-to-left) layout
LANGUAGES_BIDI = ["he", "ar", "fa", "ur"]

LOCALE_PATHS = (
    os.path.join(BASE_DIR, "locale"),
)

# Session and CSRF configuration
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 180000  # (30 minutes) and set SESSION_EXPIRE_AT_BROWSER_CLOSE to false
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_NAME = 'realjournals'
SESSION_COOKIE_DOMAIN = '.realjournals.com'
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_AGE = None
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [
    "https://{}".format(API_HOST), 
    "https://{}".format(ADMIN_HOST), 
    "https://{}".format(ACCOUNT_HOST), 
    "https://{}".format(TERMINAL_HOST),
    "https://{}".format(LANDING_HOST)
]


# MAIL OPTIONS
DEFAULT_FROM_EMAIL = "Real Journals <admin@realjournals.com>"
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
# EMAIL_USE_SSL = True
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

RABBITMQ_USER = config('RABBITMQ_USER', default='guest')
RABBITMQ_PASSWORD = config('RABBITMQ_PASSWORD', default='guest')
RABBITMQ_HOST = config('RABBITMQ_HOST', default='localhost')
RABBITMQ_PORT = config('RABBITMQ_PORT', default='5672')

from kombu import Queue  # noqa

# CELERY
CELERY_ENABLED = True
CELERY_BROKER_URL = f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/'
CELERY_RESULT_BACKEND = None # for a general installation, we don't need to store the results
CELERY_ACCEPT_CONTENT = ['json', ]  # Values are 'pickle', 'json', 'msgpack' and 'yaml'
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = 'Africa/Nairobi'
CELERY_TASK_DEFAULT_QUEUE = 'tasks'
CELERY_QUEUES = (
    Queue('tasks', routing_key='task.#'),
    Queue('transient', routing_key='transient.#', delivery_mode=1)
)
CELERY_TASK_DEFAULT_EXCHANGE = 'tasks'
CELERY_TASK_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'task.default'

# 0 notifications will work in a synchronous way
# >0 an external process will check the pending notifications and will send them
# collapsed during that interval
CHANGE_NOTIFICATIONS_MIN_INTERVAL = 60  # seconds
SEND_BULK_EMAILS_WITH_CELERY = True

DJMAIL_REAL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DJMAIL_SEND_ASYNC = True
DJMAIL_MAX_RETRY_NUMBER = 3
DJMAIL_TEMPLATE_EXTENSION = "jinja"

# Events backend
EVENTS_PUSH_BACKEND_OPTIONS = {
    "url": f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/'
}
EVENTS_PUSH_BACKEND = "apps.events.backends.rabbitmq.EventsPushBackend"

# Message System
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse"
        }
    },
    "formatters": {
        "complete": {
            "format": "%(levelname)s:%(asctime)s:%(module)s %(message)s"
        },
        "simple": {
            "format": "%(levelname)s:%(asctime)s: %(message)s"
        },
        "null": {
            "format": "%(message)s",
        },
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[%(server_time)s] %(message)s",
        },
    },
    "handlers": {
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "apps.utils.logs.CustomAdminEmailHandler",
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
        "database": {
            "level": "ERROR",
            "class": "apps.utils.logs.DatabaseHandler",
            "formatter": "complete",
        }        
    },
    "loggers": {
        "django": {
            "handlers": ["null", "database"],
            "propagate": True,
            "level": "INFO",
        },
        "django.request": {
            "handlers": [
                "database",
                "mail_admins", 
                "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "realjournals": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        }
    }
}

AUTH_USER_MODEL = "users.User"

# Authentication settings (only for django admin)
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # default
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.twitter.TwitterOAuth'
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '884185272139-vlh8074gg07n3n5kigejkc0umb4dfvs9.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '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'

SOCIAL_AUTH_FACEBOOK_KEY = "735660328403343"        # App ID
SOCIAL_AUTH_FACEBOOK_SECRET = "5b56feb6ba3e55027c5b4a033707dab9"  # App Secret
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email', 'user_link'] # add this
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {       # add this
  'fields': 'id, name, email, picture.type(large), link'
}
SOCIAL_AUTH_FACEBOOK_EXTRA_DATA = [                 # add this
    ('name', 'name'),
    ('email', 'email'),
    ('picture', 'picture'),
    ('link', 'profile_url'),
]

SOCIAL_AUTH_TWITTER_KEY = 'z5WUvOyfSv36mwAv0totxy2yw'
SOCIAL_AUTH_TWITTER_SECRET = '8q4ySzPHRCmQw8aAT0bTsZ0AeNIMRdUPDJLibfVVredyse4ZA2'

DATE_INPUT_FORMATS = (
    "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%b %d %Y",
    "%b %d, %Y", "%d %b %Y", "%d %b, %Y", "%B %d %Y",
    "%B %d, %Y", "%d %B %Y", "%d %B, %Y"
)

MAX_AGE_AUTH_TOKEN = 1800 # 30 minutes
MAX_AGE_CANCEL_ACCOUNT = 30 * 24 * 60 * 60  # 30 days in seconds


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        "apps.users.backends.Token"
        # TODO: add token auth
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': None,
        'user': None
    },
    "EXCEPTION_HANDLER": "apps.utils.exceptions.exception_handler",
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'drf_link_header_pagination.LinkHeaderPagination',
    "PAGINATE_BY": 30,
    "PAGINATE_BY_PARAM": "page_size",
    "MAX_PAGINATE_BY": 1000
}

SOUTH_MIGRATION_MODULES = {
    'easy_thumbnails': 'easy_thumbnails.south_migrations',
}

# CUSTOM SETTINGS
PUBLIC_REGISTER_ENABLED = True
SEARCHES_MAX_RESULTS = 150

THN_AVATAR_SIZE = 80                # 80x80 pixels
THN_AVATAR_BIG_SIZE = 300           # 300x300 pixels
THN_LOGO_SMALL_SIZE = 80            # 80x80 pixels
THN_LOGO_BIG_SIZE = 300             # 300x300 pixels
THN_TIMELINE_IMAGE_SIZE = 640       # 640x??? pixels
THN_CARD_IMAGE_WIDTH = 300          # 300 pixels
THN_CARD_IMAGE_HEIGHT = 200         # 200 pixels
THN_PREVIEW_IMAGE_WIDTH = 800       # 800 pixels

THN_AVATAR_SMALL = "avatar"
THN_AVATAR_BIG = "big-avatar"
THN_LOGO_SMALL = "logo-small"
THN_LOGO_BIG = "logo-big"
THN_ATTACHMENT_TIMELINE = "timeline-image"
THN_ATTACHMENT_CARD = "card-image"
THN_ATTACHMENT_PREVIEW = "preview-image"

THUMBNAIL_ALIASES = {
    "": {
        THN_AVATAR_SMALL: {"size": (THN_AVATAR_SIZE, THN_AVATAR_SIZE), "crop": True},
        THN_AVATAR_BIG: {"size": (THN_AVATAR_BIG_SIZE, THN_AVATAR_BIG_SIZE), "crop": True},
        THN_LOGO_SMALL: {"size": (THN_LOGO_SMALL_SIZE, THN_LOGO_SMALL_SIZE), "crop": True},
        THN_LOGO_BIG: {"size": (THN_LOGO_BIG_SIZE, THN_LOGO_BIG_SIZE), "crop": True},
        THN_ATTACHMENT_TIMELINE: {"size": (THN_TIMELINE_IMAGE_SIZE, 0), "crop": True},
        THN_ATTACHMENT_CARD: {"size": (THN_CARD_IMAGE_WIDTH, THN_CARD_IMAGE_HEIGHT), "crop": True},
        THN_ATTACHMENT_PREVIEW: {"size": (THN_PREVIEW_IMAGE_WIDTH, 0), "crop": False},
    },
}

# Feedback module settings
FEEDBACK_ENABLED = True
FEEDBACK_EMAIL = "support@realjournals.com"

# Stats module settings
STATS_ENABLED = True
STATS_CACHE_TIMEOUT = 60 * 60  # In second

# If is True /front/sitemap.xml show a valid sitemap of front client
FRONT_SITEMAP_ENABLED = False
FRONT_SITEMAP_CACHE_TIMEOUT = 24 * 60 * 60  # In second
FRONT_SITEMAP_PAGE_SIZE = 25000

MAX_PRIVATE_ACCOUNTS_PER_USER = None  # None == no limit
MAX_PUBLIC_ACCOUNTS_PER_USER = None  # None == no limit
MAX_MEMBERSHIPS_PRIVATE_ACCOUNT = None  # None == no limit
MAX_MEMBERSHIPS_PUBLIC_ACCOUNT = None  # None == no limit
MAX_PENDING_MEMBERSHIPS = 30  # Max number of unconfirmed memberships in a accounts

# TELEMETRY TODO
ENABLE_TELEMETRY = False
# RUDDER_WRITE_KEY = "1kmTTxJoSmaZNRpU1uORpyZ8mqv"
# DATA_PLANE_URL = "https://telemetry./"

# TODO: add redis port and host
# TODO: add recaptcha

RECAPTCHA_ENABLED = False
RECAPTCHA_SITEKEY = "7d7d4dcf-db28-49c2-b97a-ea95d68332bc"
RECAPTCHA_SIZE = "normal"

# Define the BRAND settings
BRAND_FAVICON_URL = 'your_favicon_url'
BRAND_LOGO_URL = 'your_logo_url'
BRAND_SUPPORT_URL = 'your_support_url'
BRAND_TERMS_URL = 'your_terms_url'
BRAND_POLICY_URL = 'your_policy_url'

AUTH_CREDENTIAL = "email"

PRIVATE_USER_PROFILES = True

EXTRA_BLOCKING_CODES = []

# Setting DEFAULT_ACCOUNT_SLUG_PREFIX to false removes the username from account slug
DEFAULT_ACCOUNT_SLUG_PREFIX = True

APP_EXTRA_EXPOSE_HEADERS = [
    "realjournals-info-account-memberships",
    "realjournals-info-account-is-private",
    "realjournals-info-order-updated"
]

SOCIAL_AUTH_JSONFIELD_ENABLED = True

SOCIAL_AUTH_LOGIN_REDIRECT_URL = "https://{}".format(TERMINAL_HOST)
WSGI_APPLICATION = 'realjournals.wsgi.application'

OTP_TOTP_ISSUER = "RealJournal"

INTERNAL_IPS = []

# Whitelist specific origins (comma-separated list)
CORS_ALLOWED_ORIGINS = [
    "https://{}".format(API_HOST), 
    "https://{}".format(ADMIN_HOST), 
    "https://{}".format(ACCOUNT_HOST), 
    "https://{}".format(TERMINAL_HOST),
    "https://{}".format(LANDING_HOST)    
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [ "access-control-allow-origin",  
                        "access-control-allow-headers",
                        "content-type", "x-requested-with",
                        "authorization", "accept-encoding",
                        "x-disable-pagination", "x-lazy-pagination",
                        "x-host", "x-session-id", "set-orders", "x-pagination-count", "x-paginated", "x-paginated-by",
                       "x-pagination-current", "x-pagination-next", "x-pagination-prev",
                       "x-site-host", "x-site-register", "x-csrftoken"]

CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]

# NOTE: DON'T INSERT ANYTHING AFTER THIS BLOCK
if "test" in sys.argv:
    print("\033[1;91mNo django tests.\033[0m")
    print("Try: \033[1;33mpy.test\033[0m")
    sys.exit(0)
# NOTE: DON'T INSERT MORE SETTINGS AFTER THIS LINE
