from django.shortcuts import render, get_object_or_404, redirect
from .models import BlogPost

def blog_post_view(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    is_unlocked = post.is_unlocked_for_user(request)
    context = {
        'page': post,
        'is_unlocked_for_user': is_unlocked
    }
    return render(request, 'blog/blog_post_page.html', context)

def unlock_blog_post(request, post_id):
    # Redirect to the blog post with an unlock_key in the query string
    # Replace 'your_unlock_key' with actual logic to generate a key
    return redirect(f'/blog/post/{post_id}/?unlock_key=your_unlock_key')
