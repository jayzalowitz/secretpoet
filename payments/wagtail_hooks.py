# payments/wagtail_hooks.py
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from .models import UserAccount
from django.contrib.auth import get_user_model

import logging
import json
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

User = get_user_model()

class UserAccountAdmin(ModelAdmin):
    model = UserAccount
    menu_label = 'User Crypto Accounts'  # Menu label in Wagtail admin
    menu_icon = 'user'  # Wagtail admin icon
    add_to_settings_menu = False  # Whether to add to the settings menu
    exclude_from_explorer = False # Whether to exclude from the explorer navigation menu
    list_display = ('user',   
        'next_block_to_sync')
    '''
    readonly_fields = ('account_key_id',
        'account_name',
        'account_main_address',
        'recovery_mnemonic')
    '''
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
        logging.error("running readonly: recovery_mnemonic")
            
        readonly_fields = super().get_readonly_fields(request, obj)
        # Make 'recovery_mnemonic' read-only for the user who owns the account or for superusers
        if obj is not None and (request.user.is_superuser or request.user == obj.user):
            readonly_fields + ('recovery_mnemonic',)
        return readonly_fields + ('recovery_mnemonic',)

# Register your modeladmin class with Wagtail
modeladmin_register(UserAccountAdmin)
