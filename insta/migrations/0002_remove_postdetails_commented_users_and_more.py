# Generated by Django 4.2.7 on 2023-11-18 00:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('insta', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postdetails',
            name='commented_users',
        ),
        migrations.RemoveField(
            model_name='postdetails',
            name='saved_users',
        ),
        migrations.RemoveField(
            model_name='postdetails',
            name='shared_users',
        ),
        migrations.DeleteModel(
            name='TodayOpenAVD',
        ),
        migrations.DeleteModel(
            name='postdetails',
        ),
    ]