# /blog/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import BlogPost
from wagtail.models import Page
from secretpoet.payments.utils import Payment 
from asgiref.sync import sync_to_async
from django.core.paginator import Paginator
from django.http import Http404
import logging
import json
from django.http import JsonResponse

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def health_check(request):
    import os
    from django.db import connections, OperationalError
    from django.contrib.auth import get_user_model
    # Environment variable checks
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    if not all([username, email, password]):
        return JsonResponse({"environment": "missing variables"}, status=503)

    # Function to check and create superuser
    def check_and_create_superuser():
        User = get_user_model()
        user_exists = User.objects.filter(username=username).exists() or \
                      User.objects.filter(email=email).exists()

        if user_exists:
            return "existing user"
        else:
            # Create superuser
            User.objects.create_superuser(username=username, email=email, password=password)
            return "superuser created"

    # Database connectivity check
    def check_database_connection():
        db_conn = connections['default']
        try:
            db_conn.cursor()
        except OperationalError:
            return False
        return True

    user_status = check_and_create_superuser()
    db_connected = check_database_connection()

    if not db_connected:
        return JsonResponse({"database": "unavailable"}, status=503)

    return JsonResponse({
        "status": "healthy",
        "user_check": user_status,
        "environment": "variables present"
    }, status=200)

async def blog_index_view(request):
    # Get all blog posts, you might want to order them as well
    blog_posts = await sync_to_async(list)(BlogPost.objects.live().order_by('-last_published_at'))

    # Implement pagination
    paginator = Paginator(blog_posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = await sync_to_async(paginator.get_page)(page_number)

    # If page does not exist, show 404 error
    if not page_obj:
        context = {
            'page_obj': None,
        }
    else:  
        # Pass the page object to the template
        context = {
            'page_obj': page_obj,
        }

    # Render the blog index page
    return await sync_to_async(render)(request, 'blog/blog_index_page.html', context)


async def blog_post_check_view(request, post_id=None, post_slug=None):
    if post_id:
        post = await sync_to_async(get_object_or_404)(BlogPost, pk=post_id)
    elif post_slug:
        post = await sync_to_async(get_object_or_404)(BlogPost, slug=post_slug)
        # Handle the case where neither is provided
        # Redirect to a default page or show an error
    else:
        # Handle the case where neither is provided
        return render(request, 'errors/404.html', {}, status=404)

    unlock_key = request.GET.get('unlock_key', '')
    if not unlock_key:
        is_unlocked = False
    else:
        payment = Payment()
        is_unlocked = await payment.is_unlocked_for_user(unlock_key,post)
        logging.error(is_unlocked)
        
    return JsonResponse({
        "is_unlocked": is_unlocked
    }, status=200)

async def blog_post_view(request, post_id=None, post_slug=None):
    if post_id:
        post = await sync_to_async(get_object_or_404)(BlogPost, pk=post_id)
    elif post_slug:
        post = await sync_to_async(get_object_or_404)(BlogPost, slug=post_slug)
        # Handle the case where neither is provided
        # Redirect to a default page or show an error
    else:
        # Handle the case where neither is provided
        return render(request, 'errors/404.html', {}, status=404)

    unlock_key = request.GET.get('unlock_key', '')
    if not unlock_key:
        is_unlocked = False
    else:
        payment = Payment()
        is_unlocked = await payment.is_unlocked_for_user(unlock_key,post)
        logging.error(is_unlocked)
        
    if not unlock_key:  
        context = {
            'page': post,
            'payment_required': post.payment_required,
            'is_unlocked_for_user': is_unlocked
        }
        logging.error(context)
    else:
        logging.error(is_unlocked)
         
        context = {
            'page': post,
            'payment_required': post.payment_required,
            'is_unlocked_for_user': is_unlocked,
            'unlock_key': unlock_key
        }
    response = await sync_to_async(render)(request, 'blog/blog_post_page.html', context)
    return response


async def unlock_blog_post(request, post_id=None, post_slug=None):
    # Redirect to the blog post with an unlock_key in the query string
    # Replace 'your_unlock_key' with actual logic to generate a key
    if post_id:
        post = await sync_to_async(get_object_or_404)(BlogPost, pk=post_id)
        payment = Payment()
        unlock_key = await payment.check_for_owner_of_post_and_grab_a_public_address(post)
        # get post owners key for system
        return redirect(f'/blog/post/{post_id}/?unlock_key={unlock_key}')
    elif post_slug:
        post = await sync_to_async(get_object_or_404)(BlogPost, slug=post_slug)
        payment = Payment()
        unlock_key = await payment.check_for_owner_of_post_and_grab_a_public_address(post)
        
        # get post owners key for system
        return redirect(f'/blog/post/{post_slug}/?unlock_key={unlock_key}')
