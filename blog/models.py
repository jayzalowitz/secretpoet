from django.db import models
from wagtail.models import Page  # Updated import
from wagtail.admin.panels import FieldPanel
from django.conf import settings


class BlogIndexPage(Page):
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context['posts'] = BlogPost.objects.live().order_by('-first_published_at')
        return context

class BlogPost(Page):
    body = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    payment_required = models.BooleanField(default=True)
    unlock_fee = models.DecimalField(max_digits=13, decimal_places=10, default=1.0)
    coin_choice = (
        ('mobilecoin','mobilecoin'),
        ('eusd', 'eusd (inactive)'),
    )
    coin_option = models.CharField(max_length=10, choices=coin_choice, default='mobilecoin')
    content_panels = Page.content_panels + [
        FieldPanel('body'),
        FieldPanel('author'),
        FieldPanel('payment_required'),
        FieldPanel('unlock_fee'),
        FieldPanel('coin_option')
    ]

    def is_unlocked_for_user(self, request):
        unlock_key = request.GET.get('unlock_key', '')
        if not unlock_key:
        	return False
        else:
        	mobilecoin.get_key()
	        # Implement a secure method to validate the unlock_key
	        return unlock_key == "expected_key"  # Replace with your logic