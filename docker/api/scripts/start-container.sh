#!/usr/bin/env bash
set -euo pipefail

# Execute pending migrations
echo Executing pending migrations
# python3 manage.py compilemessages
# python3 manage.py collectstatic --no-input
python3 -m pip install -r requirements.txt
python3 manage.py makemigrations
python3 manage.py migrate

# Load default templates
echo Load default templates
python3 manage.py loaddata initial_user
python3 manage.py loaddata initial_brokers
python3 manage.py loaddata initial_theme
python3 manage.py loaddata initial_account_templates

# if [ "$APP_ENV" == "production" ]; then
#     exec gunicorn realjournals.wsgi:application \
#         --name realjournals \
#         --bind 0.0.0.0:8000 \
#         --workers 3 \
#         --worker-tmp-dir /dev/shm \
#         --log-level=debug \
#         --access-logfile - \
#         "$@"
# else
#     python3 manage.py runserver 0.0.0.0:8000
# fi

if [ "$APP_SCHEDULE" == "true" ]; then
	crontab /var/cron.schedule
	service cron restart
fi

if [ $# -gt 0 ]; then
	exec "$@"
else
    exec supervisord --nodaemon \
        --configuration=/var/supervisord.conf \
        --logfile=/var/www/html/log/supervisord/supervisord.log \
        --logfile_maxbytes=5MB
fi

