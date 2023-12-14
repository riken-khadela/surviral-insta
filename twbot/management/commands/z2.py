import subprocess,os
from django.core.management.base import BaseCommand
from twbot.models import UserAvd,User_details
from dotenv import load_dotenv
load_dotenv()
class Command(BaseCommand):

    def handle(self, *args, **options):
        # print(os.environ.get('SENDER_MAIL'),'-----')
        # breakpoint()
        objects_with_not_null_field = User_details.objects.filter(avd_pc='PKPC16')
        print(len(objects_with_not_null_field))
        
        
        avd_list = subprocess.check_output(['emulator', '-list-avds'])
        avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
        all_user = User_details.objects.filter(avd_pc__isnull=True,status="ACTIVE")
        unique_avd_name = []
        dub_avd_name = []
        system_no = os.environ.get('SYSTEM_NO')
        if not system_no : 
            print('There is not system number defined')
            return
        
        breakpoint()
        
        for user in all_user : 
            
            if user.avdsname in avd_list :
                if not user.avdsname in unique_avd_name :
                    unique_avd_name.append(user.avdsname)
                else:
                    dub_avd_name.append(user)
        
        if len(dub_avd_name) == 0:
            print(dub_avd_name)
            for unique in unique_avd_name:
                unique.avd_pc = system_no
                unique.save()
                print('user id :',unique.id,'systemno :',unique.avd_pc)
                ...
        else :
            breakpoint()
        