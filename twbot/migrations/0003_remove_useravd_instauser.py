# Generated by Django 3.2.3 on 2023-12-07 12:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('twbot', '0002_useravd_instauser'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='useravd',
            name='instauser',
        ),
    ]
