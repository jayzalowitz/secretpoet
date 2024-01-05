#!/bin/sh
python manage.py makemigrations home
python manage.py makemigrations blog
python manage.py makemigrations payments
python manage.py migrate
#docker-compose run web python manage.py createsuperuser_with_password --username $DJANGO_SUPERUSER_USERNAME --email $DJANGO_SUPERUSER_EMAIL --password $DJANGO_SUPERUSER_PASSWORD
#docker-compose run web python manage.py createsuperuser
#python manage.py runserver 0.0.0.0:8000
