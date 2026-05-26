# middleware.py
from django.utils import timezone
from .models import RegistroSesion

class ActivityTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Solo si el usuario está autenticado y hace una petición a tu API
        if request.user.is_authenticated and request.path.startswith('/api/') and not request.path.endswith('/token/'):
            try:
                # Buscar la sesión activa más reciente
                sesion = RegistroSesion.objects.filter(
                    usuario=request.user,
                    fin_sesion__isnull=True
                ).latest('inicio_sesion')

                # Actualizar solo si pasó más de 1 minuto desde la última actualización
                if (timezone.now() - sesion.last_activity).total_seconds() > 60:
                    sesion.last_activity = timezone.now()
                    sesion.save(update_fields=['last_activity'])

            except RegistroSesion.DoesNotExist:
                pass  # No hacer nada si no hay sesión activa

        return response