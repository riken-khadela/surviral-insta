import subprocess,os
from django.core.management.base import BaseCommand
from twbot.models import UserAvd,User_details
from dotenv import load_dotenv
load_dotenv()
class Command(BaseCommand):

    def handle(self, *args, **options):
        
        avd_list = subprocess.check_output(['emulator', '-list-avds'])
        avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
        print(avd_list)