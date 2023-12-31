from django.shortcuts import render, get_object_or_404, redirect
from .models import BlogPost
from wagtail.models import Page
from secretpoet.payments.utils import Payment 
from asgiref.sync import sync_to_async

import logging
import json
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


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
        
    if not unlock_key:   
        context = {
            'page': post,
            'is_unlocked_for_user': is_unlocked
        }
    else:
        logging.error(is_unlocked)
         
        context = {
            'page': post,
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
