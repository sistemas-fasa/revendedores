from .settings import *  # noqa: F401,F403


# En CI se usan sqlite, pero se conservan los alias extra (ej: `fe`)
# que el settings base haya agregado. Solo se reemplazan default/fasa.
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'test.sqlite3',
}
DATABASES['fasa'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'test_fasa.sqlite3',
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
