from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Registrar señales que aplican reglas de negocio al persistir modelos.
        from . import signals  # noqa: F401
