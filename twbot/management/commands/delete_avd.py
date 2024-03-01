from django.core.management.base import BaseCommand
import subprocess,os
import pandas as pd
from twbot.models import User_details

class Command(BaseCommand):
    # def add_arguments(self, parser):
    
    def delete_avd(self,avdname) :
        print("delete avd name :",avdname)
        try:
            subprocess.check_output(['avdmanager', 'delete', 'avd', '-n', avdname])
        except Exception as e:
            print(e)
        ...
    def handle(self, *args, **options):
        # return 
        avd_list = subprocess.check_output(['emulator', '-list-avds'])
        avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
        
        # try:
        #     all_inactive_avds = pd.read_csv('delete_avd.csv')
        # except FileNotFoundError:
        #     all_inactive_avds = pd.DataFrame(columns=['avd'])
        #     all_inactive_avds.to_csv('delete_avd.csv', index=False)
            
        # all_inactive_avds = pd.read_csv('delete_avd.csv')
        # print(len(all_inactive_avds))
        # for avd in all_inactive_avds:
        #     if avd in avd_list:
        #         print(f"AVD {avd} with login issue so deleting")
        #         try:
        #             subprocess.check_output(['avdmanager', 'delete', 'avd', '-n', avd])
        #             all_inactive_avds.drop(all_inactive_avds.index[all_inactive_avds['avd']== f'{avd}'], axis=0,inplace=True)
        #             all_inactive_avds.to_csv('delete_avd.csv',index=False)
        #         except Exception as e:
        #             print(e)
        csv_path = os.path.join(os.getcwd(),'csv','this_pc_avd.csv')
        if os.path.exists(os.path.join(os.getcwd(),'csv','this_pc_avd.csv')) :
            this_pc_avds_list = pd.read_csv(csv_path)['Avdsname'].tolist()
            for pcavd in avd_list :
                detailes = User_details.objects.filter(avdsname=pcavd).first()
                if not pcavd in this_pc_avds_list and not detailes:
                    self.delete_avd(pcavd)

            
            # inactive_user = User_details.objects.exclude(status="ACTIVE")
            # for user in inactive_user :
                
            #     if not user.avdsname in this_pc_avds_list and user.avdsname in avd_list :
            #         self.delete_avd(user.avdsname)
        

        


