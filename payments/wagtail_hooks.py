# payments/wagtail_hooks.py
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from .models import UserAccount
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAccountAdmin(ModelAdmin):
    model = UserAccount
    menu_label = 'User Crypto Accounts'  # Menu label in Wagtail admin
    menu_icon = 'user'  # Wagtail admin icon
    add_to_settings_menu = False  # Whether to add to the settings menu
    exclude_from_explorer = False # Whether to exclude from the explorer navigation menu
    list_display = ('user',   
        'next_block_to_sync')
    readonly_fields = ('account_key_id',
        'account_name',
        'account_main_address',
        'recovery_mnemonic')
    
    # Custom permissions for view, edit, and delete
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def user_can_edit_obj(self, user, obj):
        return user.is_superuser or user == obj.user

    '''
    def get_edit_view_extra_css_urls(self, view, request, view_args, view_kwargs):
        return ['/path/to/my/custom.css']  # If you need extra CSS

    def get_edit_view_extra_js_urls(self, view, request, view_args, view_kwargs):
        return ['/path/to/my/custom.js']  # If you need extra JS

    '''
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        # Make certain fields read-only for non-superusers viewing their own account
        if not request.user.is_superuser and obj is not None and obj.user == request.user:
            return readonly_fields + ('account_keys',)  # Add more fields as needed
        return readonly_fields

# Register your modeladmin class with Wagtail
modeladmin_register(UserAccountAdmin)
