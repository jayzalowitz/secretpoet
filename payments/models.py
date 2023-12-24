from django.db import models
from django.conf import settings

class MobileCoinAccount(models.Model):
    # Link to the Django user model
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Store the MobileCoin account keys as a text field
    account_keys = models.TextField()

    # The first block index to consider when syncing transactions
    next_block_to_sync = models.IntegerField()

    class Meta:
        verbose_name = "MobileCoin Account"
        verbose_name_plural = "MobileCoin Accounts"

    def __str__(self):
        return f"MobileCoin Account for {self.user.username}"