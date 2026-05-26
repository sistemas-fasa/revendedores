#!/bin/bash

# ===================================
# SCRIPT DE INSTALACIÓN COMPLETA
# Ferreteria Avenida - Vue + Django + Docker
# Código en /var/www/html/reventa
# Subdominio: ventas.ferreteriaavenida.com.ar
# ===================================

set -e

echo "🚀 Iniciando instalación completa..."
echo "📌 Asegúrate de que el DNS 'ventas.ferreteriaavenida.com.ar' apunta a tu IP pública"

# Variables
PROJECT_DIR="/var/www/mi-app"
CODE_DIR="/var/www/html/reventa"
DOMAIN="ventas.ferreteriaavenida.com.ar"

# Validar que exista la carpeta de código
if [ ! -d "$CODE_DIR" ]; then
  echo "❌ Error: No se encontró la carpeta de código en $CODE_DIR"
  echo "Crea la carpeta o copia tu código allí antes de continuar."
  exit 1
fi

if [ ! -d "$CODE_DIR/backend" ] || [ ! -d "$CODE_DIR/frontend" ]; then
  echo "❌ Error: Deben existir las carpetas $CODE_DIR/backend y $CODE_DIR/frontend"
  exit 1
fi

# -----------------------------------
# 1. Actualizar sistema
# -----------------------------------
echo "🔧 Actualizando sistema..."
#sudo apt update
#sudo apt upgrade -y

# -----------------------------------
# 2. Instalar Docker (versión oficial, compatible con noble)
# -----------------------------------
echo "🐳 Instalando Docker desde repositorio oficial..."

# Eliminar versiones anteriores
sudo apt remove -y docker.io containerd runc || true

# Dependencias
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Clave GPG
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Repositorio (usamos jammy para compatibilidad)
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  jammy stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verificar
sudo docker --version
# -----------------------------------
# 3. Instalar Docker Compose
# -----------------------------------
echo "📦 Instalando Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# -----------------------------------
# 4. Crear estructura de Docker
# -----------------------------------
echo "📁 Creando estructura de Docker en $PROJECT_DIR..."
sudo mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

sudo mkdir -p backend frontend nginx scripts backups

# -----------------------------------
# 5. backend/Dockerfile (solo dependencias)
# -----------------------------------
cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi:application"]
EOF

# -----------------------------------
# 6. frontend/Dockerfile (sin copiar código)
# -----------------------------------
cat > frontend/Dockerfile << 'EOF'
FROM node:18 AS builder
# El código se monta en runtime

FROM nginx:alpine
# El build se hace en docker-compose
EOF

# -----------------------------------
# 7. nginx/nginx.conf
# -----------------------------------
cat > nginx/nginx.conf << 'EOF'
server {
    listen 80;
    server_name ventas.ferreteriaavenida.com.ar;

    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name ventas.ferreteriaavenida.com.ar;

    ssl_certificate /etc/nginx/ssl/live/ventas.ferreteriaavenida.com.ar/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/ventas.ferreteriaavenida.com.ar/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Port 443;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        proxy_pass http://backend:8000;
    }

    location /media/ {
        proxy_pass http://backend:8000;
    }
}
EOF

# -----------------------------------
# 8. .env
# -----------------------------------
cat > .env << 'EOF'
MYSQL_DATABASE=reventa
MYSQL_USER=reventa
MYSQL_PASSWORD=fGil6RuWE1Cf
MYSQL_ROOT_PASSWORD=LlcORpBRU7xc
DJANGO_SECRET_KEY=#ucrgqj%5#%z16&e5ayv$y@4qsvxilne++kr$(bu_ch&#ca
DEBUG=False
ALLOWED_HOSTS=ventas.ferreteriaavenida.com.ar,backend,localhost
EOF

