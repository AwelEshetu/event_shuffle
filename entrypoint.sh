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
    # Run migrations only (don't generate them)
    uv run python manage.py migrate

    # Create Django admin user if credentials are provided
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
        uv run python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', 'admin@example.com', '$DJANGO_SUPERUSER_PASSWORD')
EOF
    fi

    # Start the server
    uv run python manage.py runserver 0.0.0.0:8000
fi
