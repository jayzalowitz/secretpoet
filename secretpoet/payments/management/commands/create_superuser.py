import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a superuser if one does not exist'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'defaultusername')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'defaultemail@example.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'defaultpassword')
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS('Successfully created superuser'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists'))
