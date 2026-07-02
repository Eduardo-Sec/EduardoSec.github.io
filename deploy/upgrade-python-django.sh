#!/bin/bash
# ONE-TIME migration: Python 3.9 -> 3.11, Django 4.2 LTS -> 5.2 LTS.
#
# Why: Django 4.2 reached end of extended support on 2026-04-07 and no
# longer receives security patches. This installs Python 3.11 alongside
# the existing system python3 (does not replace it -- nothing else on
# the OS depends on 3.11), rebuilds the app's venv against it, and
# deploys the already-merged requirements.txt bump to django==5.2.*.
#
# Run this ONCE, as root, after merging the upgrade PR:
#   sudo bash /opt/ebustamante/deploy/upgrade-python-django.sh
#
# After this completes successfully, go back to the normal deploy flow
# (deploy/update.sh) for everything else -- this script only exists to
# get through the one-time venv rebuild that update.sh can't do itself
# (its pip install step uses the OLD venv's Python 3.9, which can't
# satisfy Django 5.2's >=3.10 requirement).
set -euo pipefail

APP_DIR="/opt/ebustamante"
APP_USER="ebustamante"
BACKUP_DIR="/opt/ebustamante-venv-backup-$(date +%Y%m%d-%H%M%S)"

echo "==> Step 1: Installing Python 3.11 (alongside system python3, not replacing it)"
dnf install -y python3.11

echo "==> Step 2: Verifying installation"
python3.11 --version

echo "==> Step 3: Pulling latest code (must already have the django==5.2.* PR merged)"
cd "$APP_DIR"
git config --global --add safe.directory "$APP_DIR" 2>/dev/null || true
git pull
grep -q "django==5.2" requirements.txt || {
  echo "ERROR: requirements.txt doesn't show django==5.2.* -- did you merge the upgrade PR first?"
  exit 1
}

echo "==> Step 4: Backing up old venv (rollback instructions printed at the end)"
mv "$APP_DIR/.venv" "$BACKUP_DIR"

echo "==> Step 5: Creating new venv with Python 3.11"
python3.11 -m venv "$APP_DIR/.venv"

echo "==> Step 6: Installing dependencies into the new venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip --quiet
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" --quiet

echo "==> Step 7: Running migrations"
.venv/bin/python manage.py migrate --noinput

echo "==> Step 8: Collecting static files"
.venv/bin/python manage.py collectstatic --noinput

echo "==> Step 9: Importing writeups"
.venv/bin/python manage.py import_writeups

echo "==> Step 10: Fixing ownership on the new venv"
chown -R "$APP_USER:$APP_USER" "$APP_DIR/.venv"

echo "==> Step 11: Restarting gunicorn"
systemctl restart ebustamante

echo "==> Step 12: Verifying the service came up healthy"
sleep 2
systemctl is-active --quiet ebustamante && echo "gunicorn is active" || {
  echo "ERROR: gunicorn failed to start. Check: journalctl -u ebustamante -n 50"
  echo "Rollback instructions are below -- old venv is untouched at $BACKUP_DIR"
  exit 1
}
curl -sf http://127.0.0.1/ > /dev/null && echo "Smoke test passed: homepage returned 200" || echo "WARNING: smoke test failed, check http://127.0.0.1/ manually and journalctl -u ebustamante"

DJANGO_VERSION=$("$APP_DIR/.venv/bin/python" -c "import django; print(django.get_version())")
echo ""
echo "==> Done. Django $DJANGO_VERSION running on Python 3.11."
echo "    Old venv backed up at: $BACKUP_DIR"
echo ""
echo "    If something is wrong and you need to roll back:"
echo "      sudo systemctl stop ebustamante"
echo "      sudo rm -rf $APP_DIR/.venv"
echo "      sudo mv $BACKUP_DIR $APP_DIR/.venv"
echo "      cd $APP_DIR && sudo git log --oneline -5   # find the commit before the upgrade merge"
echo "      sudo git checkout <that-commit-hash>"
echo "      sudo systemctl start ebustamante"
echo ""
echo "    Once you've confirmed everything is stable for a few days, remove the backup:"
echo "      sudo rm -rf $BACKUP_DIR"
