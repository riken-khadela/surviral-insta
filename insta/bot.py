from conf import *
import pandas as pd, parallel, numpy as np, random, subprocess, time, os
from dotenv import load_dotenv
from main import LOGGER
from insta.models import UserAvd
from surviral.settings import BASE_DIR
from ppadb.client import Client as AdbClient
from utils import run_cmd, get_installed_packages
from faker import Faker
from surviral import settings 

class InstaBot:
    def __init__(self, emulator_name, start_appium=True, start_adb=True,
                 appium_server_port=APPIUM_SERVER_PORT, adb_console_port=None):
        self.user = ''
        self.emulator_name = emulator_name
        load_dotenv()
        self.user_avd = UserAvd.objects.using('on_pc').filter(name=emulator_name).first()
        
        if not self.user_avd:
            self.user_avd = UserAvd.objects.filter(name=emulator_name).first()
        # if not self.user_avd:
        #     UserAvd.objects.filter(name=emulator_name).first()
        # breakpoint()
        self.logger = LOGGER
        #  self.kill_bot_process(appium=True, emulators=True)
        self.app_driver = None
        try:
            self.df = pd.read_csv(f'{BASE_DIR}/delete_avd.csv')
        except FileNotFoundError:
            self.df = pd.DataFrame(columns=['avd'])
            self.df.to_csv('delete_avd.csv', index=False)
        try:
            self.today_avd = pd.read_csv(f'{BASE_DIR}/today_avd.csv')
        except FileNotFoundError:
            self.today_avd = pd.DataFrame(columns=['avd'])
            self.today_avd.to_csv('today_avd.csv', index=False)


        #  self.emulator_port = None
        #  self.service = self.start_appium(port=4724) if start_appium else None
        self.adb = AdbClient() if start_adb else None
        self.device = None
        self.get_device_retires = 0
        self.start_driver_retires = 0
        

        self.wait_time = WAIT_TIME

        # parallel running configration
        self.appium_server_port = appium_server_port
        if not parallel.get_listening_adb_pid():
            run_cmd('adb start-server')
        parallel.start_appium(port=self.appium_server_port)
        #  parallel.start_appium_without_exit()
        if not adb_console_port:
            self.adb_console_port = str(
                parallel.get_one_available_adb_console_port())
            self.system_port = str(parallel.get_one_available_system_port(
                int(self.adb_console_port)))
        else:
            self.adb_console_port = adb_console_port
        self.system_port = str(parallel.get_one_available_system_port(
            int(self.adb_console_port)))
        self.emulator_port = self.adb_console_port
        self.parallel_opts = self.get_parallel_opts()
        fake = Faker()
        seed=None
        np.random.seed(seed)
        fake.seed_instance(seed)
        self.gender =np.random.choice(["male", "female"], p=[0.5, 0.5])
        self.fname =  fake.first_name_male() if "gender"=="male" else fake.first_name_female()
        self.lname =  fake.last_name()
        self.password = self.fname+'@1234'
        self.full_name = self.fname + self.lname
        self.birth_year = str(random.randint(1990,2003))
        self.birth_date = str(random.randint(1,28))
        if len(self.birth_date)==1:
            self.birth_date = f"0{self.birth_date}"
        # birth_month_li = ['January','February','March','April','May','June','July','August','September','October','November', 'December']
        birth_month_li = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov', 'Dec']
        self.birth_month = random.choice(birth_month_li)


    @staticmethod
    def create_avd(avd_name, package=None, device=None):
        default_package = "system-images;android-28;default;x86"

        try:
            if not package:
                cmd = f'avdmanager create avd --name {avd_name} --package "{default_package}"'
                package = default_package
            else:
                cmd = f'avdmanager create avd --name {avd_name} --package "{package}"'

            if device:
                #  cmd += f" --device {device}"
                cmd += f" --device \"{device}\""

            # install package
            if package not in get_installed_packages():
                LOGGER.info(f'Install or update package: {package}')
                cmd1 = f'sdkmanager "{package}"'
                p = subprocess.Popen(cmd1, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, shell=True, text=True)
                # print live output
                while True:
                    output = p.stdout.readline()
                    if p.poll() is not None:
                        break
                    if output:
                        print(output.strip())

            LOGGER.info(f'AVD command: {cmd}')
            #  result = run_cmd(cmd)
            #  return result
            p = subprocess.Popen(
                [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
            )
            time.sleep(1)
            p.communicate(input=b"\n")
            p.wait()
            # breakpoint()
            updated_config = os.path.join(settings.BASE_DIR, 'twbot/avd_config/config.ini')
            new_config_file = f"{settings.AVD_DIR_PATH}/{avd_name}.avd/config.ini"
            LOGGER.debug(f'updated_config: {updated_config}')
            LOGGER.debug(f'new_config_file: {new_config_file}')
            if os.path.isdir(f"{settings.AVD_DIR_PATH}/{avd_name}.avd") and os.path.isfile(new_config_file):
                # os.replace(updated_config, new_config_file)
                from shutil import copyfile
                copyfile(updated_config, new_config_file)
            return True

        except Exception as e:
            LOGGER.error(e)
            return False