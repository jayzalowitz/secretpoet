# Generated by Django 5.0 on 2023-12-30 08:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_alter_useraccount_account_keys_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='useraccount',
            options={'verbose_name': 'MobileCoin/Eusd Account', 'verbose_name_plural': 'MobileCoin/Eusd Accounts'},
        ),
    ]