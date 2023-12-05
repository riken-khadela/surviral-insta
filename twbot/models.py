import os.path
from pyexpat import model
import random
import subprocess

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
# Create your models here.
from django.db import models
from django.db.models import JSONField as JSONFieldPostgres
from django.db.models.signals import post_save, pre_delete

from conf import AVD_PACKAGES, AVD_DEVICES
from constants import ACC_BATCH
from core.models import User
# from django.contrib.auth.models import  User
from main import LOGGER
from twbot.cyberghostvpn import CyberGhostVpn
from twbot.vpn.nord_vpn import NordVpn
from django.utils import timezone


# Create your models here.
class TimeStampModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        
class TodayOpenAVDManager(models.Manager):
    def get_queryset(self):
        now = timezone.now()
        return super().get_queryset().filter(created_at__date=now.date())

class TodayOpenAVD(models.Model):
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TodayOpenAVDManager()

    def __str__(self):
        return self.name
    

class UserAvd(TimeStampModel):
    prox_type = (
        ("NORD_VPN", "NordVPN"),
        ("SURFSHARK", "SURFSHARK"),
        ("SMART_PROXY", "SMART_PROXY"),
        ("CYBERGHOST", "CYBERGHOST"),
    )
    COUNTRIES = tuple((i,) * 2 for i in CyberGhostVpn.get_server_list())
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="avd_user")
    name = models.CharField(max_length=100, unique=True)
    port = models.IntegerField(unique=True)
    proxy_type = models.CharField(max_length=50, choices=prox_type, blank=True, null=True)
    country = models.CharField(max_length=40, choices=COUNTRIES, null=True, blank=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.name}:{self.port}" 

class User_details(models.Model):
    STATUS = (
        ("ACTIVE", "ACTIVE"),
        ("LOGIN_ISSUE","LOGIN_ISSUE"),
        ("SUSPENSION","SUSPENSION")
    )
    avdsname = models.CharField(max_length=255)
    username = models.CharField(max_length=255,blank=True, null=True)
    number = models.BigIntegerField(null=False)
    password = models.CharField(max_length=255,blank=True, null=True)
    birth_date = models.CharField(max_length=255,blank=True, null=True)
    birth_month = models.CharField(max_length=255,blank=True, null=True)
    birth_year = models.CharField(max_length=255,blank=True, null=True)
    updated = models.BooleanField(default=False,blank=True, null=True)
    random_action = models.IntegerField(default=0,blank=True, null=True)
    # rio = models.BooleanField(default=False)
    engagement = models.IntegerField(default=0,blank=True, null=True)
    status = models.CharField(max_length=255,choices=STATUS,default='ACTIVE',blank=True, null=True)
    following = models.IntegerField(default=0)
    followers = models.IntegerField(default=0)
    can_search = models.BooleanField(default=True)
    avd_pc = models.CharField(max_length=255,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    is_filtered = models.BooleanField(default=False)
    bio = models.CharField(max_length=1024, blank=True, null=True)
    is_bio_updated = models.BooleanField(default=False)
    def __str__(self):
        return self.username

class postdetails(models.Model):
    details = models.CharField(max_length=10000)
    like = models.IntegerField()
    target_comment = models.IntegerField(default=0)
    target_like = models.IntegerField(default=0)
    comment = models.IntegerField(default=0)
    commented_users = models.ManyToManyField(User_details, related_name='commented_posts')
    shared_users = models.ManyToManyField(User_details, related_name='shared_posts')
    saved_users = models.ManyToManyField(User_details, related_name='save_posts')
    date = models.DateField(auto_now_add=True)

def create_avd(sender, instance, **kwargs):
    from twbot.bot import InstaBot
    created = kwargs.get('created')

    if created:
        LOGGER.info('Start to create AVD')
        try:
            # Initialize bot
            twbot = InstaBot(instance.name, start_appium=False, start_adb=False)

            # Create avd
            twbot.create_avd(avd_name=instance.name)
            updated_config = os.path.join(settings.BASE_DIR, 'twbot/avd_config/config.ini')
            new_config_file = f"{settings.AVD_DIR_PATH}/{instance.name}.avd/config.ini"
            LOGGER.debug(f'updated_config: {updated_config}')
            LOGGER.debug(f'new_config_file: {new_config_file}')
            if os.path.isdir(settings.AVD_DIR_PATH) and os.path.isfile(new_config_file):
                from shutil import copyfile
                copyfile(updated_config, new_config_file)

            print(f"**** AVD created with name: {instance.name} and port: {instance.port} ****")

        except Exception as e:
            instance.delete()
            print(f"Couldn't create avd due to the following error \n")
            print(e)


def create_better_avd(sender, instance, **kwargs):
    from twbot.bot import InstaBot
    created = kwargs.get('created')

    if created:
        LOGGER.info('Start to create AVD')
        try:
            # Initialize bot
            twbot = InstaBot(instance.name, start_appium=False, start_adb=False)
            device = random.choice(AVD_DEVICES)  # get a random device
            print(device)
            # package = random.choice(AVD_PACKAGES)  # get a random package
            twbot.create_avd(avd_name=instance.name,
                             device=device)

            LOGGER.info(f"**** AVD created with name: {instance.name} and port: {instance.port} ****")

        except Exception as e:
            # commands = [f'lsof -t -i tcp:{instance.port} | xargs kill -9',
            #                 f'lsof -t -i tcp:4724 | xargs kill -9']
            # for cmd in commands:
            #     p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
            instance.delete()
            LOGGER.error(f"Couldn't create avd due to the following error \n")
            LOGGER.error(e)


def delete_avd(sender, instance, **kwargs):
    try:
        cmd = f'avdmanager delete avd --name {instance.name}'
        p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
    except Exception as e:
        pass


#  post_save.connect(create_avd, sender=UserAvd)
# post_save.connect(create_better_avd, sender=UserAvd)
# pre_delete.connect(delete_avd, sender=UserAvd)