# -----------------------------------
# 9. docker-compose.yml
# -----------------------------------
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  db:
    image: mysql:8.0
    container_name: mysql-db
    environment:
      MYSQL_DATABASE: ${MYSQL_DATABASE}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    command: --default-authentication-plugin=mysql_native_password
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p$$MYSQL_ROOT_PASSWORD"]
      interval: 10s
      timeout: 5s
      retries: 10
    restart: unless-stopped

  backend:
    build: ./backend
    container_name: django-backend
    volumes:
      - /var/www/html/reventa/backend:/app
    expose:
      - "8000"
    environment:
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - DEBUG=${DEBUG}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: vue-frontend
    volumes:
      - /var/www/html/reventa/frontend:/app
    command: >
      sh -c "cd /app && npm install && npm run build && cp -r dist/* /usr/share/nginx/html/ && nginx -g 'daemon off;'"
    expose:
      - "80"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: reverse-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  mysql_data:
  nginx_ssl:
EOF

# -----------------------------------
# 10. deploy.sh
# -----------------------------------
cat > deploy.sh << 'EOF'
#!/bin/bash

echo "🚀 Iniciando despliegue desde /var/www/html/reventa"

cd /var/www/mi-app || { echo "❌ No se encontró el directorio"; exit 1; }

# Detener servicios
echo "⏹️ Deteniendo servicios..."
sudo docker-compose down

# Reconstruir frontend (asegura que se haga build con nuevos cambios)
echo "🔨 Reconstruyendo frontend..."
sudo docker-compose build frontend

# Levantar servicios
echo "🚀 Levantando servicios..."
sudo docker-compose up -d

# Aplicar migraciones
echo "🔄 Aplicando migraciones..."
sudo docker-compose exec -T backend python manage.py migrate --noinput

# Backup inicial
echo "📦 Creando backup inicial..."
BACKUP_DIR="/var/www/mi-app/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%F_%H-%M)
sudo docker-compose exec -T db mysqldump -u admin -p"ferre2025secure" ferreteria > "$BACKUP_DIR/db-$DATE.sql"
echo "✅ Backup guardado: $BACKUP_DIR/db-$DATE.sql"

echo "✅ Despliegue completado: https://ventas.ferreteriaavenida.com.ar"
EOF

chmod +x deploy.sh

# -----------------------------------
# 11. Script de backup diario
# -----------------------------------
cat > scripts/backup-db.sh << 'EOF'
#!/bin/bash
cd /var/www/mi-app || exit 1
DATE=$(date +%F)
docker-compose exec -T db mysqldump -u admin -p"ferre2025secure" ferreteria > backups/db-$DATE.sql
find backups -name "db-*.sql" -mtime +7 -delete
EOF

chmod +x scripts/backup-db.sh

# Agregar al cron
(crontab -l 2>/dev/null; echo "0 2 * * * /var/www/mi-app/scripts/backup-db.sh >> /var/www/mi-app/backups/backup.log 2>&1") | crontab -

# -----------------------------------
# 12. Finalizar
# -----------------------------------
echo "
✅ Instalación completada.

📌 Próximos pasos:

1. Asegúrate de que el DNS:
   ventas.ferreteriaavenida.com.ar → TU_IP_PUBLICA

2. Genera el certificado SSL (una vez que el DNS esté listo):
   sudo docker-compose -f $PROJECT_DIR/docker-compose.yml down nginx
   sudo certbot certonly --standalone -d ventas.ferreteriaavenida.com.ar
   sudo mkdir -p $PROJECT_DIR/nginx/ssl
   sudo cp -r /etc/letsencrypt/live/ventas.ferreteriaavenida.com.ar $PROJECT_DIR/nginx/ssl/live/
   $PROJECT_DIR/deploy.sh

3. Para actualizar tu app en el futuro:
   $PROJECT_DIR/deploy.sh

🔐 Acceso a base de datos (HeidiSQL):
   - Host: TU_IP_PUBLICA
   - Puerto: 3306
   - Usuario: admin
   - Contraseña: ferre2025secure
   - Base de datos: ferreteria
   (Asegúrate de abrir el puerto 3306 solo para tu IP)

🚀 Tu app se servirá desde: https://ventas.ferreteriaavenida.com.ar
"