# secretpoet/payment/admin.py

from django.contrib import admin
from blog.models import BlogPost
from .models import MobileCoinAccount

admin.site.register(BlogPost)
admin.site.register(MobileCoinAccount)