from math import e
from django.core.management.base import BaseCommand
import pandas as pd, os, subprocess
from twbot.models import User_details,UserAvd

class Command(BaseCommand):
    # def add_arguments(self, parser):
    #         parser.add_argument('-m', '--run_times', type=int, default=0,
    #                             help='After the run times, the bot will exit(0 means no effect)')
    #         parser.add_argument(
    #             "--no_vpn",
    #             type=bool,
    #             nargs="?",
    #             const=True,
    #             default=False,
    #             help="Whether to use VPN or not, if it presents, don't use VPN.",
    #         )
            
    def handle(self, *args, **options):
        while True :
            try :
                all_users = list(User_details.objects.filter(status='ACTIVE').order_by('?'))
            
                print(f'\n\n\n--- PC number : {os.getenv("SYSTEM_NO")}\n\n\n')
                all_users = list(User_details.objects.filter(status='ACTIVE').order_by('?'))
                avd_list = subprocess.check_output(['emulator', '-list-avds'])
                avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
                print(avd_list,'------------')
                csv_path = os.path.join(os.getcwd(),'csv','this_pc_avd.csv')
                # if not os.path.exists(csv_path) :
                headers = ['avd_id','user_id','Avdsname','username','created_at','eng_at']  # Add your column names here
                df = pd.DataFrame(columns=headers)
                
                ThisPcUsername = []
                if not df.empty:
                    ThisPcUsername = df['username'].tolist()
                
                unique_avd_name = []
                dub_avd_name = []
                for user in all_users : 
                    if user.avdsname in avd_list :
                        if not user.username in ThisPcUsername :
                            user_avd = UserAvd.objects.filter(name=user.avdsname).first()
                            if not user_avd :continue
                            
                            df.loc[len(df.index)] = [user_avd.id,user.id,user_avd.name,user.username,user.created_at,user.created_at]
                            if not user.avdsname in unique_avd_name :
                                unique_avd_name.append(user.avdsname)
                            else:
                                dub_avd_name.append(user.avdsname)
                            print(user.id)
                df.to_csv(csv_path,index=False)
                if  dub_avd_name :
                    print('there are dublicates avds name in user data')
            
            except Exception as e : print(e)
        