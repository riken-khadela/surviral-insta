import sys
import time, os
from concurrent import futures
from xml.dom import UserDataHandler

import numpy as np
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from conf import US_TIMEZONE, PARALLEL_NUMER
from core.models import User, user_detail
from twbot.models import User_details
from exceptions import PhoneRegisteredException, CannotRegisterThisPhoneNumberException, GetSmsCodeNotEnoughBalance
from twbot.bot import *
from twbot.utils import delete_avd_by_name
load_dotenv()
AGENT='xanametaverse'



class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-m', '--run_times', type=int, default=0,
                            help='After the run times, the bot will exit(0 means no effect)')
        parser.add_argument(
            "--no_vpn",
            type=bool,
            nargs="?",
            const=True,
            default=False,
            help="Whether to use VPN or not, if it presents, don't use VPN.",
        )
        parser.add_argument(
            '--parallel_number',
            nargs='?',
            default=PARALLEL_NUMER,
            type=int,
            help=(f'Number of parallel running. Default: {PARALLEL_NUMER}'
                  '(PARALLEL_NUMER in the file conf.py)')
        )

    def create_avd(self,avdname):
        # ...
        LOGGER.debug('Start to creating AVD user')
        twbot = InstaBot(emulator_name=avdname, start_appium=False, start_adb=False)
        device = random.choice(AVD_DEVICES)  # get a random device
        # package = random.choice(AVD_PACKAGES)  # get a random package
        twbot.create_avd(avd_name=avdname,device=device)
        LOGGER.info(f"**** AVD created with name1111: {avdname} ****")
        return avdname
    
    def create_avd_object(self,avdname):
        LOGGER.debug('Start to creating AVD user')
        used_ports = set(UserAvd.objects.values_list('port', flat=True))
        port_range = range(1, 9000)  # Adjust the range as needed
        port = next((1000 + port for port in port_range if (1000 + port) not in used_ports), None)
        if port is not None:
            country = 'Hong Kong'
            LOGGER.debug(f'country: {country}')
            try:
                if 'united states' in country.lower():
                    user_avd = UserAvd.objects.create(
                        user=User.objects.all().first(),
                        name=avdname,
                        port=port,
                        proxy_type="CYBERGHOST",
                        country=country,
                        timezone=random.choice(US_TIMEZONE),
                    )
                else:
                    user_avd = UserAvd.objects.create(
                        user=User.objects.all().first(),
                        name=avdname,
                        port=port,
                        proxy_type="CYBERGHOST",
                        country=country
                    )
            except Exception as e:
                print(e)
                self.create_avd_object(avdname)

            LOGGER.debug(f'AVD USER: {user_avd}')
            
            
            LOGGER.info(f"**** AVD created with name2222: {avdname} ****")
            return user_avd

    def run_tasks(self,i):
        country = 'Hong Kong'
        
        while True:
            # all_users = list(user_detail.objects.using('monitor').filter(status='ACTIVE').order_by('-created_at'))
            # all_users = list(User_details.objects.filter(status='ACTIVE').order_by('-created_at'))
            csv_path = os.path.join(os.getcwd(),'csv','this_pc_avd.csv')
            from datetime import datetime
            all_users = []
            df = pd.DataFrame()
            
            if os.path.exists(os.path.join(os.getcwd(),'csv','this_pc_avd.csv')) :
                df = pd.read_csv(csv_path)  
                enged_date_times_li = [datetime.strptime(dt, '%Y-%m-%d %H:%M:%S.%f%z') for dt in df['eng_at'].tolist()]
                enged_date_times_li = [datetime.strptime(dt, '%Y-%m-%d %H:%M:%S.%f%z') for dt in df['eng_at'].tolist()]
                sorted_user_li = sorted(enged_date_times_li)
                user_data_dict = df.to_dict(orient='records')
                all_users = [user_data_dict[enged_date_times_li.index(user)] for user in sorted_user_li]
                
                
            if not all_users :
                all_users = list(User_details.objects.filter(status='ACTIVE',avdsname='instagram_5073730').order_by('?'))
                
            ...
            for userr in all_users:
                if df.empty :
                    userr_avd = UserAvd.objects.filter(name=userr.avdsname).first()
                else :
                    userr_avd = UserAvd.objects.filter(id=userr['avd_id']).first()
                    userr = User_details.objects.filter(username=userr['username']).first()
                    
                
                avd_list = subprocess.check_output(['emulator', '-list-avds'])
                avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
                if userr.avdsname not in avd_list: continue
                
                try:
                    output = subprocess.check_output(['adb', 'devices']).decode().strip()
                    avd_names = [line.split('\t')[0] for line in output.split('\n')[1:] if line.endswith('\tdevice')]
                    if userr.avdsname in avd_names:
                        continue
                except subprocess.CalledProcessError:
                    pass

                try:
                    if userr.is_bio_updated:
                        comment = True
                    else:
                        comment = False
                    
                    tb = InstaBot(userr.avdsname,user_avd_obj=userr_avd)
                    tb.check_apk_installation()
                    # Connect vpn
                    if not self.no_vpn:
                        time.sleep(10)
                        if not tb.connect_to_vpn(country=country):
                            raise Exception("Couldn't able to connect Cyberghost VPN")
                        
                    
                    if tb.login(userr.username,userr.password) :
                        
                        tb.send_views(AGENT,comment=comment)
                        

                except GetSmsCodeNotEnoughBalance as e:
                    LOGGER.debug('Not enough balance in GetSMSCode')
                    tb.kill_bot_process(True, True)
                    sys.exit(1)
                except Exception as e:
                    print(traceback.format_exc())
                    try:
                        tb.kill_bot_process(True, True)
                        # user_avd.delete() if user_avd else None
                    except:
                        pass
                finally:
                    if self.run_times != 0:
                        count += 1
                        if count >= self.run_times:
                            LOGGER.info(f'Real run times: {count}, now exit')
                            break

                    if 'tb' in locals() or 'tb' in globals():
                        LOGGER.info(f'Clean the bot: {userr.avdsname}')
                        self.clean_bot(tb,is_sleep=False)
                    else:
                        name = userr.avdsname
                        port = ''
                        parallel.stop_avd(name=name, port=port)
    def handle(self, *args, **options):
        self.total_accounts_created = 0
        self.avd_pack = []
        # if UserAvd.objects.all().count() >= 500:
        #     return "Cannot create more than 500 AVDs please delete existing to create a new one."


        self.no_vpn = options.get('no_vpn')
        self.parallel_number = options.get('parallel_number')
        print(1)
        self.run_times = options.get('run_times')
        LOGGER.debug(f'Run times: {self.run_times}')
        while True:
            with futures.ThreadPoolExecutor(max_workers=self.parallel_number) as executor:
                for i in range(self.parallel_number):
                    executor.submit(self.run_tasks,i)
            print(f" All created UserAvd and TwitterAccount ****\n")
        
        # random_sleep(10, 30)

    def clean_bot(self, tb, is_sleep=True):
        LOGGER.debug('Quit app driver and kill bot processes')
        #  tb.app_driver.quit()
        tb.kill_bot_process(appium=False, emulators=True)
        if is_sleep:
            random_sleep(10, 20)
