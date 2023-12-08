import sys
import time, os
from concurrent import futures
from xml.dom import UserDataHandler

import numpy as np
from django.core.management.base import BaseCommand

from conf import US_TIMEZONE, PARALLEL_NUMER
from core.models import User, user_detail
from exceptions import PhoneRegisteredException, CannotRegisterThisPhoneNumberException, GetSmsCodeNotEnoughBalance
from twbot.actions.follow import *
from twbot.bot import *


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
        twbot = InstaBot(avdname, start_appium=False, start_adb=False)
        device = random.choice(AVD_DEVICES)  # get a random device
        # package = random.choice(AVD_PACKAGES)  # get a random package
        twbot.create_avd(avd_name=avdname,device=device)
        LOGGER.info(f"**** AVD created with name1111: {avdname} ****")
        return avdname
    
    def create_avd_object(self,avdname):
        LOGGER.debug('Start to creating AVD user')
        
        ports = list(
                filter(
                    lambda y: not UserAvd.objects.filter(port=y).exists(),
                    map(
                        lambda x: 5550 + x, range(1, 500)
                    )
                )
            )
        
        port = random.choice(ports)

        country = 'Hong Kong'
        LOGGER.debug(f'country: {country}')
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

        LOGGER.debug(f'AVD USER: {user_avd}')
        
        
        LOGGER.info(f"**** AVD created with name2222: {avdname} ****")
        return user_avd
    

    def run_tasks(self):
        country = 'Hong Kong'
        
        
        while True:
            # all_users = [User_details.objects.filter(avdsname='instagram_4866').first()]
            # all_users = list(user_detail.objects.using('monitor').filter(status='ACTIVE').order_by('-created_at'))
            all_users = list(user_detail.objects.using('monitor').filter(status='ACTIVE',updated=True).order_by('?'))
            print(len(all_users),'-----')
            for userr in all_users:
                LOGGER.info(f'{userr} -------11111')
                df = pd.read_csv('delete_avd.csv')
                if not UserAvd.objects.filter(name = userr.avdsname).exists() and not userr.avdsname in df['avd'].values:
                    user_avd = self.create_avd_object(userr.avdsname)
                else :
                    user_avd = UserAvd.objects.filter(name=userr.avdsname).first()
                    avd_list = subprocess.check_output(['emulator', '-list-avds'])
                    avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
                    print(avd_list)
                    if not user_avd.name in avd_list:
                        UserAvd.objects.filter(name=userr.avdsname).first().delete()
                        user_avd = self.create_avd_object(userr.avdsname)
                
                        print(user_avd.name,'======================================')
                        print(avd_list)
                    
                
            
                try:
                    
                    tb = InstaBot(user_avd.name)
                    tb.check_apk_installation()

                    # Connect vpn
                    if not self.no_vpn:
                        time.sleep(10)
                        if not tb.connect_to_vpn(country=country):
                            raise Exception("Couldn't able to connect Cyberghost VPN")
                    
                    if tb.login(userr.username,userr.password) :
                        tb.follow_rio()
                        tb.send_views(AGENT)
                    
                    # accounts_created_bool = tb.create_account()
                    # time.sleep(300)


                except GetSmsCodeNotEnoughBalance as e:
                    LOGGER.debug('Not enough balance in GetSMSCode')
                    tb.kill_bot_process(True, True)
                    sys.exit(1)
                except Exception as e:
                    print(traceback.format_exc())
                    try:
                        tb.kill_bot_process(True, True)
                        user_avd.delete() if user_avd else None
                    except:
                        pass
                finally:
                    if self.run_times != 0:
                        count += 1
                        if count >= self.run_times:
                            LOGGER.info(f'Real run times: {count}, now exit')
                            break

                    if 'tb' in locals() or 'tb' in globals():
                        LOGGER.info(f'Clean the bot: {user_avd.name}')
                        self.clean_bot(tb,is_sleep=False)
                    else:
                        name = user_avd.name
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
        with futures.ThreadPoolExecutor(max_workers=self.parallel_number) as executor:
            for i in range(self.parallel_number):
                executor.submit(self.run_tasks)
        print(f" All created UserAvd and TwitterAccount ****\n")
        
        # random_sleep(10, 30)

    def clean_bot(self, tb, is_sleep=True):
        LOGGER.debug('Quit app driver and kill bot processes')
        #  tb.app_driver.quit()
        tb.kill_bot_process(appium=False, emulators=True)
        if is_sleep:
            random_sleep(10, 20)
