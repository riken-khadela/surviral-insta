# Generated by Django 3.2.3 on 2024-02-29 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('twbot', '0011_run_command'),
    ]

    operations = [
        migrations.AddField(
            model_name='run_command',
            name='execute',
            field=models.BooleanField(default=False),
        ),
    ]
