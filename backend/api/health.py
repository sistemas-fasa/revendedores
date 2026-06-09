import subprocess
from pathlib import Path

from django.db import connection
from django.http import JsonResponse
from django.utils import timezone


SERVICE_NAME = "ventas-ferreteria"


def _current_version():
    repo_root = Path(__file__).resolve().parents[2]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except Exception:
        return "unknown"

    return result.stdout.strip() or "unknown"


def _health_payload(status, database, error=None):
    payload = {
        "status": status,
        "service": SERVICE_NAME,
        "database": database,
        "version": _current_version(),
        "time": timezone.now().isoformat(),
    }
    if error:
        payload["error"] = error
    return payload


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse(
            _health_payload("error", "error", "database unavailable"),
            status=500,
        )

    return JsonResponse(_health_payload("ok", "ok"))
