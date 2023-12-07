from django.core.management.base import BaseCommand
import subprocess
import pandas as pd, os
from twbot.models import User_details
from dotenv import load_dotenv

class Command(BaseCommand):
    # def add_arguments(self, parser):
    def handle(self, *args, **options):
            
        # avd_list = subprocess.check_output(['emulator', '-list-avds'])
        # avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
        avds_li = []
        same_avds_user = []
        inactive_user = User_details.objects.exclude(status='ACTIVE').order_by('?')
        for user in inactive_user :
            if user.avdsname in avds_li :
                same_avds_user.append(user.avdsname)
            else :
                if user.avdsname not in avds_li :
                    avds_li.append(user.avdsname)
        breakpoint()
