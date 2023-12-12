import subprocess,os
from django.core.management.base import BaseCommand
from twbot.models import UserAvd,User_details
from dotenv import load_dotenv
load_dotenv()
class Command(BaseCommand):

    def handle(self, *args, **options):
        # my_variable = os.environ.get('MY_VARIABLE')
        # print(my_variable)
        avd_list = subprocess.check_output(['emulator', '-list-avds'])
        avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
        all_user = User_details.objects.filter(avd_pc__isnull=True,status="ACTIVE")
        unique_avd_name = []
        dub_avd_name = []
        system_no = os.environ.get('SYSTEM_NO')
        for user in all_user : 
            if user.avdsname in avd_list :
                if not user.avdsname in unique_avd_name :
                    unique_avd_name.append(user.avdsname)
                else:
                    dub_avd_name.append(user)
        
        breakpoint()
        print(dub_avd_name)
        