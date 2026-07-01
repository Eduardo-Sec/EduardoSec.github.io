#!/bin/bash
# One-time setup for Rocky Linux 9.
# Run as root: bash /tmp/setup.sh
set -euo pipefail

APP_DIR="/opt/ebustamante"
APP_USER="ebustamante"
REPO_URL="https://github.com/Eduardo-Sec/EduardoSec.github.io.git"
LOG_DIR="/var/log/ebustamante"

echo "==> Installing system packages"
dnf install -y python3 python3-pip python3-devel nginx git

echo "==> Creating app user"
useradd -r -s /sbin/nologin -d "$APP_DIR" "$APP_USER" 2>/dev/null || echo "User already exists"

echo "==> Cloning repo"
git clone "$REPO_URL" "$APP_DIR"
# Ensure we're on the right branch — merge your work to master before deploying
git -C "$APP_DIR" checkout master

echo "==> Creating virtual environment"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip --quiet
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" --quiet

echo "==> Creating .env file"
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
cat > "$APP_DIR/.env" << EOF
DJANGO_SECRET_KEY=$SECRET_KEY
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=ebustamante.dev 127.0.0.1 localhost
SITE_URL=https://ebustamante.dev
EOF
chmod 640 "$APP_DIR/.env"

echo "==> Running migrations and importing writeups"
cd "$APP_DIR"
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py import_writeups
.venv/bin/python manage.py collectstatic --noinput

echo "==> Creating superuser (interactive)"
.venv/bin/python manage.py createsuperuser

echo "==> Setting permissions"
mkdir -p "$LOG_DIR"
chown -R "$APP_USER:$APP_USER" "$APP_DIR" "$LOG_DIR"
chmod 750 "$APP_DIR"
chmod 640 "$APP_DIR/.env"

echo "==> Installing systemd service"
cp "$APP_DIR/deploy/ebustamante.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now ebustamante
systemctl status ebustamante --no-pager

echo "==> Configuring Nginx"
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/conf.d/ebustamante.conf
# Remove default server block if present
rm -f /etc/nginx/conf.d/default.conf
nginx -t
systemctl enable --now nginx

echo "==> SELinux: allow nginx to proxy to gunicorn"
setsebool -P httpd_can_network_connect 1
# Allow nginx to read static files under /opt
chcon -Rt httpd_sys_content_t "$APP_DIR/staticfiles"

echo "==> Firewall: nginx listens only on localhost (Cloudflare tunnel handles external)"
# Do NOT open port 80/443 publicly — tunnel handles that
# Only allow the tunnel loopback traffic (already allowed by default for loopback)
echo "    Cloudflare tunnel will connect to http://127.0.0.1:80"

echo ""
echo "==> Setup complete."
echo "    Next: configure and start the Cloudflare tunnel (see deploy/cloudflared.yml)"
echo "    Then verify: curl -s http://127.0.0.1/  should return the homepage"
