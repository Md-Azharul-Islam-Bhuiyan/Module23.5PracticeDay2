# Generated by Django 5.0 on 2024-01-03 04:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_alter_transaction_transaction_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='is_bancrupt',
            field=models.BooleanField(default=False),
        ),
    ]
