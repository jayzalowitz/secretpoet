docker-compose run web python manage.py makemigrations home
docker-compose run web python manage.py makemigrations blog
docker-compose run web python manage.py migrate
#docker-compose run web python manage.py createsuperuser_with_password --username $DJANGO_SUPERUSER_USERNAME --email $DJANGO_SUPERUSER_EMAIL --password $DJANGO_SUPERUSER_PASSWORD
docker-compose run web python manage.py createsuperuser
docker-compose up --build
