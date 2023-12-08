from django.core.management.base import BaseCommand
import subprocess
import pandas as pd

class Command(BaseCommand):
    # def add_arguments(self, parser):
    def handle(self, *args, **options):
        all_inactive_avds = pd.read_csv('delete_avd.csv')
        
        print(len(all_inactive_avds))
        avd_list = subprocess.check_output(['emulator', '-list-avds'])
        avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
        for avd in all_inactive_avds:
            if avd in avd_list:
                print(f"AVD {avd} with login issue so deleting")
                try:
                    subprocess.check_output(['avdmanager', 'delete', 'avd', '-n', avd])
                    all_inactive_avds.drop(all_inactive_avds.index[all_inactive_avds['avd']== f'{avd}'], axis=0,inplace=True)
                    all_inactive_avds.to_csv('delete_avd.csv',index=False)
                except Exception as e:
                    print(e)

        


