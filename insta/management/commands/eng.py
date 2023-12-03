

import random
import shutil
import sys
import time, os
from concurrent import futures
from dotenv import load_dotenv
load_dotenv()
import numpy as np
from django.core.management.base import BaseCommand

import parallel
from conf import US_TIMEZONE, PARALLEL_NUMER, MIN_HARD_DISK_FREE_SPACE, MAX_ACTIVE_ACCOUNTS
from insta.models import UserAvd, User_details
from exceptions import (CannotRegisterThisPhoneNumberException, CannotGetSms, GetSmsCodeNotEnoughBalance,
                        PhoneRegisteredException)
from main import LOGGER
from insta.bot import InstaBot
from insta.cyberghostvpn import CyberGhostVpn
from utils import random_sleep
from insta.utils import CURRENT_PC_NAME, delete_avd, get_random_username, create_avd, delete_avd

class Command(BaseCommand):
    def add_arguments(self, parser):
        """

        :param parser: 

        """
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

    def delete_avds(self,user_avd):
        user_avd.delete()
        delete_avd(user_avd.avdsname)

    def run_tasks(self):
        """

        :param required_accounts: 

        """
        while True :
            all_active_users = User_details.objects.filter(avd_pc=os.getenv('PC'),status="ACTIVE").order_by('?')
            for user in all_active_users : 
                
                try:    
                    tb = InstaBot(user.avdsname)

                    country = 'Hong Kong'
                    if not self.no_vpn:
                        if not tb.connect_to_vpn(country=country):
                            raise Exception("Couldn't able to connect Nord VPN")
                    else:
                        tb.check_apk_installation()
                    
                    tb.Engagement_main(user.id)
                    self.clean_bot(tb, False)

                except GetSmsCodeNotEnoughBalance as e:
                    LOGGER.debug('Not enough balance in GetSMSCode')
                    tb.kill_bot_process(True, True)
                    sys.exit(1)

                except Exception as e:

                    #  print(traceback.format_exc())
                    LOGGER.exception(e)
                    accounts_created += 1  # avoid infinite loop
                    try:
                        tb.kill_bot_process(True, True)
                    except:
                        pass
                finally:
                    if self.run_times != 0:
                        count += 1
                        if count >= self.run_times:
                            LOGGER.info(f'Real run times: {count}, now exit')
                            break

                    if 'tb' in locals() or 'tb' in globals():
                        LOGGER.info(f'Clean the bot: {user.avdsname}')
                        self.clean_bot(tb, False)
                    else:
                        name = user.avdsname
                        port = ''
                        parallel.stop_avd(name=name, port=port)

    def handle(self, *args, **options):
        """

        :param args:
        :param options:

        """
        self.total_accounts_created = 0
        self.avd_pack = []
        if UserAvd.objects.filter(pcname=CURRENT_PC_NAME).count() >= MAX_ACTIVE_ACCOUNTS or User_details.objects.filter(status='ACTIVE',avd_pc=CURRENT_PC_NAME).count() >= MAX_ACTIVE_ACCOUNTS:
            return f"Cannot create more than {MAX_ACTIVE_ACCOUNTS} AVDs please delete existing to create a new one."

        self.no_vpn = options.get('no_vpn')
        self.parallel_number = options.get('parallel_number')

        self.run_times = options.get('run_times')
        LOGGER.debug(f'Run times: {self.run_times}')

        self.disk_path = options.get('disk_path')
        if not self.disk_path :
            self.disk_path = "/"

        with futures.ThreadPoolExecutor(max_workers=self.parallel_number) as executor:
            for i in range(self.parallel_number):
                executor.submit(self.run_tasks)
        print(f" All created UserAvd and TwitterAccount ****\n")


    @staticmethod
    def clean_bot(tb, is_sleep=True):
        """

        :param tb: 
        :param is_sleep:  (Default value = True)

        """
        LOGGER.debug('Quit app driver and kill bot processes')
        try :
            # tb.app_driver.quit()
            tb.kill_bot_process(appium=False, emulators=True)
            if is_sleep:
                random_sleep(60, 80)
        except : ...