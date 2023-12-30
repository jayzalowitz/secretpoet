# secretpoet/payments/signals.py
import asyncio
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from payments.models import UserAccount
from secretpoet.payments.utils import Payment
from asgiref.sync import sync_to_async  # Import sync_to_async

def create_user_account_and_payment_sync(user):
    """
    This function creates a new thread and runs the async function
    `create_user_account_and_payment` in an event loop in that thread.
    """
    async def async_create_user_account_and_payment():
        payment = Payment()
        await payment.check_for_account_and_create_if_not_exists(user)

    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_create_user_account_and_payment())
        loop.close()

    thread = threading.Thread(target=run_in_thread)
    thread.start()

@receiver(post_save, sender=User)
def ensure_user_account_and_payment(sender, instance, **kwargs):
    # Call the synchronous wrapper function
    create_user_account_and_payment_sync(instance)

'''
@receiver(post_save, sender=User)
@sync_to_async  # Use sync_to_async decorator
async def ensure_user_account_and_payment(sender, instance, **kwargs):
    # Use sync_to_async for the synchronous database query
    user_account, created = await sync_to_async(UserAccount.objects.get_or_create)(user=instance)
    
    if created or not user_account or not user_account.account_key_id:
        payment = Payment()  # Instantiate Payment
        await payment.run_check_for_account_and_create_if_not_exists(user=instance)
'''