#!/bin/bash
# Deployment update script — run after every git push.
# Usage: ssh user@REDACTED 'bash /opt/ebustamante/deploy/update.sh'
set -euo pipefail

APP_DIR="/opt/ebustamante"
cd "$APP_DIR"

echo "==> Pulling latest code"
git pull

echo "==> Installing any new dependencies"
.venv/bin/pip install -r requirements.txt --quiet

echo "==> Running migrations"
.venv/bin/python manage.py migrate --noinput

echo "==> Collecting static files"
.venv/bin/python manage.py collectstatic --noinput

echo "==> Importing new writeups"
.venv/bin/python manage.py import_writeups

echo "==> Restarting gunicorn"
systemctl restart ebustamante

echo "==> Done. Site is live."
