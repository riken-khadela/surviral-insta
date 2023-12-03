

import random
import shutil
import sys
import time, os
from concurrent import futures
from dotenv import load_dotenv
load_dotenv()
import numpy as np
from django.core.management.base import BaseCommand
from django.db import connection

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
        parser.add_argument('-n',
                            type=int,
                            help="Number of Accounts")
        parser.add_argument('-m', '--run_times', type=int, default=0,
                            help='After the run times, the bot will exit(0 means no effect)')
        parser.add_argument(
            "--no_vpn",
            type=bool,
            nargs="?",
            const=True,
            default=1,
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

        connection.connect()
        user_avd.delete()
        delete_avd(user_avd.name)

    def run_tasks(self, required_accounts):
        """

        :param required_accounts: 

        """
        count = 0
        accounts_created = 0
        while accounts_created < required_accounts:
            # Check PC Restart request
            total, used, free = shutil.disk_usage(self.disk_path)
            free_in_gb = free // (2 ** 30)
            if free_in_gb < MIN_HARD_DISK_FREE_SPACE:
                LOGGER.info(
                    f"Your hard disk free space less than {MIN_HARD_DISK_FREE_SPACE} so stopping account creation")
                break
            
            avds = UserAvd.objects.all()
            avds_port = [i.port for i in avds]
            avds_name = [i.name for i in avds]
            ports = []
            devices = []
            for i in range(5550,6250):
                if not i in avds_port :
                    ports.append(i)
                if not f"instagram_{i}" in avds_name :
                    devices.append(f"instagram_{i}")
            

            start_time = time.time()
            avd_name = random.choice(devices)
            port = random.choice(ports)

            # create all accounts in USA
            country = 'Hong Kong'
            LOGGER.debug(f'country: {country}')
            try:
                # create an avd user, at the same time, creat the relative AVD
                # before deleting this avd user, first deleting the relative AVD
                LOGGER.debug('Start to creating AVD user')

                user_avd = UserAvd.objects.create(
                    name=avd_name,
                    port=port,
                    proxy_type="CYBERGHOST",
                    country=country,
                    pcname = os.getenv('PC')
                )
                creat_avd_bool = create_avd(avd_name)
                if not creat_avd_bool :
                    self.delete_avds(user_avd)
                    raise "the avd could not create!"

                LOGGER.debug(f'AVD USER: {user_avd}')

                tb = InstaBot(user_avd.name)

                # Connect vpn
                if not self.no_vpn:
                    if not tb.connect_to_vpn(country=country):
                        tb.check_apk_installation()
                        # raise Exception("Couldn't able to connect Nord VPN")
                else:
                    tb.check_apk_installation()
                breakpoint()
                # accounts_created_bool = tb.create_account()
                accounts_created_bool = False
                if accounts_created_bool == True:
                    accounts_created += 1
                else :
                    self.delete_avds(user_avd)

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
                    user_avd.delete() if user_avd else None
                    self.delete_avds(user_avd)
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
                    self.clean_bot(tb, False)
                else:
                    name = user_avd.name
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

        required_accounts = int(options.get('n'))

        self.no_vpn = options.get('no_vpn')
        self.parallel_number = options.get('parallel_number')

        self.run_times = options.get('run_times')
        LOGGER.debug(f'Run times: {self.run_times}')

        self.disk_path = options.get('disk_path')
        if not self.disk_path :
            self.disk_path = "/"

        requied_account_list = [n.size for n in
                                np.array_split(np.array(range(required_accounts)), self.parallel_number)]
        with futures.ThreadPoolExecutor(max_workers=self.parallel_number) as executor:
            for i in range(self.parallel_number):
                executor.submit(self.run_tasks, requied_account_list[i])
        print(f" All created UserAvd and TwitterAccount ****\n")



    @staticmethod
    def clean_bot(tb, is_sleep=True):
        """

        :param tb: 
        :param is_sleep:  (Default value = True)

        """
        try :
            LOGGER.debug('Quit app driver and kill bot processes')
            #  tb.app_driver.quit()
            tb.kill_bot_process(appium=False, emulators=True)
            if is_sleep:
                random_sleep(60, 80)
        except : ...