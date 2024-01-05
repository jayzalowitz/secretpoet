# /payments/models
from django.db import models
from django import forms
from wagtail.admin.panels import FieldPanel
from django.conf import settings

class UserAccount(models.Model):
    # Link to the Django user model
    user = models.OneToOneField(settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='account')

    # Store the MobileCoin account keys as a text field
    account_key_id = models.TextField(null=True, blank=True)
    account_name = models.TextField(null=True, blank=True)
    account_main_address = models.TextField(null=True, blank=True)
    # The first block index to consider when syncing transactions
    next_block_to_sync = models.IntegerField(default=0)
    last_mobilecoin_balance_observed = models.IntegerField(default=0)
    recovery_mnemonic = models.TextField(null=True, blank=True)
    

    panels = [
        FieldPanel('user'),
        FieldPanel('next_block_to_sync'),
        FieldPanel('account_key_id', widget=forms.TextInput(attrs={'readonly': 'readonly'})),
        FieldPanel('account_name', widget=forms.TextInput(attrs={'readonly': 'readonly'})),
        FieldPanel('account_main_address', widget=forms.TextInput(attrs={'readonly': 'readonly'})),
        FieldPanel('last_mobilecoin_balance_observed', widget=forms.NumberInput(attrs={'readonly': 'readonly'})),
        FieldPanel('recovery_mnemonic', widget=forms.TextInput(attrs={'readonly': 'readonly'})),
        # Add other fields and panels as needed
    ]
    '''
            {'account_id': 'ad4ca8084dacb31bf3bcae220634432149a0660db99784862daa73db330cb726',
             'name': "wagtail's key",
             'entropy': None,
             'mnemonic': 'armor remove evil pizza brother purity strategy pink core tenant seek appear mixed badge laundry exhaust include truth nature exhaust debate box remain camp',
             'key_derivation_version': '2',
             'account_key': {'view_private_key': '0a20f6992b6118608a86e9d885cfce5c5be1b892f746eb4d788cbeceae144a17dd09',
              'spend_private_key': '0a2033f646cb46d6603bec3ac87ccc50dccfb1a120904dc2e643f017f03780b18102',
              'fog_report_url': '',
              'fog_report_id': '',
              'fog_authority_spki': ''},
             'view_account_key': None}
             '''

    class Meta:
        verbose_name = "MobileCoin/Eusd Account"
        verbose_name_plural = "MobileCoin/Eusd Accounts"

    def __str__(self):
        return f"MobileCoin/Eusd Account for {self.user.username}"

