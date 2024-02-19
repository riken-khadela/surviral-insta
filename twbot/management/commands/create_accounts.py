import sys
import time
from concurrent import futures
import pandas as pd, os, shutil

import numpy as np
from django.core.management.base import BaseCommand
import selenium.common.exceptions as sel_ex

from conf import US_TIMEZONE, PARALLEL_NUMER, MIN_HARD_DISK_FREE_SPACE, MAX_ACTIVE_ACCOUNTS, MIN_ACTIVE_ACCOUNTS
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
        # ...
        LOGGER.debug('Start to creating AVD user')
        twbot = InstaBot(emulator_name=avdname, start_appium=False, start_adb=False)
        device = random.choice(AVD_DEVICES)  # get a random device
        # package = random.choice(AVD_PACKAGES)  # get a random package
        twbot.create_avd(avd_name=avdname,device=device)
        LOGGER.info(f"**** AVD created with name1111: {avdname} ****")
        return avdname

    def run_tasks(self, required_accounts,country):
        count = 0
        accounts_created = 0
        used_ports = set(UserAvd.objects.values_list('port', flat=True))
        self.ports = [30000 + x for x in range(1, 4000) if (3000 + x) not in used_ports]
        used_name = set(User_details.objects.values_list('avdsname', flat=True))
        self.devices = [f"instagram_50{x}" for x in range(1,90000) if f"instagram_{x}" not in used_name]
        # for avd_name  in self.devices:
        random.shuffle(country)
        list_ = self.create_list(1,country,required_accounts)
        delete_avd = []
        while accounts_created < required_accounts :
            if delete_avd:
                for i in delete_avd:
                    avdname = i.name
                    i.delete()
                    try:
                        subprocess.check_output(['avdmanager', 'delete', 'avd', '-n', avdname])
                        print("Successfully deleted AVD:", avdname)
                    except subprocess.CalledProcessError as e:
                        print(f"Error deleting AVD {avdname}: {e}")
                    except Exception as e:
                        print(f"Unexpected error: {e}")

                delete_avd.clear()
            total, used, free = shutil.disk_usage("/")
            free_in_gb = free // (2 ** 30)
            if free_in_gb < MIN_HARD_DISK_FREE_SPACE:
                LOGGER.info(
                    f"Your hard disk free space less than {MIN_HARD_DISK_FREE_SPACE} so skipping account creation")
                return
            
            # else:break
            # fix the error
            # psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint "twbot_useravd_port_key"
            # DETAIL:  Key (port)=(5794) already exists.
            start_time = time.time()
            port = random.choice(self.ports)*(random.randint(100,999))
            avd_name = random.choice(self.devices)
            print(avd_name)
            
            LOGGER.info(f'available avdname len is {len(self.devices)}')
            LOGGER.info(f'available ports len is {len(self.ports)}')
            # avd_name = random.choice(self.devices)
            # ...
            print(1111)
            if User_details.objects.filter(avdsname= avd_name).exists():
                continue
            print(2222)
            if UserAvd.objects.filter(name = avd_name).exists():
                continue
            print(3333)
            avd_list = subprocess.check_output(['emulator', '-list-avds'])
            avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
            if avd_name  in avd_list:
                continue
            # create all accounts in USA
            counrty_code_dict = {
                    'China' : "china"
                    ,'Hong Kong' : "hk"
                    ,'Indonesia' : "id"
                    # ,'Philippines' : "ph"
                    # ,'Kenya' : "kn"

                }
            countrys = list_.pop(0)
            if type(countrys) == list :
                country = random.choice(countrys)
            country_code = counrty_code_dict[country]
            LOGGER.debug(f'country: {country}')
            try:
                # if UserAvd.objects.filter(name=avd_name).exists(): continue
                
                # create an avd user, at the same time, creat the relative AVD
                # before deleting this avd user, first deleting the relative AVD
                LOGGER.debug('Start to creating AVD user')
                print('-----')

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
                print('-----')

                # tb = TwitterBot('android_368')
                tb = InstaBot(user_avd.name)
                tb.check_apk_installation()
                # Connect vpn
                if not self.no_vpn:
                    time.sleep(10)
                    if not tb.connect_urban(country=country):
                        delete_avd.append(user_avd)
                        raise Exception("Couldn't able to connect Cyberghost VPN")
            
                created_user_obj, user_obj_bool, number_not_found = tb.create_account(country_code=country_code)
                if number_not_found != '' and number_not_found == "number_not_found":
                    self.country.remove(country)
                if user_obj_bool == False or created_user_obj == "delete_avd" :
                    self.clean_bot(tb, False)
                    user_avd.delete()
                    
                elif created_user_obj or user_obj_bool == True :
                    csv_path = os.path.join(os.getcwd(),'csv','this_pc_avd.csv')
                    if not os.path.exists(csv_path) :
                        headers = ['avd_id','user_id','Avdsname','username','created_at','eng_at']  # Add your column names here
                        df = pd.DataFrame(columns=headers)
                    else :
                        df = pd.read_csv(csv_path)
                        
                    df.loc[len(df.index)] = [user_avd.id,created_user_obj.id,user_avd.name,created_user_obj.username,created_user_obj.created_at,created_user_obj.created_at]
                    df.to_csv(csv_path,index=False)
                        
                    accounts_created += 1
                

            except GetSmsCodeNotEnoughBalance as e:
                LOGGER.debug('Not enough balance in GetSMSCode')
                tb.kill_bot_process(True, True)
                sys.exit(1)
            except Exception as e:
                print(e,'-------')
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
        # self.parallel_number = 1
        
        
        self.country = ['China','Hong Kong','Indonesia','Philippines']
        # self.country = ['Indonesia','Philippines']
        # self.country = ['China']
        # self.country = ['Indonesia','Philippines']
        self.run_times = options.get('run_times')
        LOGGER.debug(f'Run times: {self.run_times}')
        requied_account_list = [n.size for n in
                                np.array_split(np.array(range(required_accounts)), self.parallel_number)]
        
        while True:
            try:
                with futures.ThreadPoolExecutor(max_workers=self.parallel_number) as executor:
                    for i in range(self.parallel_number):
                        # if 'China' in self.country :
                        #     executor.submit(self.run_tasks, requied_account_list[i],'China')
                        #     self.country.remove('China')
                        # else :
                        executor.submit(self.run_tasks, requied_account_list[i],self.country)
                            
            except Exception as e : print(e)
            LOGGER.debug(f" All created UserAvd and TwitterAccount ****\n")
        
        random_sleep(10, 30)

    def clean_bot(self, tb, is_sleep=True):
        LOGGER.debug('Quit app driver and kill bot processes')
        #  tb.app_driver.quit()
        tb.kill_bot_process(appium=False, emulators=True)
        if is_sleep:
            random_sleep(60, 80)
            
    def create_list(self, num_threads,links,loop):
        main_list = []
        duplicate_list = links[:]
        for i in range(loop):
            nested_list= []
            for i in range(num_threads):
                if not duplicate_list:
                    duplicate_list = links[:]
                    nested_list.append(duplicate_list.pop(0))
                else:
                    nested_list.append(duplicate_list.pop(0))
            main_list.append(nested_list)
        return main_list