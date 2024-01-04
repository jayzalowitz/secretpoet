import asyncio
from asgiref.sync import sync_to_async
from mobilecoin.client import ClientAsync
from payments.models import UserAccount
import logging
import json
import os
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class ClientSync:
    def __init__(self, url=None):
        self.url = url
        self.client = None

    async def _init_client(self):
        if not self.client:
            self.client = ClientAsync(url=self.url or os.getenv('FULL_SERVICE_URL', "http://full_service:9090/wallet/v2"))

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

    async def is_unlocked_for_user(self, unlock_key,post):
        mob_info = False
        if not unlock_key:
            return False
        else:
            address_stat = await self.client.get_address_status(address=unlock_key)
            # address_logs = await self.client.get_transaction_logs(address=unlock_key)
            
            #logging.error("address_logs: %s", json.dumps(address_logs))
            if address_stat and "balance_per_token" in address_stat:
                logging.error("balance: %s", json.dumps(address_stat["balance_per_token"]))
                # Todo post.coin_option needs a check before token type right now assumed to be mob
                if "0" in address_stat["balance_per_token"]:
                    mob_info = address_stat["balance_per_token"]["0"]
                    logging.error("balance: %s", json.dumps(address_stat["balance_per_token"]["0"]))
            else:
                return False

        if not mob_info:
            return False
        else: 
            balance = int(mob_info["unspent"]) / 1000000000000
            logging.error("balance: %s", json.dumps(balance))
            # TODO: Check coin option
            unlock_fee_str = str(post.unlock_fee)
            logging.error("unlock fee: %s", unlock_fee_str)
            logging.error(balance >= post.unlock_fee)
            paid_enough = balance >= post.unlock_fee
            return paid_enough
                

    async def check_for_owner_of_post_and_grab_a_public_address(self, post):
        author = await sync_to_async(getattr)(post, 'author')
        account = await sync_to_async(getattr)(author, 'account')
        account_key_id = await sync_to_async(getattr)(account, 'account_key_id')
        public_address = await self.client.assign_address_for_account(account_id=account_key_id)
        logging.info("public_address: %s", json.dumps(public_address))
        return public_address['public_address_b58']

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

            logging.error("secrets: %s", json.dumps(secrets["mnemonic"]))
            user_account.account_key_id = crypto_account["id"]
            user_account.account_name = crypto_account["name"]
            user_account.account_main_address = public_address['public_address_b58']
            user_account.next_block_to_sync = crypto_account["next_block_index"]
            user_account.last_mobilecoin_balance_observed = 0  # Set initial balance, update as needed
            user_account.recovery_mnemonic = secrets["mnemonic"]
            await sync_to_async(user_account.save)()


            return user_account, crypto_account
