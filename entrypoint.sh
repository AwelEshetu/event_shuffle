#!/bin/sh
set -e

if [ "$#" -gt 0 ]; then
    # Allow shell access for troubleshooting
    case "$1" in
        sh|bash)
            exec "$1"
            ;;
        *)
            exec "$@"
            ;;
    esac
else
    # Run migrations
    uv run python manage.py makemigrations
    uv run python manage.py migrate

    # Create Django admin user if not exists
    uv run python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
EOF

    # Start the server
    uv run python manage.py runserver 0.0.0.0:8000
fi
