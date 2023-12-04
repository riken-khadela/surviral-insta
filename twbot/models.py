from django.db import models
from insta.cyberghostvpn import CyberGhostVpn

# Create your models here.

class TimeStampModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True




class User_details(models.Model):
    STATUS = (
        ("ACTIVE", "ACTIVE"),
        ("LOGIN_ISSUE","LOGIN_ISSUE"),
        ("SUSPENSION","SUSPENSION")
    )
    GENDER = (
        ("MALE", "MALE"),
        ("FEMALE","FEMALE"),
        ("NONE","NONE")
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
    engagement = models.IntegerField(default=0,blank=True, null=True)
    status = models.CharField(max_length=255,choices=STATUS,default='ACTIVE',blank=True, null=True)
    gender = models.CharField(max_length=255,choices=GENDER,default='NONE',blank=True, null=True)
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
    


class UserAvd(models.Model):
    prox_type = (
        ("NORD_VPN", "NordVPN"),
        ("SURFSHARK", "SURFSHARK"),
        ("SMART_PROXY", "SMART_PROXY"),
        ("CYBERGHOST", "CYBERGHOST"),
    )

    COUNTRIES = tuple((i,) * 2 for i in CyberGhostVpn.get_server_list())
    name = models.CharField(max_length=100, unique=True)
    port = models.IntegerField(unique=True)
    proxy_type = models.CharField(max_length=50, choices=prox_type, default="CYBERGHOST", blank=True, null=True)
    country = models.CharField(max_length=40, choices=COUNTRIES, null=True, blank=True)
    timezone = models.CharField(max_length=50, blank=True, null=True)
    pcname = models.CharField(max_length=50, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return f"{self.name}:{self.port}"