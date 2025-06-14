#!/bin/bash

echo "Waiting for postgres..."
while ! nc -z db 5432; do
  sleep 1
done
python manage.py migrate
python manage.py collectstatic --no-input
python manage.py load_ingredients /app/data/ingredients.json || echo "Failed to load ingredients"
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')"
python manage.py create_test_data

exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000