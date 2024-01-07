from django.urls import path
from .views import blog_post_view, unlock_blog_post, blog_post_check_view

urlpatterns = [
    path('post/<int:post_id>/', blog_post_view, name='blog_post'),
    path('unlock-post/<int:post_id>/', unlock_blog_post, name='unlock_blog_post'),
    path('check-post/<int:post_id>/', blog_post_check_view, name='blog_post_check'),
]
