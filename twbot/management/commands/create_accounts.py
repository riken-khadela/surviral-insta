import sys
import time
from concurrent import futures

import numpy as np
from django.core.management.base import BaseCommand
import selenium.common.exceptions as sel_ex

from conf import US_TIMEZONE, PARALLEL_NUMER
from core.models import User
from twbot.models import User_details
from exceptions import PhoneRegisteredException, CannotRegisterThisPhoneNumberException, GetSmsCodeNotEnoughBalance
from twbot.actions.follow import *
from twbot.bot import *


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-n')
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
        # breakpoint()
        LOGGER.debug('Start to creating AVD user')
        twbot = InstaBot(emulator_name=avdname, start_appium=False, start_adb=False)
        device = random.choice(AVD_DEVICES)  # get a random device
        # package = random.choice(AVD_PACKAGES)  # get a random package
        twbot.create_avd(avd_name=avdname,device=device)
        LOGGER.info(f"**** AVD created with name1111: {avdname} ****")
        return avdname

    def run_tasks(self, required_accounts):
        count = 0
        accounts_created = 0
        used_ports = set(UserAvd.objects.values_list('port', flat=True))
        self.ports = [3000 + x for x in range(1, 4000) if (3000 + x) not in used_ports]
        used_name = set(User_details.objects.values_list('avdsname', flat=True))
        self.devices = [f"instagram_{x}" for x in range(1,7000) if f"instagram_{x}" not in used_name]
        # for avd_name  in self.devices:
        while accounts_created < required_accounts :
            # else:break
            # fix the error
            # psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint "twbot_useravd_port_key"
            # DETAIL:  Key (port)=(5794) already exists.
            start_time = time.time()
            port = random.choice(self.ports)
            avd_name = random.choice(self.devices)
            print(avd_name)
            
            LOGGER.info(f'available avdname len is {len(self.devices)}')
            LOGGER.info(f'available ports len is {len(self.devices)}')
            # avd_name = random.choice(self.devices)
            # breakpoint()
            if User_details.objects.filter(avdsname= avd_name).exists():
                continue
            if UserAvd.objects.filter(name = avd_name).exists():
                continue
            avd_list = subprocess.check_output(['emulator', '-list-avds'])
            avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
            if avd_name  in avd_list:
                continue
            # create all accounts in USA
            country = 'Hong Kong'
            LOGGER.debug(f'country: {country}')
            try:
                # if UserAvd.objects.filter(name=avd_name).exists(): continue
                
                # create an avd user, at the same time, creat the relative AVD
                # before deleting this avd user, first deleting the relative AVD
                LOGGER.debug('Start to creating AVD user')

                # if the country is USA, then create timezone for AVD
                if 'united states' in country.lower():
                    user_avd = UserAvd.objects.create(
                        user=User.objects.all().first(),
                        name=avd_name,
                        port=port,
                        proxy_type="CYBERGHOST",
                        country=country,
                        timezone=random.choice(US_TIMEZONE),
                    )
                else:
                    user_avd = UserAvd.objects.create(
                        user=User.objects.all().first(),
                        name=avd_name,
                        port=port,
                        proxy_type="CYBERGHOST",
                        country=country
                    )
                self.create_avd(user_avd.name)        
                LOGGER.debug(f'AVD USER: {user_avd}')

                breakpoint()
                # tb = TwitterBot('android_368')
                tb = InstaBot(user_avd.name)
                tb.check_apk_installation()
                # Connect vpn
                if not self.no_vpn:
                    time.sleep(10)
                    if not tb.connect_to_vpn(country=country):
                        raise Exception("Couldn't able to connect Cyberghost VPN")
            
                accounts_created_bool= tb.create_account()
                # time.sleep(300)

                if accounts_created_bool:
                    tb.follow_rio()
                    accounts_created += 1

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
            except sel_ex.WebDriverException as f:
                print(f)
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
        self.total_accounts_created = 0
        self.avd_pack = []
        # if UserAvd.objects.all().count() >= 500:
        #     return "Cannot create more than 500 AVDs please delete existing to create a new one."

        required_accounts = int(options.get('n'))

        self.no_vpn = options.get('no_vpn')
        self.parallel_number = options.get('parallel_number')

        self.run_times = options.get('run_times')
        LOGGER.debug(f'Run times: {self.run_times}')
        requied_account_list = [n.size for n in
                                np.array_split(np.array(range(required_accounts)), self.parallel_number)]
        while True:
            try:
                with futures.ThreadPoolExecutor(max_workers=self.parallel_number) as executor:
                    for i in range(self.parallel_number):
                        executor.submit(self.run_tasks, requied_account_list[i])
            except Exception as e : print(e)
        print(f" All created UserAvd and TwitterAccount ****\n")
        
        random_sleep(10, 30)

    def clean_bot(self, tb, is_sleep=True):
        LOGGER.debug('Quit app driver and kill bot processes')
        #  tb.app_driver.quit()
        tb.kill_bot_process(appium=False, emulators=True)
        if is_sleep:
            random_sleep(60, 80)