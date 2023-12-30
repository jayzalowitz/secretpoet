import asyncio
from asgiref.sync import sync_to_async
from mobilecoin.client import ClientAsync
from payments.models import UserAccount

class ClientSync:
    def __init__(self, url=None):
        self.url = url
        self.client = None

    async def _init_client(self):
        if not self.client:
            self.client = ClientAsync(url=self.url or "http://full_service:9090/wallet/v2")

    async def _run_async(self, method_name, *args, **kwargs):
        await self._init_client()
        method = getattr(self.client, method_name)
        return await method(*args, **kwargs)

    def __getattr__(self, method_name):
        def wrapper(*args, **kwargs):
            # Ensure that asyncio.run is used in a thread-safe manner
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we are already in an async loop, just await the coroutine
                return asyncio.ensure_future(self._run_async(method_name, *args, **kwargs))
            else:
                return asyncio.run(self._run_async(method_name, *args, **kwargs))
        return wrapper


class Payment:
    def __init__(self, url=None):
        self.url = url
        self.client = ClientAsync(url=self.url or "http://full_service:9090/wallet/v2")

    async def check_for_account_and_create_if_not_exists(self, user):
        user_account_queryset = await sync_to_async(UserAccount.objects.filter)(user=user)
        user_account = await sync_to_async(user_account_queryset.first)()
        if not user_account or not user_account.account_key_id:
            pretty_name = user.username + "'s key"
            crypto_account = await self.client.create_account(name=pretty_name)
            secrets = await self.client.export_account_secrets(account_id=crypto_account["id"])
            public_address = await self.client.assign_address_for_account(account_id=crypto_account["id"])

            if not user_account:
                user_account = UserAccount(user=user)

            user_account.account_key_id = crypto_account["id"]
            user_account.account_name = crypto_account["name"]
            user_account.account_main_address = public_address['public_address_b58']
            user_account.next_block_to_sync = crypto_account["next_block_index"]
            user_account.last_mobilecoin_balance_observed = 0  # Set initial balance, update as needed
            user_account.recovery_mnemonic = secrets["mnemonic"]
            await sync_to_async(user_account.save)()

            return user_account, crypto_account
