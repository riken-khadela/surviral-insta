import sys
import time, os,shutil, tempfile, threading
from concurrent import futures
from xml.dom import UserDataHandler
from maill import SendErrorMail
import numpy as np
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from conf import US_TIMEZONE, PARALLEL_NUMER, MIN_HARD_DISK_FREE_SPACE, MAX_ACTIVE_ACCOUNTS, MIN_ACTIVE_ACCOUNTS
from core.models import User, user_detail
from twbot.models import User_details
from exceptions import PhoneRegisteredException, CannotRegisterThisPhoneNumberException, GetSmsCodeNotEnoughBalance
from twbot.bot import *
from twbot.utils import delete_avd_by_name
from django.db import connections
from django.core.management import call_command

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
        parser.add_argument(
            '--account_creation',
            nargs='?',
            default=False,
            type=bool,
            help=(f'Number of parallel running. Default: {PARALLEL_NUMER}'
                  '(PARALLEL_NUMER in the file conf.py)')
        )
        parser.add_argument(
            '--venv_activate_path',
            nargs='?',
            default=f'{BASE_DIR}/env/bin/activate',
            help=('The path of "bin/activate" for python virtual environment. '
                  f'Default: {BASE_DIR}/env/bin/activate'),
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
                LOGGER.info(e)
                self.create_avd_object(avdname)

            LOGGER.debug(f'AVD USER: {user_avd}')
            
            
            LOGGER.info(f"**** AVD created with name2222: {avdname} ****")
            return user_avd


    def handle(self, *args, **options):
        call_command('update_csv')
        call_command('delete_avd')
        for root, dirs, files in os.walk(os.getcwd()):
            for file in files:
                if file.endswith('.pyc'):
                    pyc_file_path = os.path.join(root, file)
                    os.remove(pyc_file_path)
        self.no_vpn = options.get('no_vpn')
        self.parallel_number = options.get('parallel_number')
        self.venv_activate_path = options.get("venv_activate_path")
        self.account_creation = options.get("account_creation")
        if not os.getenv("SYSTEM_NO") :
            SendErrorMail(subject='The SYSTEM number could not found')
            return
        self.random_cron_time_for_reboot()
        self.change_cron_time_for_auto_manage()
        LOGGER.info(f'\n\n\n--- PC number : {os.getenv("SYSTEM_NO")}\n\n\n')
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        
        LOGGER.info(f'\n\n\n--- PC number : {current_file_path}\n\n\n')
        self.total_accounts_created = 0
        self.avd_pack = []
        # if UserAvd.objects.all().count() >= 500:
        #     return "Cannot create more than 500 AVDs please delete existing to create a new one."


        
        LOGGER.info(1)
        self.run_times = options.get('run_times')
        LOGGER.debug(f'Run times: {self.run_times}')
        while True:
            with futures.ThreadPoolExecutor(max_workers=self.parallel_number) as executor:
                for i in range(self.parallel_number):
                    executor.submit(self.run_tasks,i)
            LOGGER.info(f" All created UserAvd and TwitterAccount ****\n")
        
        # random_sleep(10, 30)


    def run_tasks(self,i):
        try:
            old_pc = ['PC3','PC8','PC11','PC20','PKPC16','PKPC17','RK']
            if self.account_creation and not os.environ.get("SYSTEM_NO") in old_pc :
                account_thread = threading.Thread(target=self.create_accounts_if_not_enough)
                account_thread.start()
            if os.environ.get("SYSTEM_NO") in old_pc :
                self.no_vpn = True
            while True:
                connection.connect()
                csv_path = os.path.join(os.getcwd(),'csv','this_pc_avd.csv')
                from datetime import datetime
                all_users = []
                df = pd.DataFrame()
                
                if os.path.exists(os.path.join(os.getcwd(),'csv','this_pc_avd.csv')) :
                    df = pd.read_csv(csv_path)  
                    shuffled_df = df.sample(frac=1).reset_index(drop=True)
                    enged_date_times_li = [datetime.strptime(dt, '%Y-%m-%d %H:%M:%S.%f%z') for dt in shuffled_df['eng_at'].tolist()]
                    sorted_user_li = sorted(enged_date_times_li)
                    user_data_dict = shuffled_df.to_dict(orient='records')
                    all_users = [user_data_dict[enged_date_times_li.index(user)] for user in sorted_user_li]
                    
                    
                if not all_users :
                    all_users = list(User_details.objects.filter(status='ACTIVE').order_by('?'))
                
                random.shuffle(all_users)
                for userr in all_users:
                    if df.empty :
                        userr_avd = UserAvd.objects.filter(name=userr.avdsname).first()
                    else :
                        userr_avd = UserAvd.objects.filter(id=userr['avd_id']).first()
                        userr = User_details.objects.filter(username=userr['username']).first()
                        
                    print(111)
                    avd_list = subprocess.check_output(['emulator', '-list-avds'])
                    avd_list = [avd for avd in avd_list.decode().split("\n") if avd]
                    print(111)
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
                            if not tb.connect_to_vpn(country=userr_avd.country):
                                raise Exception("Couldn't able to connect Cyberghost VPN")
                            
                        
                        if tb.login(userr.username,userr.password) :
                            tb.send_views(AGENT,comment=comment)
                            

                    except GetSmsCodeNotEnoughBalance as e:
                        LOGGER.debug('Not enough balance in GetSMSCode')
                        tb.kill_bot_process(True, True)
                        sys.exit(1)
                    except Exception as e:
                        LOGGER.info(traceback.format_exc())
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
        
                    time.sleep(random.randint(80,100))
        except Exception as e :
            LOGGER.info(e) 

        finally : 
            LOGGER.info('The script is closed !')
            connections['default'].close()
    def create_accounts_if_not_enough(self):
        """ """
        while True :
            # Create new accounts if existing accounts are not enough
            try:
                total, used, free = shutil.disk_usage("/")
                free_in_gb = free // (2 ** 30)
                total_in_gb = total // (2 ** 30)
                used_in_gb = used // (2 ** 30)
                if free_in_gb < MIN_HARD_DISK_FREE_SPACE:
                    LOGGER.info(
                        f"Your hard disk free space less than {MIN_HARD_DISK_FREE_SPACE} so skipping account creation")
                    return
                
                # active_accounts = User_details.objects.filter(status='ACTIVE',avd_pc = os.getenv("SYSTEM_NO"))
                active_accounts = User_details.objects.filter(status='ACTIVE')
                LOGGER.info(f"Total Active accounts: {active_accounts.count()}")
                if active_accounts.count() < MIN_ACTIVE_ACCOUNTS :
                    LOGGER.debug(
                        f"Active accounts are less than {MIN_ACTIVE_ACCOUNTS} of required accounts so running "
                        f"account creation")
                    accounts_to_create = int(min((free_in_gb - MIN_HARD_DISK_FREE_SPACE )/10, MAX_ACTIVE_ACCOUNTS))
                    shell_cmd = f". {self.venv_activate_path} && {BASE_DIR}/manage.py create_accounts " \
                                f"-n {accounts_to_create} --parallel_number {self.parallel_number}"
                    subprocess.run(shell_cmd, check=True, shell=True)
                else:
                    LOGGER.debug("Active accounts more than maximum number of required accounts so skipping account creation")
            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                LOGGER.debug(e)
    
    @staticmethod
    def random_cron_time_for_reboot():
        LOGGER.info('Create random time to the one after reboot in crontab for auto_engage')
        cmd = 'auto_manage'
        cmds = 'crontab -l'
        verbose = True
        result = run_cmd(cmds, verbose=verbose)
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        current_file_path = current_file_path.replace('/twbot/management/commands','')
        
        if result:
            (returncode, output) = result
            #  LOGGER.info(output)
            outs = output.strip().split('\n')
            outs_all = [e + '\n' for e in outs]
            effective_outs = [ e + '\n' for e in outs if not e.strip().startswith('#')]
            if 'no crontab for' in output:
                #  outs_all = ['\n']
                outs_all = []
                effective_outs = []
            exist_flag = False
            exist_job = ''
            for item in effective_outs:
                if cmd in item :
                    LOGGER.info(f'There has already been one job for command {cmd}')
                    exist_flag = True
                    exist_job = item
                    break
            
            if exist_flag:
                LOGGER.info(f'Override the existing job: {exist_job}')
                
                outs_all.remove(exist_job) if exist_job in outs_all else ...

                if exist_job.strip().startswith('@'):
                    if 'sleep' in exist_job:
                        LOGGER.info('The cron job starts with @ and with a command sleep, now ignore it')
                        return True
                
            new_job_parts = ['@reboot', 'sleep', '300', '&&', '/bin/bash',os.path.join(current_file_path,'tasks/auto_manage.sh'), '>>', os.path.join(current_file_path,'tasks/auto_manage.log'), '2>&1']
            new_job = ' '.join(new_job_parts) + '\n'
            LOGGER.info(f'New crontab job: {new_job}')
            
            outs_all.append(new_job)
            jobs_text = ''.join(outs_all)
            LOGGER.info(jobs_text)
            with tempfile.NamedTemporaryFile(mode='w+t') as fp:
                LOGGER.info(f'Write jobs to file {fp.name}')
                fp.write(jobs_text)
                fp.flush()
                # import crontab job
                cmds = f'crontab {fp.name}'
                verbose = True
                result = run_cmd(cmds, verbose=verbose)
                if result:
                    (returncode, output) = result
                    if returncode == 0:
                        LOGGER.info('Imported jobs into crontab')
                    else:
                        LOGGER.info('Failed to import jobs into crontab')
                else:
                    LOGGER.info('Cannot importe jobs into crontab')
                #  LOGGER.info(new_output)
        else:
            LOGGER.info('Cannot get crontab jobs')
    
    @staticmethod
    def change_cron_time_for_auto_manage():
        """ """
        LOGGER.info('Create random time in crontab for auto_engage')
        cmd = 'auto_manage'
        cmds = 'crontab -l'
        verbose = True
        result = run_cmd(cmds, verbose=verbose)
        if result:
            (returncode, output) = result
            #  LOGGER.info(output)
            outs = output.strip().split('\n')
            outs_all = [e + '\n' for e in outs]
            effective_outs = [
                e + '\n' for e in outs if not e.strip().startswith('#')]
            if 'no crontab for' in output or output == '':
                #  outs_all = ['\n']
                outs_all = []
                effective_outs = []
            exist_flag = False
            exist_job = ''
            for item in effective_outs:
                if cmd in item and not '@' in item:
                    LOGGER.info(f'There has already been one job for command {cmd}')
                    exist_flag = True
                    exist_job = item
                    break

            if exist_flag:
                LOGGER.info(f'Override the existing job: {exist_job}')
                outs_all.remove(exist_job)
                exist_job_parts = exist_job.strip().split()
                m = random.randint(0, 59)
                h = random.randint(12,24)

                exist_job_parts[0] = f'{m}'
                exist_job_parts[1] = f'*/{h}'
                new_job = ' '.join(exist_job_parts) + '\n'
                LOGGER.info(f'New crontab job: {new_job}')

                outs_all.append(new_job)
            else :
                current_file_path = os.path.dirname(os.path.abspath(__file__))
                current_file_path = current_file_path.replace('/twbot/management/commands','')
                exist_job_parts = ['*','*','*','*','*','/bin/bash',os.path.join(current_file_path,'tasks/auto_manage.sh'),'>>',os.path.join(current_file_path,'tasks/auto_manage.log'),'2>&1']
                m = random.randint(0, 59)

                if exist_job_parts[1] != '*':
                    original_hour = int(exist_job_parts[1])
                else:
                    original_hour = random.randint(0, 8)
                # next_hour = (original_hour + 8) % 24
                # ho = next_hour + random.randint(5,8) 

                # if not ho < 8 :
                ho = random.randint(5,8)
                exist_job_parts[0] = f'*/{m}'
                exist_job_parts[1] = f'*/{ho}'
                new_job = ' '.join(exist_job_parts) + '\n'
                LOGGER.info(f'New crontab job: {new_job}')

                outs_all.append(new_job)
                ...
            jobs_text = ''.join(outs_all)
            LOGGER.info(jobs_text)
            with tempfile.NamedTemporaryFile(mode='w+t') as fp:
                #  LOGGER.info(f'jobs_text: {jobs_text}')
                LOGGER.info(f'Write jobs to file {fp.name}')
                fp.write(jobs_text)
                fp.flush()
                # import crontab job
                cmds = f'crontab {fp.name}'
                verbose = True
                result = run_cmd(cmds, verbose=verbose)
                if result:
                    (returncode, output) = result
                    if returncode == 0:
                        LOGGER.info('Imported jobs into crontab')
                    else:
                        LOGGER.info('Failed to import jobs into crontab')
                else:
                    LOGGER.info('Cannot importe jobs into crontab')
                #  LOGGER.info(new_output)
        else:
            LOGGER.info('Cannot get crontab jobs')
    
    def clean_bot(self, tb, is_sleep=True):
        LOGGER.debug('Quit app driver and kill bot processes')
        #  tb.app_driver.quit()
        tb.kill_bot_process(appium=False, emulators=True)
        if is_sleep:
            random_sleep(10, 20)
