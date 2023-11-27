from django.db import models

# Create your models here.


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