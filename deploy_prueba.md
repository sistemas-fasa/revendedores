# Deploy de Prueba - Docker

Entorno de prueba aislado con Docker en `192.168.0.195` (fasa_195).

## Servicios y Puertos

| Servicio | URL | Descripcion |
|----------|-----|-------------|
| Frontend | http://192.168.0.195:15173 | Vue SPA (nginx) |
| Backend API | http://192.168.0.195:18089/api/ | Django REST |
| Backend Admin | http://192.168.0.195:18089/admin/ | Django Admin |
| MySQL | 192.168.0.195:3307 | Base de datos |

## Prerrequisitos

- Docker >= 20.10
- Docker Compose >= 2.0
- Copiar la carpeta `docker/` al servidor

```bash
# En el servidor (192.168.0.195)
sudo apt update && sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
# Cerrar y abrir sesion para aplicar grupo docker
```

## Levantar

```bash
cd /var/www/html/reventa/docker

# Construir y levantar
sudo docker compose up -d --build

# Verificar que todos esten corriendo
sudo docker compose ps
```

## Primera vez - Inicializar base de datos

```bash
# Crear tablas
sudo docker compose exec backend python manage.py migrate

# Crear superusuario
sudo docker compose exec backend python manage.py createsuperuser

# Cargar datos iniciales (si existe el comando)
sudo docker compose exec backend python manage.py loaddata initial_data
```

## Acceder

Abrir en el navegador: **http://192.168.0.195:15173**

- El frontend conecta la API automaticamente via nginx proxy
- Login con el superusuario creado arriba
- Django Admin: http://192.168.0.195:18089/admin/

## Ver Logs

```bash
# Todos los servicios
sudo docker compose logs -f

# Solo backend
sudo docker compose logs -f backend

# Solo frontend
sudo docker compose logs -f frontend

# Solo MySQL
sudo docker compose logs -f mysql
```

## Parar

```bash
sudo docker compose down
```

## Parar y borrar datos

```bash
sudo docker compose down -v
```

## Reconstruir desde cero

```bash
sudo docker compose down -v
sudo docker compose up -d --build
sudo docker compose exec backend python manage.py migrate
sudo docker compose exec backend python manage.py createsuperuser
``>

## Archivos

```
docker/
  Dockerfile.backend      # Python 3.11 + gunicorn
  Dockerfile.frontend     # Node 20 build + nginx:alpine
  docker-compose.yml      # Orquestacion de servicios
  .env.docker             # Variables de entorno para Docker
  nginx/
    default.conf          # Config nginx (SPA + proxy API)
```

## Notas

- La base de datos Docker es **aislada** (no afecta produccion)
- El email esta deshabilitado (consola) en este entorno
- Los puertos no conflictuan con produccion (80/443, 8088, 3306)
- Los archivos media se guardan en un volumen Docker persistente
