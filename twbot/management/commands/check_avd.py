from typing import Any
from django.core.management.base import BaseCommand
import subprocess
from twbot.models import *
import pandas as pd
from main import LOGGER

class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any):
        # all_users = list(User_details.objects.filter(status='ACTIVE').order_by('?'))
    
        print(f'\n\n\n--- PC number : {os.getenv("SYSTEM_NO")}\n\n\n')
        all_users = list(User_details.objects.filter(status='ACTIVE', avd_pc=os.getenv("SYSTEM_NO")).order_by('?'))
        avd_list = subprocess.check_output(['emulator', '-list-avds'])
        avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
        os.makedirs('csv',exist_ok=True)
        csv_path = os.path.join(os.getcwd(),'csv','this_pc_avd.csv')
        df = pd.read_csv(csv_path)
        not_in_both = 0
        not_in_data = 0
        not_in_csv = 0
        suceess = 0
        if not df.empty:
            ThisPcUsername = df['username'].tolist()
        for user in all_users :
            user_avd = UserAvd.objects.filter(name=user.avdsname)
            if user_avd and user.username in ThisPcUsername :
                # LOGGER.info('Avd Object successfully created in both (csv and database)...')
                suceess+=1
            elif user_avd and user.username not in ThisPcUsername:
                # LOGGER.info('avd object create in database, but not created in csv')
                not_in_csv+=1
            elif not user_avd and user.username in ThisPcUsername:
                # LOGGER.info('avd object not create in database, but created in csv')
                not_in_data+=1
            else:
                # LOGGER.info('avd object not create in both')
                not_in_both+=1
        LOGGER.info(f'{not_in_both} avds not created....')
        LOGGER.info(f'{suceess} avds sucessfully created....')
        LOGGER.info(f'{not_in_data} avds not in database, but created....')
        LOGGER.info(f'{not_in_csv} avds not in csv, but created in database....')


                
'''
User details in system number
Use avd detailes
Csv 
def delete_avd(self,avdname) :
        print("delete avd name :",avdname)
        try:
            subprocess.check_output(['avdmanager', 'delete', 'avd', '-n', avdname])
        except Exception as e:
            print(e)
            
Step 1 :
Find User details with system numberr
for avd in avd_list:
    user_avd = UserAvd.objects.filter(name=user.avdsname).first()
    detailes = User_details.objects.filter(status='ACTIVE',avdsname=avd).first()
    
    if not detailes:
        if avd not in csvlist:
            self.delete_avd()
    
    # if detailes:
    #     if detailes.username not in ThisPcUsername:
    #         df.loc[len(df.index)] = [user_avd.id,user.id,user_avd.name,user.username,user.created_at,user.created_at]
    #         df.to_csv(csv_path,index=False)
    
    
    
user name in csv
avd in system

''' 
    