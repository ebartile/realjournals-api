#!/usr/bin/env bash
set -euo pipefail

# Execute pending migrations
echo Executing pending migrations
# python manage.py compilemessages
# python manage.py collectstatic --no-input
python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate

# Load default templates
echo Load default templates
python manage.py loaddata initial_user
python manage.py loaddata initial_brokers
python manage.py loaddata initial_roles
python manage.py loaddata initial_theme
python manage.py loaddata initial_modules

# Start Real Journals processes
echo Starting Real Journals API...
if [ "$APP_ENV" == "production" ]; then
    exec gunicorn realjournals.wsgi:application \
        --name realjournals \
        --bind 0.0.0.0:8080 \
        --workers 3 \
        --worker-tmp-dir /dev/shm \
        --log-level=debug \
        --access-logfile - \
        "$@"
else
    exec python manage.py runserver 0.0.0.0:8080
fi

if [ "$APP_SCHEDULE" == "true" ]; then
	crontab /var/cron.schedule
	service cron restart
fi

if [ $# -gt 0 ]; then
	exec "$@"
else
	exec /usr/bin/supervisord --nodaemon \
		--configuration=/var/supervisord.conf \
		--logfile=/var/log/supervisord/supervisord.log \
		--logfile_maxbytes=5MB
fi

