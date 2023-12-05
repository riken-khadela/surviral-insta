from django.core.management.base import BaseCommand
import subprocess
import pandas as pd
from twbot.models import User_details, UserAvd

class Command(BaseCommand):
    # def add_arguments(self, parser):
    def handle(self, *args, **options):
        avd_list = subprocess.check_output(['emulator', '-list-avds'])
        avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
        # avd = []
        for avd in avd_list:
            try:
                if not User_details.objects.filter(avdsname=avd).exists():
                    print(f'this avd {avd}')
                    subprocess.check_output(['avdmanager', 'delete', 'avd', '-n', avd])
                    UserAvd.objects.get(name=avd).delete()
            except subprocess.CalledProcessError as e:
                    # Handle the error
                    if 'There is no Android Virtual Device named' in str(e):
                        print(f"AVD '{avd}' does not exist.")
                    else:
                        print(f"An error occurred while deleting the AVD: {e}")
            except Exception as e : print(e)


           