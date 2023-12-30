# secretpoet/payment/admin.py

from django.contrib import admin
from blog.models import BlogPost
from .models import UserAccount

# @admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_key_id', 'next_block_to_sync')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        # Make certain fields read-only for non-superusers viewing their own account
        if not request.user.is_superuser and obj is not None and obj.user == request.user:
            return readonly_fields + ('account_keys',)  # Add more fields as needed
        return readonly_fields

    def has_change_permission(self, request, obj=None):
        # Check if user has permission to change the object
        has_permission = super().has_change_permission(request, obj)
        if not request.user.is_superuser and obj is not None:
            return obj.user == request.user and has_permission
        return has_permission

admin.site.register(UserAccount, 
    UserAccountAdmin)
admin.site.register(BlogPost)

