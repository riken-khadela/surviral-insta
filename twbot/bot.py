import difflib
import random
import psycopg2
from dotenv import load_dotenv
from faker import Faker
from pathlib import Path
from datetime import date
import faker
import pandas as pd
from surviral_avd import settings
import numpy as np
from xml.etree.ElementTree import Comment
from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from appium.webdriver.common.touch_action import TouchAction
from numpy import number
from ppadb.client import Client as AdbClient
from selenium.common.exceptions import InvalidSessionIdException
from selenium.webdriver.common.keys import Keys
from core.models import user_detail
from twbot.models import User_details, postdetails
import parallel
from django.db import connection
import weakref
from gender_guesser import detector
import random, names
from conf import APPIUM_SERVER_HOST, APPIUM_SERVER_PORT, US_TIMEZONE
from conf import TWITTER_VERSIONS
from conf import WAIT_TIME
from constants import COUNTRY_CODES
from exceptions import CannotStartDriverException
from twbot.models import *
from twbot.utils import *
from twbot.vpn.nord_vpn import NordVpn
from utils import get_installed_packages
from utils import run_cmd
from .utils import phone_numbers, GetInstaComments, INSTA_PROFILE_BIO_LIST, random_insta_bio
timeout = 10


def random_sleep(min_sleep_time=1, max_sleep_time=5,reason=''):
    sleep_time = random.randint(min_sleep_time, max_sleep_time)
    if not reason:LOGGER.debug(f'Random sleep: {sleep_time}')
    else:LOGGER.debug(f'Random sleep: {sleep_time} for {reason}')
    time.sleep(sleep_time)
    
class button_name:
    change_profile_pic = "Change profile photo"
    follow = "Follow"
    ok = "OK"
    edit_profile = "Edit profile"
    not_now = "Not now"
    

class InstaBot:
    def __init__(self, emulator_name,user_avd_obj='', start_appium=True, start_adb=True,
                 appium_server_port=APPIUM_SERVER_PORT, adb_console_port=None):
        self.user = ''
        self.emulator_name = emulator_name
        load_dotenv()
        if user_avd_obj :
            self.user_avd = user_avd_obj
        else :
            self.user_avd = UserAvd.objects.filter(name=emulator_name).first()
        self.logger = LOGGER
        #  self.kill_bot_process(appium=True, emulators=True)
        self.app_driver = None
        try:
            self.df = pd.read_csv('delete_avd.csv')
        except FileNotFoundError:
            self.df = pd.DataFrame(columns=['avd'])
            self.df.to_csv('delete_avd.csv', index=False)
        
        # try:
        #     self.random = pd.read_csv('random.csv')
        # except FileNotFoundError:
        #     self.random = pd.DataFrame(columns=['postdetails','like','date'])
        #     self.random.to_csv('random.csv',index=False)
            
        try:
            self.today_avd = pd.read_csv('today_avd.csv')
        except FileNotFoundError:
            self.today_avd = pd.DataFrame(columns=['avd'])
            self.today_avd.to_csv('today_avd.csv', index=False)

        #  self.emulator_port = None
        #  self.service = self.start_appium(port=4724) if start_appium else None
        self.adb = AdbClient() if start_adb else None
        self.device = None
        self.get_device_retires = 0
        self.start_driver_retires = 0
        log_activity(
            self.user_avd.id,
            action_type="IntaBotini",
            msg=f"Initiated InstaBot instance with {self.user_avd.name}",
            error=None,
        )

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
        weakref.finalize(self, self.__del__)
        


    def __del__(self):
        '''
        Close the driver and activity
        '''
        if hasattr(self, 'app_driver'):
            self.driver().quit()

    @property
    def wait_obj(self):
        """Used for waiting certain element appear"""
        return WebDriverWait(self.driver(), self.wait_time)

    def get_parallel_opts(self):
        return {
            'appium:avd': self.emulator_name,
            'appium:avdArgs': ['-port', str(self.adb_console_port)] + self.get_avd_options(),
            'appium:systemPort': self.system_port,
            'appium:noReset': True,
            # 'appPackage': 'com.instagram.android',
            # 'appActivity': 'com.instagram.android.activity.MainTabActivity'
            #  'appium:skipLogCapture': True,
        }
        
        # driver = webdriver.Remote(http://127.0.0.1:4724/wd/hub/session/:sessionId/cookie,desired_caps)
    
    def start_appium(self, port):
        # start appium server
        LOGGER.debug(f'Start appium server, port: {port}')
        server = AppiumService()
        server.start(
            args=["--address", "127.0.0.1", "-p", str(port), "--session-override"]
        )
        if server.is_running and server.is_listening:
            log_activity(
                self.user_avd.id,
                action_type="StartAppiumServer",
                msg=f"Started Appium server for {self.user_avd.name}",
                error=None,
            )
            return server
        else:
            log_activity(
                self.user_avd.id,
                action_type="StartAppiumServer",
                msg=f"Failed to start Appium server for {self.user_avd.name}",
                error=f"server status is not running and listening.",
            )
            return False

    def create_avd_object(self,avdname):
        LOGGER.debug('Start to creating AVD user')
        used_ports = set(UserAvd.objects.values_list('port', flat=True))
        port_range = range(1, 10000)
        port = next((1000 + port for port in port_range if (1000 + port) not in used_ports), None)
        if port is not None:

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

    def get_avd_options(self):
        emulator_options = [
            #  '-phone-number', str(self.phone) if self.phone else '0',
        ]

        if self.user_avd.timezone:
            emulator_options += ['-timezone', f"{self.user_avd.timezone}"]
        LOGGER.debug(f'Other options for emulator: {emulator_options}')
        return emulator_options

    def get_device(self):
        name = self.emulator_name

        if self.get_adb_device():
            self.get_device_retires = 0
            # self.get_adb_device().wait_boot_complete(timeout=100)
        else:
            self.device = False
            if self.get_device_retires >= 3:
                log_activity(
                    self.user_avd.id,
                    action_type="StartAvd",
                    msg=f"Failed to start AVD for {self.user_avd.name}",
                    error="Couldn't get device",
                )
                raise Exception("Couldn't get device.")

            self.get_device_retires += 1

            # kill all running devices/emulators
            print("killed in get_device")
            self.kill_bot_process(emulators=True)
            time.sleep(2)
            self.get_device()

        return self.device
# desired_caps = {'platformName': 'Android','deviceName': 'instagram_2972','appPackage': 'com.instagram.android','appActivity': 'com.instagram.android.activity.MainTabActivity','automationName': 'UiAutomator2'}
    def check_apk_installation(self):
        LOGGER.debug('Check if apk is installed')
        vpn = CyberGhostVpn(self.driver())
        if vpn.is_app_installed():
            vpn.terminate_app()

        LOGGER.debug('Check if cyberghost is installed')
        if not self.driver().is_app_installed('de.mobileconcepts.cyberghost'):
            cmd = f"adb -s emulator-{self.adb_console_port} install -t -r -d -g {os.path.join(BASE_DIR, 'apk/cyberghost.apk')}"
            p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
            p.wait()
        
        LOGGER.debug('Check if instagram is installed')
        if not self.driver().is_app_installed("com.instagram.android"):
            LOGGER.debug('instagram is not installed, now install it')
            self.install_apk(self.adb_console_port, "instagram")
            LOGGER.info('instagram app installed successfully')
            
        else:
            LOGGER.debug('Check instagram version')
            apk_version = self.get_apk_version('com.instagram.android')
            random_sleep()
            if apk_version != '273.1.0.16.72':
                LOGGER.debug('Install instagram new version')
                self.Install_new_insta()
            else:
                self.driver().terminate_app('com.instagram.android')

        if self.driver().is_app_installed('com.windscribe.vpn'):
            self.driver().remove_app('com.windscribe.vpn')
            
        try:
            command = f"adb -s emulator-{self.adb_console_port} shell rm -r /sdcard/Download/*"
            subprocess.run(command, shell=True, check=True)
        except Exception as e:
            print(e)
        #     LOGGER.info('install windscribe')
        #     cmd = f"adb -s emulator-{self.adb_console_port} install -t -r -d -g {os.path.join(BASE_DIR, 'apk/windscribe-2.apk')}"
        #     p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
        #     p.wait()
        # else:
        #     self.driver().terminate_app('com.windscribe.vpn')
    
    def clear_app_tray(self):
        try:
            output = subprocess.check_output(["adb", '-s',f'emulator-{self.adb_console_port}',"shell", "dumpsys", "activity", "recents"], universal_newlines=True)
            lines = output.split('\n')
            stack_ids = []
            stack_ids = [int(line.split("StackId=")[1].split(" ")[0]) for line in lines if "StackId=" in line]
            stack_ids = [id for id in stack_ids if int(id)!= 0 and int(id) !=-1]
            LOGGER.info("Found StackIds:", stack_ids)
            if stack_ids:
                for stack_id in stack_ids:
                    LOGGER.info(f"Removing StackId: {stack_id}")
                    subprocess.run(["adb", '-s',f'emulator-{self.adb_console_port}',"shell", "am", "stack", "remove", str(stack_id)])
                    LOGGER.info(f"Removed StackId: {stack_id}")
        except Exception as e:
            print("Error:", str(e))
        
    def get_adb_device(self):
        #  LOGGER.debug('Get adb device')
        for x in range(20):
            if self.adb.devices():
                try:
                    response = self.adb.devices()[0].shell("getprop sys.boot_completed | tr -d '\r'")
                    if "1" in response:
                        self.emulator_port = self.adb.devices()[0].serial.split("-")[-1]
                        return self.adb.devices()[0]
                except Exception as e:
                    #  print(e)
                    LOGGER.error(e)
            time.sleep(x)

    def start_driver(self):
       
        try:
            opts = {
                "platformName": "Android",
                #  "platformVersion": "9.0",    # comment it in order to use other android version
                "automationName": "UiAutomator2",
                "noSign": True,
                "noVerify": True,
                "ignoreHiddenApiPolicyError": True,
                # "appWaitDuration": 10000
            }
            opts.update(self.parallel_opts)

            #  LOGGER.debug('Start appium driver')
            LOGGER.debug(f'Driver capabilities: {opts}')
            LOGGER.debug(f"Driver url: http://{APPIUM_SERVER_HOST}:{self.appium_server_port}/wd/hub")

            self.app_driver = webdriver.Remote(
                f"http://{APPIUM_SERVER_HOST}:{self.appium_server_port}/wd/hub",
                desired_capabilities=opts,
                #  keep_alive=True,
            )
            self.start_driver_retires = 0
            log_activity(
                self.user_avd.id,
                action_type="ConnectAppium",
                msg=f"Driver started successfully",
                error=None,
            )
        except Exception as e:
            LOGGER.warning(type(e))
            LOGGER.warning(e)
            # if 'driver' in globals():
            #     self.app_driver.close()
            if not parallel.get_avd_pid(name=self.emulator_name,
                                        port=self.adb_console_port):
                self.adb_console_port = str(
                    parallel.get_one_available_adb_console_port())
                adb_console_port = self.adb_console_port
            else:
                adb_console_port = str(
                    parallel.get_one_available_adb_console_port())
            self.system_port = str(parallel.get_one_available_system_port(
                int(adb_console_port)))
            self.parallel_opts = self.get_parallel_opts()
            if not parallel.get_listening_adb_pid():
                run_cmd('adb start-server')

            
            parallel.start_appium(port=self.appium_server_port)

            tb = traceback.format_exc()
            if self.start_driver_retires > 5:
                LOGGER.info("================ Couldn't start driverCouldn't start driver")
                log_activity(
                    self.user_avd.id,
                    action_type="ConnectAppium",
                    msg=f"Error while connecting with appium server",
                    error=tb,
                )
                raise CannotStartDriverException("Couldn't start driver")
            #  print("killed in start_driver")
            #  self.kill_bot_process(True, True)
            #  self.service = self.start_appium(port=4724)

            self.start_driver_retires += 1
            LOGGER.info(f"appium server starting retries: {self.start_driver_retires}")
            log_activity(
                self.user_avd.id,
                action_type="ConnectAppium",
                msg=f"Error while connecting with appium server",
                error=f"Failed to connect with appium server retries_value: {self.start_driver_retires}",
            )
            self.driver()

    def driver(self):
        try:
            if not self.app_driver:
                self.start_driver()
            session = self.app_driver.session
        except CannotStartDriverException as e:
            raise e
        except Exception as e:
            LOGGER.warning(e)
            self.start_driver()
        
        # self.coneect_db()
        return self.app_driver

    # def coneect_db(self):
    #     while True :
    #         try :
    #             postdetails.objects.first()
    #             break
    #         except Exception as e : 
    #             try:
    #                 connection.connect()
    #                 break
    #             except Exception as e:
    #                 print(f'Error: {e}')
    
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
            p = subprocess.Popen(
                [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
            )
            time.sleep(1)
            p.communicate(input=b"\n")
            p.wait()
            updated_config = os.path.join(settings.BASE_DIR, 'twbot/avd_config/config.ini')
            new_config_file = f"{settings.AVD_DIR_PATH}/{avd_name}.avd/config.ini"
            LOGGER.debug(f'updated_config: {updated_config}')
            LOGGER.debug(f'new_config_file: {new_config_file}')
            if os.path.isdir(f"{settings.AVD_DIR_PATH}/{avd_name}.avd") and os.path.isfile(new_config_file):
                from shutil import copyfile
                copyfile(updated_config, new_config_file)
            return True

        except Exception as e:
            LOGGER.error(e)
            return False
        
    def install_apk(self, port, app_name):
        try:
            if app_name.lower() == "reddit":
                cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/Reddit.apk')}"
                log_activity(
                    self.user_avd.id,
                    action_type="InstallRedditApk",
                    msg=f"Installation of Reddit apk",
                    error=None,
                )
                p = subprocess.Popen(
                    [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
                )
                p.wait()
            if app_name.lower() == "instagram":
                cmd = f"adb -s emulator-{port} install -g {os.path.join(BASE_DIR, 'apk/instagram.apk')}"
                log_activity(
                    self.user_avd.id,
                    action_type="InstallInstagramApk",
                    msg=f"Installation of instagram apk",
                    error=None,
                )
                p = subprocess.Popen(
                    [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
                )
                p.wait()
            elif app_name.lower() == "twitter":
                #  cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/twitter.apk')}"
                times = 0
                retry_times = 10
                apk_path = ''
                while times < retry_times:
                    twitter_version = random.choice(TWITTER_VERSIONS)
                    apk_path = os.path.join(BASE_DIR, f'apk/twitter_{twitter_version}.apk')
                    times += 1
                    if Path(apk_path).exists():
                        break

                if apk_path == '':
                    LOGGER.critical(f'Cannot find twitter apk, please'
                                    ' configure the versions in the file conf.py')
                    # use the defaut apk
                    apk_path = os.path.join(BASE_DIR, f'apk/twitter.apk')

                # get architecture of device
                arch = self.get_arch_of_device()
                if arch:
                    cmd = f"adb -s emulator-{port} install --abi {arch} {apk_path}"
                else:
                    cmd = f"adb -s emulator-{port} install {apk_path}"
                LOGGER.debug(f'Install cmd: {cmd}')
                log_activity(
                    self.user_avd.id,
                    action_type="InstallTwitterApk",
                    msg=f"Installation of twitter apk",
                    error=None,
                )
                p = subprocess.Popen(
                    [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
                )
                p.wait()
            elif app_name.lower() == "shadowsocks":
                cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/shadowsocks.apk')}"
                log_activity(
                    self.user_avd.id,
                    action_type="InstallShadowsockApk",
                    msg=f"Installation of shadowsocks apk",
                    error=None,
                )
                p = subprocess.Popen(
                    [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
                )
                p.wait()

            elif app_name.lower() == "nord_vpn":
                cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/nord_vpn.apk')}"
                LOGGER.debug(f'Install cmd: {cmd}')
                log_activity(
                    self.user_avd.id,
                    action_type="InstallNordVPNApk",
                    msg=f"Installation of NordVPN apk",
                    error=None,
                )
                p = subprocess.Popen(
                    [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
                )
                p.wait()
            else:
                return False

            return True
        except Exception as e:
            print(e)
            return False

    def kill_process(self, port):
        try:
            cmd = f"lsof -t -i tcp:{port} | xargs kill -9"
            p = subprocess.Popen(
                [cmd],
                stdin=subprocess.PIPE,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            log_activity(
                self.user_avd.id,
                action_type="KillProcess",
                msg=f"Kill process of given port: {port}",
                error=None,
            )
            return True
        except Exception as e:
            log_activity(
                self.user_avd.id,
                action_type="KillProcessError",
                msg=f"Failed to kill process of given port: {port}",
                error=traceback.format_exc(),
            )
            return False

    def kill_bot_process(self, appium=False, emulators=False):
        LOGGER.debug(f'Start to kill the AVD: {self.emulator_name}')
        if self.app_driver:
            LOGGER.info(f'Stop the driver session')
            try:
                self.driver().quit()
            except InvalidSessionIdException as e:
                LOGGER.info(e)

        name = self.emulator_name
        port = self.adb_console_port
        parallel.stop_avd(name=name, port=port)
    
    def connect_to_vpn(self, fail_tried=0, vpn_type='cyberghostvpn',
                       country='', city=""):
        if not country:
            country = self.user_avd.country
        if re.search("surfshark", str(country), re.I):
            country_code = country[:2]
            surf_shark_country = COUNTRY_CODES[country_code]
            nord_vpn_countries = difflib.get_close_matches(surf_shark_country, NordVpn.get_server_list())
            country = random.choice(nord_vpn_countries)
            self.user_avd.proxy_type = "CYBERGHOST"
            self.user_avd.country = country
            self.user_avd.save()

        if vpn_type == 'cyberghostvpn':
            if not country in CyberGhostVpn.get_server_list() :
                ghost_vpn_countries = difflib.get_close_matches(country, CyberGhostVpn.get_server_list())
                country = random.choice(ghost_vpn_countries)
            if not country:
                country = "United States"
            self.user_avd.proxy_type = "CYBERGHOST"
            self.user_avd.country = country
            self.user_avd.save()
            LOGGER.info('Connect to CyberGhost VPN')
            vpn = CyberGhostVpn(self.driver())
            reconnect = True
            #  country = 'United States' if not vpn_country else vpn_country
            return vpn.start_ui(reconnect=reconnect, country=country, city=city)
        else:
            LOGGER.debug('Connect to Nord VPN')
            vpn = NordVpn(self.driver(), self.user_avd)
            try:
                if vpn.connect_to_vpn(country, fail_tried=fail_tried):
                    return True
            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                print(f"Error: {e}")
            fail_tried += 1
            if fail_tried <= 3:
                if self.connect_to_vpn(fail_tried):
                    return True
            return False

    def get_arch_of_device(self):
        LOGGER.debug('Get the architecture of the current device')
        device = self.adb.device(f'emulator-{self.adb_console_port} -no-boot-anim')
        if device:
            arch = device.shell('getprop ro.product.cpu.abi').strip()
            LOGGER.debug(f'Architecture of current device: {arch}')
            return arch

            
            
    def find_element(self, element, locator, locator_type=By.XPATH,
            page=None, timeout=10,timesleep=1):
        """Find an element, then return it or None.
        If timeout is less than or requal zero, then just find.
        If it is more than zero, then wait for the element present.
        """
        try:
            time.sleep(timesleep)
            if timeout > 0:
                wait_obj = WebDriverWait(self.driver(), timeout)
                ele = wait_obj.until(
                         EC.presence_of_element_located(
                             (locator_type, locator)))
            else:
                self.logger.info(f'Timeout is less or equal zero: {timeout}')
                ele = self.driver().find_element(by=locator_type,
                        value=locator)
            if page:
                self.logger.info(
                        f'Found the element "{element}" in the page "{page}"')
            else:
                self.logger.info(f'Found the element: {element}')
            return ele
        except (NoSuchElementException, TimeoutException) as e:
            if page:
                self.logger.info(f'Cannot find the element "{element}"'
                        f' in the page "{page}"')
            else:
                self.logger.info(f'Cannot find the element: {element}')
    
    def find_elements(self, element, locator, locator_type=By.XPATH,
            page=None, timeout=10,timesleep=1):
        """Find an element, then return it or None.
        If timeout is less than or requal zero, then just find.
        If it is more than zero, then wait for the element present.
        """
        try:
            time.sleep(timesleep)
            if timeout > 0:
                wait_obj = WebDriverWait(self.driver(), timeout)
                ele = wait_obj.until(
                         EC.presence_of_all_elements_located(
                             (locator_type, locator)))
            else:
                self.logger.info(f'Timeout is less or equal zero: {timeout}')
                ele = self.driver().find_elements(by=locator_type,
                        value=locator)
            if page:
                self.logger.info(
                        f'Found the element "{element}" in the page "{page}"')
            else:
                self.logger.info(f'Found the element: {element}')
            return ele
        except (NoSuchElementException, TimeoutException) as e:
            if page:
                self.logger.info(f'Cannot find the element "{element}"'
                        f' in the page "{page}"')
            else:
                self.logger.info(f'Cannot find the element: {element}')

    def click_element(self, element, locator, locator_type=By.XPATH,
            timeout=timeout,page=None,timesleep=1):
        
        """Find an element, then click and return it, or return None"""
        ele = self.find_element(element, locator, locator_type, timeout=timeout,page=page,timesleep=timesleep)
        if ele:
            ele.click()
            LOGGER.debug(f'Clicked the element: {element}')
            return ele

    def input_text(self, text, element, locator, locator_type=By.XPATH,
            timeout=timeout, hide_keyboard=True,page=None):
        
        """Find an element, then input text and return it, or return None"""
        try:
            if hide_keyboard :
                self.logger.debug(f'Hide keyboard')
                try:self.driver().hide_keyboard()
                except:None

            ele = self.find_element(element, locator, locator_type=locator_type,
                    timeout=timeout,page=page)
            if ele:
                ele.clear()
                ele.send_keys(text)
                self.logger.debug(f'Inputed "{text}" for the element: {element}')
                return ele
        except Exception as e :
            self.logger.info(f'Got an error in input text :{element} {e}')  
    
    def swip_display(self,scroll_height):
        try:
            window_size = self.driver().get_window_size()
            width = window_size["width"]
            height = window_size["height"]
            x1 = width*0.7
            y1 = height*(scroll_height/10)
            y2 = height*0.2
            self.driver().swipe(start_x = x1,start_y = y1,end_x = x1,end_y = y2, duration=random.randrange(1050, 1250),)
        except Exception as e : print(e)

    def swipe_left(self):
        try:
            window_size = self.driver().get_window_size()
            width = window_size["width"]
            height = window_size["height"]
            x1 = width * 0.7
            y1 = height * 0.5
            x2 = width * 0.2
            self.driver().swipe(start_x=x1, start_y=y1, end_x=x2, end_y=y1, duration=random.randrange(1050, 1250))
        except Exception as e:
            print(e)

    def swipe_right(self):
        try:
            window_size = self.driver().get_window_size()
            width = window_size["width"]
            height = window_size["height"]
            x1 = width * 0.2
            y1 = height * 0.5
            x2 = width * 0.7
            self.driver().swipe(start_x=x1, start_y=y1, end_x=x2, end_y=y1, duration=random.randrange(1050, 1250))
        except Exception as e:
            print(e)

    def swipe_down(self):
        try:
            size = self.driver().get_window_size()
            x, y = size['width'], size['height']
            x1, y1, y2 = x * 0.5, y * 0.4, y * 0.7  # start from the middle of the screen and swipe down to the bottom
            t = 200
            self.driver().swipe(x1, y1, x1, y2, t)
        except Exception as e:
            print(e)

    def swipe_up(self):
        try:
            size = self.app_driver.get_window_size()
            x, y = size['width'], size['height']
            x1, y1, y2 = x * 0.5, y * 0.7, y * 0.4 # start from the middle of the screen and swipe up to the top
            t = 200
            self.app_driver.swipe(x1, y1, x1, y2, t)
            # size = self.driver().get_window_size()
            # x, y = size['width'], size['height']
            # x1 = x * 0.5
            # y1, y2 = y * 0.75, y * 0.25  # move 1/4 up from the bottom and 3/4 down from the top
            # t = 200
            # self.app_driver.swipe(x1, y1, x1, y2, t)
        except Exception as e: print(e)

    def tap_left(self):
        from appium.webdriver.common.touch_action import TouchAction
        try:
            x = 1286
            y = 1126
            action = TouchAction(self.driver())
            action.tap(x=x, y=y).perform()
        except Exception as e:
            print(e)
            
    def back_until_number(self,number):
        try:
            for i in range(number):
                time.sleep(0.3)
                self.driver().back()
        except Exception as e :
            self.logger.info(f'Got an error in Go back to the number : {e}')
            
    def find_accessibility_id(self, id):
        try:
            ele = self.driver().find_element_by_accessibility_id(id)
            if ele: return ele
        except:
            return None
        
    def otp_process(self,):
        number_class = phone_numbers()
        china = True if "china" == str(self.country_code).lower() else False
        for I_otp in range(10) :
            otp = number_class.get_sms(self.phone_number,self.country_code,china=china)
            if otp:
                print(otp)
                self.input_text(str(otp),'input otp','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
                next_btn = self.app_driver.find_element(By.XPATH,'//android.widget.Button[@content-desc="Next"]')
                next_btn.click()
                return True ,''
            if I_otp == 9:
                number_class.ban_number(self.phone_number,self.country_code,china=china)
        return False, 'delete_avd'
                
                
    def phone_number_proccess(self):
        if self.find_element('phone number page', '''//android.view.View[@text="What's your mobile number?"]''',timeout=2):
            for phone_try in range(3):
                china = True if "china" == str(self.country_code).lower() else False
                number_class = phone_numbers()
                print(f'\n\n\n----The china china is : {china}----\n\n\n')
                self.phone_number = number_class.get_number(china=china,country_code=self.country_code)
                phone_number_digit = str(self.phone_number).isdigit()
                if phone_number_digit:
                    if self.input_text(self.phone_number,'phone number input','//android.widget.EditText[@class="android.widget.EditText"]'):
                        LOGGER.info(f"The phone number is {self.phone_number}")
                        if self.click_element('Next btn','//android.widget.Button[@content-desc="Next"]') :
                            random_sleep(3,3)
                            if self.find_accessibility_id('Please wait a few minutes before you try again.'):
                                return 'delete_avd'  ,'' 
                            if self.find_accessibility_id('Looks like your mobile number may be incorrect. Try entering your full number, including the country code.'):
                                number_class.ban_number(self.phone_number,self.country_code,china=china)
                                continue
                            random_sleep(10,10,reason='next page')
                else:
                    LOGGER.info(self.phone_number)
                    continue

                otp_page = self.find_element('Confirmation code input','//android.view.View[@content-desc="Enter the confirmation code"]',page='OTP page')
                if not otp_page :
                
                    if self.find_accessibility_id('Looks like your mobile number may be incorrect. Try entering your full number, including the country code.'):
                        number_class.ban_number(self.phone_number,self.country_code,china=china)
                        continue
                    
                    elif self.click_element('Create account','//android.widget.Button[@content-desc="Create new account"]'):
                        ...
                        
                    elif self.find_element('otp page', '//android.view.View[@text="Enter the confirmation code"]',timeout=5):
                        ...
                        
                    elif self.find_element('something went wrong','//android.view.View[@content-desc="Something went wrong. Please try again later."]',timeout=2):
                        number_class.ban_number(self.phone_number,self.country_code,china=china)
                        self.df.loc['avd']=self.emulator_name
                        self.df.to_csv('delete_avd.csv', index=False)
                        print(f'add this {self.emulator_name} avd in delete local avd list')
                        self.user_avd.delete()
                        return 'delete_avd' ,''

                    elif self.find_element('phone number page', '''//android.view.View[@text="What's your mobile number?"]''',timeout=2):
                        self.df.loc['avd']=self.emulator_name
                        self.df.to_csv('delete_avd.csv', index=False)
                        print(f'add this {self.emulator_name} avd in delete local avd list')
                        self.user_avd.delete()
                        return 'delete_avd'  ,''    
                    
                    elif self.find_element('name page', '''//android.view.View[@text="What's your name?"]''',timeout=2):
                        return True ,'otp_page'
                    
                for I_otp in range(10) :
                    
                    otp = number_class.get_sms(self.phone_number,self.country_code,china=china)
                    if otp:
                        print(otp)
                        self.input_text(str(otp),'input otp','//android.widget.EditText[@class="android.widget.EditText"]')
                        next_btn = self.app_driver.find_element(By.XPATH,'//android.widget.Button[@content-desc="Next"]')
                        next_btn.click()
                        return True ,''
                    if I_otp == 9:
                        number_class.ban_number(self.phone_number,self.country_code,china=china)
                        self.driver().back()
                    time.sleep(10)
                        
            else:
                print(f'add this {self.emulator_name} avd in delete local avd list')
                return 'delete_avd', 'number_not_found'                    
            
        # else :
        #     self.df.loc['avd']=self.emulator_name
        #     self.df.to_csv('delete_avd.csv', index=False)
        #     print(f'add this {self.emulator_name} avd in delete local avd list')
        #     self.user_avd.delete()
        #     return 'delete_avd', 'number_not_found'

    def send_request(self):
        import requests
        import random

        # Set API key and base URL
        API_KEY = 'iYa3QPpz0YifBomcbWg7uq8TzloBB5K4WWPZnRyRijXbwfdj48c5NWiY'
        BASE_URL = "https://api.pexels.com/v1"
        if self.gender == "female" : 
            query = random.choice(['girl','beautiful girl','beautiful woman','business woman'])
        else:
            query = random.choice(['handsome boy','cool boy', 'businessman'])
        # topic  = ['person',,'forest','bird','animal','sunrise','sunset','mount','river','ocean','beautiful nature','beautiful cloud']
        # Set search parameters
        # query = random.choice(topic)  # or any other query
        per_page = 1  # number of results to return
        page = random.randint(1, 500)  # select a random page number

        # Set headers with API key
        headers = {"Authorization": API_KEY}

        # Send API request to Pexels
        url = f"{BASE_URL}/search?query={query}&per_page={per_page}&page={page}"
        response = requests.get(url, headers=headers)
        return response
    
    def profile_img_download(self):
        '''
        downloading the file and saving it in download folder
        '''
        response = self.send_request()
        # Check if API request was successful
        while response.status_code != 200:
            time.sleep(5)
            response = self.send_request()

        LOGGER.info(f'send proofile pic request status : {response.status_code}')
        # Get URL of random photo from API response
        data = response.json()
        photo_url = data["photos"][0]["src"]["original"]

        # Download photo to local file
        file_name = "prof_img/profile_pic.jpg"
        profile_pic_path = os.path.join(os.getcwd(), file_name)
        response = requests.get(photo_url)
        # filename = f"{query}_{page}_1.jpg"  # or any other filename
        with open(file_name, "wb") as f:
            f.write(response.content)

        LOGGER.info(f"profile image path : {profile_pic_path}")
        with open(profile_pic_path, "wb") as file:
            file.write(response.content)
        time.sleep(10)

        run_cmd(f'adb -s emulator-{self.adb_console_port} push {profile_pic_path} /sdcard/Download')


    def add_profile_pic2(self):
        self.click_element('click on add_rofile','//android.widget.Button[@content-desc="Add picture"]')
        self.profile_img_download()
        time.sleep(3)
        self.click_element('choose from gallery','//android.view.View[@content-desc="Choose from Gallery"]')
        time.sleep(3)
        menu_btn = self.driver().find_element_by_accessibility_id('Show roots').click()
        self.click_element('download','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout[2]/android.widget.FrameLayout/android.widget.ListView/android.widget.LinearLayout[2]/android.widget.LinearLayout')
        self.click_element('choose pic','com.android.documentsui:id/icon_thumb',By.ID)
        self.click_element('also share post','//android.widget.Switch[@content-desc="Also share this picture as a post"]/android.view.ViewGroup/android.widget.FrameLayout/android.widget.Switch')
        
        time.sleep(3)
        donne = self.click_element('Done','//android.widget.Button[@content-desc="Done"]')
        time.sleep(20)
        skip_profile_pic_id = 'com.instagram.android:id/skip_button'
        skip = self.click_element('skip add profile pic btn',skip_profile_pic_id,By.ID)  
        if not skip:
            self.driver().back()
            
        self.click_element('Skip2','com.instagram.android:id/negative_button',By.ID)
        # self.click_element('follow instagram','//android.widget.Button[@content-desc="Follow Instagram"]')
        self.click_element('next arrow','//android.widget.Button[@content-desc="Next"]/android.widget.ImageView')
        self.click_element('Next Button','com.instagram.android:id/button_text',By.ID)
        # self.click_element('next arrow','//android.widget.Button[@content-desc="Next"]/android.widget.ImageView')
        # self.click_element('next arrow',s'//android.widget.Button[@content-desc="Next"]/android.widget.ImageView')
        # self.next_btn()
        if skip:
            return True
        else:return False


    def delete_avd(self,emulator_name):
        try:
            cmd = f'avdmanager delete avd --name {emulator_name}'
            p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
        except Exception as e:
            pass
    
    def set_value(self,value,type):
        if type == 'year':
            NumberPicker = 3
            Button = 1
            num = 2023 - int(self.birth_year) - 2
            for i in range(num):
                self.click_element(f'select {type}',f'//android.widget.DatePicker//android.widget.NumberPicker[{NumberPicker}]//android.widget.Button[{Button}]')                
        elif type == 'day':
            NumberPicker = 2
            Button = 1
            initial_day = int(self.find_element(f'{type}', f'//android.widget.DatePicker//android.widget.NumberPicker[{NumberPicker}]//android.widget.EditText').text)
            target_day = int(value)
            total_days = 31  
            downside_clicks = (target_day - initial_day) % total_days
            upside_clicks = (initial_day - target_day) % total_days
            if downside_clicks > upside_clicks:
                Button = 1
            else:
                Button = 2
            
        elif type == 'month':
            birth_month_li = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov', 'Dec']
            NumberPicker = 1
            now = self.find_element(f'{type}',f'//android.widget.DatePicker//android.widget.NumberPicker[{NumberPicker}]//android.widget.EditText').text
            now_index = birth_month_li.index(now)
            value_index = birth_month_li.index(value)
            if now_index < value_index:
                Button = 2
            elif now_index > value_index:
                Button = 1

        now = self.find_element(f'{type}',f'//android.widget.DatePicker//android.widget.NumberPicker[{NumberPicker}]//android.widget.EditText').text
        while str(now) != str(value):
            LOGGER.info(f'set {value} in {type}')
            self.click_element(f'select {type}',f'//android.widget.DatePicker//android.widget.NumberPicker[{NumberPicker}]//android.widget.Button[{Button}]')
            now = self.find_element(f'{type}',f'//android.widget.DatePicker//android.widget.NumberPicker[{NumberPicker}]//android.widget.EditText').text

    def swip_until_match(self,comperison_xpath,comperison_text):
        rect_ele = self.driver().find_element_by_xpath(comperison_xpath).rect
        start_x = rect_ele['x'] + rect_ele['width'] / 2
        start_y = rect_ele['y'] + rect_ele['height'] / 2
        end_x = start_x
        end_y = start_y + rect_ele['height']
        LOGGER.debug(f'start_x: {start_x}, start_y: {start_y}, end_x: {end_x}, end_y: {end_y}')
        is_digit = str(comperison_text).isdigit()

        while True:
            try:
                comperison_xpath_text = self.driver().find_element_by_xpath(comperison_xpath).text
                if comperison_xpath_text == comperison_text:
                    break
                if is_digit and len(comperison_text) == 4 and int(comperison_text) > int(comperison_xpath_text):
                    end_y = start_y - rect_ele['height']
                elif is_digit and len(comperison_text) == 2 and int(comperison_xpath_text) >= 15:
                    end_y = start_y - rect_ele['height']
                
                self.driver().swipe(start_x=start_x,start_y=start_y,end_x=end_x,end_y=end_y,duration=random.randrange(200, 250))
            except Exception as e :print(e)

    def set_birth_date(self):
        set_date = self.find_element('Set date scroller','android:id/alertTitle',By.ID,timeout=4)
        if set_date :
            if set_date.text == 'Set date' : ...
            else : return 
        else : return

        self.click_element('birthday input','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.widget.EditText',timeout=5)
        middle_month_picker_relative_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.DatePicker/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.NumberPicker[1]/android.widget.EditText'
        middle_day_picker_relative_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.DatePicker/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.NumberPicker[2]/android.widget.EditText'
        middle_year_picker_relative_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.DatePicker/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.NumberPicker[3]/android.widget.EditText'
        
        LOGGER.debug(f'set_year: {self.birth_year}')
        year = str(int(self.birth_year)+1)
        self.swip_until_match(middle_year_picker_relative_xpath,year)
        
        LOGGER.debug(f'set_month: {self.birth_month}')
        self.swip_until_match(middle_month_picker_relative_xpath,self.birth_month)
        
        LOGGER.debug(f'set_date: {self.birth_date}')
        self.swip_until_match(middle_day_picker_relative_xpath,self.birth_date)
        self.click_element('Set btn','android:id/button1',By.ID)
        if self.next_btn() :
            random_sleep(3)
        return True
        
    
    def add_bio2(self):
        time.sleep(5)
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
        for i in range(5):
            self.swip_display(4)
        # com.instagram.android:id/find_people_card_button
        add_btn = self.click_element('Add Bio btn','com.instagram.android:id/find_people_card_button',By.ID)
        if add_btn:
            self.bio = random_insta_bio()
            self.input_text(self.bio,"User's Bio", 'com.instagram.android:id/caption_edit_text',By.ID)
            check = self.click_element('tick btn','//android.widget.Button[@content-desc="Done"]/android.widget.ImageView')
            if check:
                return True
            time.sleep(3)
        else:
            return False
    
    def username_process(self):
        try:
            LOGGER.info(f' Full name is {self.full_name}')
            self.input_text(self.full_name,'first name input','//*[@class="android.widget.EditText"]')
            self.next_btn()
            LOGGER.info(f'password is {self.password}')
            time.sleep(5)
            self.input_text(self.password,'password input','//*[@class="android.widget.EditText"]')
            self.next_btn()
            self.click_element('save info','//android.widget.Button[@content-desc="Save"]')
            #  ----------------
        except Exception as e:
            print(e)

        self.set_birth_date_main()
        random_sleep(10,12,reason='green tick or username')
        ...
        green_tick = self.find_element('Green Tick','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.widget.ImageView')
        if green_tick:
            self.i_username = self.driver().find_element(By.XPATH,'/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText').text
            self.next_btn()
        elif self.find_element('Check Usser Name',"//*[contains(@text, 'your Instagram username')]"):
            user_name = self.find_element('Check Usser Name',"//*[contains(@text, 'your Instagram username')]")
            self.i_username = user_name.text.split(' ')[0]
            self.next_btn()
        else:
            user_ = self.find_element('username','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
            if user_:
                self.i_username = str(self.full_name)+str(random.randint(10000,99999))
                self.input_text(self.i_username,'input user_name','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
                time.sleep(3)
                self.next_btn()

    def next_btn(self):    
        return self.click_element('Next Button','//android.widget.Button[@content-desc="Next"]')
    
    def add_profile_pic(self):
        self.click_element('profile button','//android.widget.FrameLayout[@content-desc="Profile"]/android.view.ViewGroup')
        self.click_element('Edit profile','(//android.widget.FrameLayout[@resource-id="com.instagram.android:id/button_container"])[1]')
        self.click_element('Create avatar cancle','com.instagram.android:id/negative_button',By.ID)
        self.click_element('Change avatar button','com.instagram.android:id/change_avatar_button',By.ID)
        self.click_element('click on add_rofile','//android.view.ViewGroup[@content-desc="New profile picture"]')
        self.click_element('Gallary btn','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.TabWidget/android.widget.TextView[1]')
        self.click_element('gallary folder menu','com.instagram.android:id/gallery_folder_menu',By.ID)
        self.click_element('Other ...','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[2]/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.widget.Button[2]')
        self.profile_img_download() 
        if self.click_element('Show roots','//android.widget.ImageButton[@content-desc="Show roots"]',timeout=15):
            if self.click_element('download','//android.widget.TextView[@resource-id="android:id/title" and @text="Downloads"]'):
                if self.click_element('choose pic','com.android.documentsui:id/icon_thumb',By.ID) :
                    if self.click_element('next btn','com.instagram.android:id/save',By.ID,timeout=30) :
                        if self.click_element('next_button_imageview','com.instagram.android:id/next_button_imageview',By.ID):
                            return True
        return False
            
    
    def add_bio(self):
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID,timeout=30)
        self.click_element('Edit profile','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout[1]/android.widget.LinearLayout/android.widget.LinearLayout[1]/android.widget.Button[1]/android.widget.FrameLayout/android.widget.Button')
        self.swip_display(4)
        self.click_element('Add Bio btn','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout[2]/android.view.ViewGroup[4]/android.widget.EditText')
        self.bio = random_insta_bio()
        self.input_text(self.bio,"User's Bio", 'com.instagram.android:id/caption_edit_text',By.ID)
        check = self.click_element('tick btn','//android.widget.Button[@content-desc="Done"]/android.widget.ImageView')
        check = self.click_element('tick btn','//android.widget.Button[@content-desc="Done"]/android.widget.ImageView')
        if check:
            return True
        return False
        
    def enter_password(self):
        create_ps_tl =  self.find_element('Create a password title','//android.view.View[@content-desc="Create a password"]',timeout=4) 
        if create_ps_tl :
            if create_ps_tl.text == "Create a password" :
                self.input_text(self.password,'password input','//*[@class="android.widget.EditText"]')
                self.next_btn()
                random_sleep(3)
                return True
            
    def save_info(self):
        save_info_title = self.find_element('Save info','//android.view.View[@content-desc="Save your login info?"]',timeout=4) 
        if save_info_title :
            if save_info_title.text == "Save your login info?":
                self.click_element('save info','//android.widget.Button[@content-desc="Save"]')
                random_sleep(3)
                return True
            
    def add_name_in_new_user(self):
        try:
            name_title = self.find_element('Full name title','''//android.view.View[@content-desc="What's your name?"]''')
            if name_title :
                if name_title.text != "What's your name?":
                    return
                LOGGER.info(f'Full name {self.full_name}')
                self.input_text(self.full_name,'first name input','''//*[@class="android.widget.EditText"]''')
                self.next_btn()
                return True
            # print(self.password)
            # time.sleep(5)
            # if self.input_text(self.password,'password input','//*[@class="android.widget.EditText"]') :
            #     self.process_acc_creation.remove("enter_password")
            # if self.next_btn() :
            #     random_sleep(5,10)
            # if self.click_element('save info','//android.widget.Button[@content-desc="Save"]') :
            #     self.process_acc_creation.remove("save_info")
            #     random_sleep(5,10)

            # return True

        except Exception as e:
            print(e)
            return False
    
    def create_set_username(self):
        create_username_title = self.find_element('username title','//android.view.View[@content-desc="Create a username"]') or self.find_element('username title','//android.view.View[@content-desc="Create your username"]')
        if create_username_title :
            username_input = self.find_element('username input','//android.widget.EditText[@class="android.widget.EditText"]')
            random_sleep(5,7)
            while True:
                if username_input and username_input.text is not None:
                    self.user_username = username_input.text
                    self.next_btn()
                    return self.user_username
                else: 
                    self.user_username = str(self.full_name)+"_"+str(random.randint(1000000,9999999))
                    self.input_text(self.user_username,'username input','//android.widget.EditText[@class="android.widget.EditText"]')
                    random_sleep(5,7)
                    if self.find_accessibility_id('Usernames can only include numbers, letters, underscores and periods. Try again.'):continue
                    if self.find_accessibility_id(f'The username {self.user_username} is not available.'):continue    
                    if not self.next_btn():continue
                    return self.user_username

    def agree_btn(self) :
        if self.click_element('Agree policy','//android.widget.Button[@content-desc="I agree"]/android.view.ViewGroup',timeout=2) :
            # random_sleep(15,20)
            if self.find_element('Suspended account','//android.view.View[@text="We suspended your account, AdrienneGardner" and @class="android.view.View"]') : return False
            return True
        if self.click_element('Agree policy','//android.widget.Button[@content-desc="I agree"]/android.view.ViewGroup',timeout=2) : return True
    
    def other_stuff_create_account(self):
        proc_pic_title = self.find_element('Add a profile pic title','//android.view.View[@content-desc="Add a profile picture"]',timeout=50)
        if proc_pic_title:
            if proc_pic_title.text == "Add a profile picture":
                self.click_element('Skip btn for profile pic','//android.widget.Button[@content-desc="Skip"]/android.view.ViewGroup')

            follow_fb_fri = self.find_element('Follow fb friends title','com.instagram.android:id/igds_headline_headline',By.ID,timeout=40)
            if follow_fb_fri :
                if follow_fb_fri.text == "Find Facebook friends to follow":
                    a2 = self.click_element('Skip btn for profile pic','com.instagram.android:id/skip_button',By.ID)

            Follow_friends = self.find_element('Find friends','com.instagram.android:id/primary_button',By.ID,timeout=40)
            if Follow_friends : 
                if Follow_friends.text == "Follow friends":
                    self.click_element('skip button','com.instagram.android:id/negative_button',By.ID)

            Invite_friends_to_follow = self.find_element('Invite_friends_to_follow','com.instagram.android:id/igds_headline_headline',By.ID,timeout=40)
            if Invite_friends_to_follow :
                if Invite_friends_to_follow.text == "Invite friends to follow you":
                    self.click_element("skip button","com.instagram.android:id/skip_button",By.ID)

            discover_ppl = self.find_element('Discover people','com.instagram.android:id/action_bar_large_title',By.ID,timeout=40)
            if discover_ppl : 
                if discover_ppl.text == "Discover people":
                    self.click_element("Next arrow",'//android.widget.Button[@content-desc="Next"]/android.widget.ImageView')
            return True
        return False
    
    def create_account(self,country_code):
        self.country_code =country_code
        self.gender =np.random.choice(["male", "female"], p=[0.5, 0.5])
        fake = Faker()
        seed=None
        np.random.seed(seed)
        fake.seed_instance(seed)
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
        
        LOGGER.debug('Check if instagram is installed')        
        if not self.driver().is_app_installed("com.instagram.android"):
            LOGGER.debug('instagram is not installed, now install it')
            self.Install_new_insta()
        random_sleep()
        for _ in range(1) :
            self.driver().activate_app('com.instagram.android')
            create_btn = self.find_element('create account btn','//android.widget.Button[@content-desc="Create new account"]',timeout=30)

            if create_btn:
                self.click_element('create account btn','//android.widget.Button[@content-desc="Create new account"]')
            else:

                LOGGER.info(f'add this {self.emulator_name} avd in delete local avd list')
                return False, False, ''

            refreash_ele = self.find_element('page isnt available','''//android.widget.TextView[@text="Page isn't available right now" and @class="android.widget.TextView"]''')
            if refreash_ele :
                if refreash_ele.text == "Page isn't available right now":
                    return False, False, ''
            
            self.process_acc_creation = ['enter_password'
                                    ,"save_info"
                                    ,"set_birth_date"
                                    ,"phone_number_proccess"
                                    ,"create_set_username"
                                    ,"add_name_in_new_user"
                                        ]
            for i in range(13):
                if "add_name_in_new_user" in self.process_acc_creation :
                    if self.add_name_in_new_user():
                        self.process_acc_creation.remove("add_name_in_new_user")
                if "enter_password" in self.process_acc_creation :
                    if self.enter_password() :
                        self.process_acc_creation.remove("enter_password")
                if "save_info" in self.process_acc_creation :
                    if self.save_info():
                        self.process_acc_creation.remove("save_info")
                if "set_birth_date" in self.process_acc_creation :
                    if self.set_birth_date():
                        self.process_acc_creation.remove("set_birth_date")
                if "create_set_username" in self.process_acc_creation :
                    if self.create_set_username():
                        self.process_acc_creation.remove("create_set_username")
                if "phone_number_proccess" in self.process_acc_creation :
                    numberr,number_not_found = self.phone_number_proccess()
                    if numberr == "delete_avd" or  numberr == False :
                        return False, False, number_not_found
                    elif number_not_found == 'otp_page' :
                        self.process_acc_creation.append('otp_process')
                    self.process_acc_creation.remove("phone_number_proccess")
                if 'otp_process' in self.process_acc_creation:
                    otp, otp_found =  self.otp_process()
                    if otp == "delete_avd" or  otp == False :
                        return False, False, otp_found
                    self.process_acc_creation.remove("otp_process")
                self.agree_btn()
                    
                if self.find_element('Add a profile pic title','//android.view.View[@content-desc="Add a profile picture"]',timeout=2):
                    break
                
            else :return False, False, ''
            
            # self.coneect_db()
            self.user_gender = random.choice(['MALE','FEMALE'])
            self.user = User_details.objects.create(avdsname=self.emulator_name,username=self.user_username,number=self.phone_number,password=self.password,birth_date=self.birth_date,birth_month=self.birth_month,birth_year=self.birth_year,status='ACTIVE',avd_pc = os.environ.get("SYSTEM_NO"))
            self.user.save()
            self.add_profile_pic()
            check_add_bio = self.add_bio()
            self.upload_post()
            try:
                self.user.bio = self.bio
                self.user.is_bio_updated=check_add_bio
            except AttributeError  as a:print(a)
            except Exception as ee:print(ee)
            self.user.updated=True
            # self.coneect_db()
            self.user.save()
            self.other_stuff_create_account()
            return self.user, True, ''
                
            # add_profile = self.click_element('profile button','//android.widget.FrameLayout[@content-desc="Profile"]/android.view.ViewGroup',timeout=15)
            # if add_profile:
            
        return False, False, ''
    
    def create_account2(self):
        print(f'\n\n\n----The ps name is : {os.getenv("SYSTEM_NO")}----\n\n\n')
        gender_detector = detector.Detector()
        fake = Faker()
        self.gender = random.choice(["male", "female"])
        if self.gender == "male":
            self.fname = names.get_first_name(gender="male")
        else:
            self.fname = names.get_first_name(gender="female")
        detected_gender = gender_detector.get_gender(self.fname)
        while detected_gender != self.gender:
            if self.gender == "male":
                self.fname = names.get_first_name(gender="male")
            else:
                self.fname = names.get_first_name(gender="female")
            detected_gender = gender_detector.get_gender(self.fname)
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
        self.driver().terminate_app('com.instagram.android')
        random_sleep(2,3,reason='open insta')
        self.driver().activate_app('com.instagram.android')
        random_sleep(15,17,reason='open insta app')
        if self.driver().current_activity == 'com.instagram.nux.activity.SignedOutFragmentActivity':
            self.driver().remove_app('com.instagram.android')
            self.Install_new_insta()
            self.create_account()        
        self.click_element('create account btn','//android.widget.Button[@content-desc="Create new account"]')
        if self.find_element('name page', '''//android.view.View[@text="What's your name?"]''',timeout=5):
            self.username_process()
            phone_number = self.phone_number_proccess()
            if not phone_number:
                return False
        else:
            phone_number = self.phone_number_proccess()
            if not phone_number:
                return False 
            self.username_process()

        
        i_agree = self.find_element('i_agree','//android.widget.Button[@content-desc="I agree"]')
        if i_agree:
            self.click_element('I agree','//android.widget.Button[@content-desc="I agree"]')
            random_sleep(22,25,reason='I agree')
            
            add_profile = self.find_element('add_profile_btn','//android.widget.Button[@content-desc="Add picture"]')
            if not add_profile:
                self.driver().back()
                self.next_btn()
                self.click_element('i_agree','//android.widget.Button[@content-desc="I agree"]')
                random_sleep(22,25,reason='I agree')
                add_profile = self.find_element('add_profile_btn','//android.widget.Button[@content-desc="Add picture"]')
            
            add_profile = self.find_element('add_profile_btn','//android.widget.Button[@content-desc="Add picture"]')
            if add_profile:
                user = User_details.objects.create(
                            avdsname=self.emulator_name,
                            username=self.i_username,
                            number=self.phone_number,
                            password=self.password,
                            birth_date=self.birth_date,
                            birth_month=self.birth_month,
                            birth_year=self.birth_year,
                            status='ACTIVE',
                            avd_pc = os.getenv('PC'),
                        )
                
                self.add_profile_pic()
                check_add_bio = self.add_bio()
                time.sleep(5)
                try:
                    user.bio = self.bio
                    user.is_bio_updated=check_add_bio
                except AttributeError  as a:print(a)
                # except Exception as ee:print(ee)
                user.updated=False
                user.save()
                self.driver().terminate_app('com.instagram.android')
                self.driver().activate_app('com.instagram.android')
                random_sleep(10,15,reason='open instagram')
                # self.follow_rio()
                # self.follow_gpt()
                return user
            else:
                return False
            

    def Install_new_insta(self,):
        cmd = f"adb -s emulator-{self.adb_console_port} install -t -r -d -g {os.path.join(BASE_DIR, 'apk/instagram.apk')}"
        log_activity(
            self.user_avd.name,
            action_type="InstallInstagramApk",
            msg=f"Installation of instagram apk",
            error=None,
        )
        p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
        p.wait()

    def connect_windscribe(self,country):
        self.driver().activate_app('com.windscribe.vpn')
        random_sleep(5,10,reason='open windscribe')
        if self.driver().current_activity == 'com.windscribe.mobile.welcome.WelcomeActivity':
            self.click_element('login','//android.widget.Button[@text="Login"]')
            self.input_text(os.getenv('windscribe_username'),'username','com.windscribe.vpn:id/username',By.ID)
            self.input_text(os.getenv('windscribe_password'),'password','com.windscribe.vpn:id/password',By.ID)  
            self.click_element('continue','//android.widget.Button[@text="Continue"]') 
            random_sleep(15,15,reason='get server list')
            while self.driver().current_activity != 'com.windscribe.mobile.windscribe.WindscribeActivity':
                time.sleep(5)
        if self.driver().current_activity == 'com.windscribe.mobile.windscribe.WindscribeActivity':
            city_name = self.find_element('city name','com.windscribe.vpn:id/tv_connected_city_name',By.ID)    
            while not city_name:
                city_name = self.find_element('city name','com.windscribe.vpn:id/tv_connected_city_name',By.ID,timeout=2)
            connection_status = self.find_element('status','com.windscribe.vpn:id/tv_connection_state',By.ID)
            if city_name.text == 'Hong Kong' and connection_status.text == 'OFF':
                self.click_element('connect btn','com.windscribe.vpn:id/on_off_button',By.ID)
                self.click_element('ok','android:id/button1',By.ID,timeout=5)
                random_sleep(8,9,reason='wait for connection')
                connection_status = self.find_element('status','com.windscribe.vpn:id/tv_connection_state',By.ID)
                while not connection_status.text == 'ON':
                    connection_status = self.find_element('status','com.windscribe.vpn:id/tv_connection_state',By.ID)
                    if connection_status.text == 'ON':
                        return True
            elif city_name.text == 'Hong Kong' and connection_status.text == 'ON':
                return True
            else:
                self.click_element('search','com.windscribe.vpn:id/img_search_list',By.ID)
                self.input_text(country,'search country','com.windscribe.vpn:id/search_src_text',By.ID)
                self.click_element('country',"//android.widget.TextView[@text='Hong Kong Victoria' and @resource-id='com.windscribe.vpn:id/node_name']")
                self.click_element('ok','android:id/button1',By.ID)
                connection_status = self.find_element('status','com.windscribe.vpn:id/tv_connection_state',By.ID)
                random_sleep(4,5,reason='wait for connection')
                while not connection_status.text == 'ON':
                    connection_status = self.find_element('status','com.windscribe.vpn:id/tv_connection_state',By.ID)
                    if connection_status.text == 'ON':
                        return True
                    
    def logout_windscribe(self):
        try:
            self.driver().start_activity('com.windscribe.vpn','com.windscribe.mobile.windscribe.WindscribeActivity')
            self.click_element('menu','com.windscribe.vpn:id/img_hamburger_menu',By.ID)
            self.click_element('logout','com.windscribe.vpn:id/cl_sign',By.ID)
            self.click_element('ok','android:id/button1',By.ID)
        except Exception as e:
            print(e)
            ...
            
            
    def get_apk_version(self,package_name):
        dumpsys_output = subprocess.check_output(['adb','-s',f'emulator-{self.adb_console_port}', 'shell', 'dumpsys', 'package', package_name]).decode('utf-8')
        version_line = [line.strip() for line in dumpsys_output.split('\n') if 'versionName' in line][0]
        version_name = version_line.split('=')[1]
        return version_name
    
    def login_checker(self):
        for i in range(3):
            self.driver().terminate_app('com.instagram.android')    
            self.driver().activate_app('com.instagram.android')
            random_sleep(14,15,reason='open insta')
            if self.driver().current_activity == 'com.instagram.mainactivity.MainActivity':
                return True
            elif self.driver().current_activity == 'com.instagram.nux.activity.SignedOutFragmentActivity':
                self.Install_new_insta()
                return f"version not match"
            elif self.driver().current_activity == 'com.instagram.nux.activity.BloksSignedOutFragmentActivity':
                if self.find_element('profile photo','//android.widget.Button[@content-desc="Profile photo"]'):
                    return True
                else:
                    if self.connect_to_vpn(country='Hong Kong'):
                        return True
                    else:
                        return False

    def login(self,username,password):
        LOGGER.info("inside login methods")
        self.user = User_details.objects.filter(username=username).first()
        for i in range(3):
            self.driver().activate_app('com.instagram.android')
            random_sleep(14,15,reason='open insta')
            if self.driver().current_activity == 'com.instagram.mainactivity.MainActivity':
                if not self.find_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID):
                    try:
                        self.click_element('Allow All Cookies','//android.widget.Button[@content-desc="Allow all cookies"]')
                        allow_btn  = self.find_element('Allow Cookies','com.instagram.android:id/primary_button',By.ID).text
                        if allow_btn == 'Allow Access':
                            self.click_element('Allow Cookies','com.instagram.android:id/primary_button',By.ID)
                            self.click_element('back','//android.widget.ImageView[@content-desc="Back"]')
                    except AttributeError as f: print(f)
                    except Exception as e :print(e) 
                return True
                    
            if self.driver().current_activity == 'com.instagram.nux.activity.SignedOutFragmentActivity':
                self.driver().remove_app('com.instagram.android')
                self.Install_new_insta()
                self.login(username,password)
                
            if self.driver().current_activity == 'com.instagram.nux.activity.BloksSignedOutFragmentActivity':
                LOGGER.info(f'Username :{username}, Password :{password}')
                input_ele = None
                if self.find_element('input element','//*[@class="android.widget.EditText"]',timeout=3):
                    try:
                        input_ele = self.driver().find_elements(By.XPATH,'//*[@class="android.widget.EditText"]')
                    except Exception as e: 
                        print(e)
                    if input_ele:   
                        try:
                            LOGGER.info(f"your username is {username}")
                            input_ele[0].clear()
                            input_ele[0].send_keys(username)
                            LOGGER.info(f"your password is {password}")
                            time.sleep(2)
                            input_ele[1].clear()
                            input_ele[1].send_keys(password)
                        except Exception as e:print(e)
                        if self.click_element('Login btn','//android.widget.Button[@content-desc="Log in"]'):
                            login_btn = True
                else:
                    self.find_element('profile photo','//android.widget.Button[@content-desc="Profile photo"]')
                    self.click_element('Login btn','//android.widget.Button[@content-desc="Log in"]')
                    HomeBtn = self.find_element('Home page','com.instagram.android:id/feed_tab',By.ID,timeout=5)
                    if HomeBtn : 
                        return True
                    else:
                        if self.click_element('try another','//android.widget.Button[@content-desc="Try another way"]',timeout=3):
                            self.click_element('password','//android.widget.RadioButton[@content-desc="Enter password to log in"]')
                            self.click_element('continue','//android.widget.Button[@content-desc="Continue"]')
                        text_views = [view for view in self.driver().find_elements(By.XPATH,"//android.view.View[@text]") if view.is_displayed()]
                        text_list = [te.text for te in text_views]
                        usernames = [text for text in text_list if text and text !=  "Log in" and text !="Create New account"][0]
                        try:
                            usernames = usernames.text
                        except  AttributeError as a:
                            print(a)
                        usser = User_details.objects.filter(username=usernames).first()
                        if not usser :
                            usser = user_detail.objects.using('monitor').filter(username=usernames).first()
                        try:
                            password = usser.password
                        except:
                            pass
                        LOGGER.info(f'Username :{usernames}, Password :{password}') 
                        
                        # /hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText
                        self.input_text(password,'Password','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
                        if self.click_element('Login btn','//android.widget.Button[@content-desc="Log in"]'):
                            login_btn = True
                    
                # save login info
                if login_btn:
                    SaveInfo = self.find_element('save info','//android.view.View[@content-desc="Save your login info?"]',timeout=20)
                if SaveInfo:
                    self.click_element('Save','//android.widget.Button[@content-desc="Save"]')
                    time.sleep(7)
                    try:
                        self.click_element('Allow All Cookies','//android.widget.Button[@content-desc="Allow all cookies"]')
                        allow_btn  = self.find_element('Allow Cookies','com.instagram.android:id/primary_button',By.ID).text
                        if allow_btn == 'Allow Access':
                            self.click_element('Allow Cookies','com.instagram.android:id/primary_button',By.ID)
                            self.click_element('back','//android.widget.ImageView[@content-desc="Back"]')
                    except AttributeError as f: print(f)
                    except Exception as e :print(e)
                    HomeBtn = self.find_element('Home page','com.instagram.android:id/feed_tab',By.ID)
                    if HomeBtn : 
                        return True
                else:
                    if self.driver().current_activity == 'com.instagram.challenge.activity.ChallengeActivity':
                            self.user.status = 'LOGIN_ISSUE'
                            self.user.save()
                            self.df.loc['avd']=self.emulator_name
                            self.df.to_csv('delete_avd.csv', index=False)
                            LOGGER.info(f'add this {self.emulator_name} avd in delete local avd list')
                            return False
                        
                    unable_login = self.find_element('unable_login','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView')
                    if unable_login:
                        if unable_login.text =='Unable to log in':
                            self.user.status = 'LOGIN_ISSUE'
                            self.user.save()
                            self.df.loc['avd']=self.emulator_name
                            self.df.to_csv('delete_avd.csv', index=False)
                            LOGGER.info(f'add this {self.emulator_name} avd in delete local avd list')
                            return False
                        
                        
                    account_not_find = self.find_element('account not find','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView').text
                    if account_not_find:
                        if "can't find" in account_not_find.lower():
                            self.user.status = 'LOGIN_ISSUE'
                            self.user.save()
                            self.df.loc['avd']=self.emulator_name
                            self.df.to_csv('delete_avd.csv', index=False)
                            LOGGER.info(f'add this {self.emulator_name} avd in delete local avd list')
                            return False

                    appeal = self.find_element('appleal','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.Button')
                    if appeal:
                        self.user.status = 'LOGIN_ISSUE'
                        self.user.save()
                        self.df.loc['avd']=self.emulator_name
                        self.df.to_csv('delete_avd.csv', index=False)
                        LOGGER.info(f'add this {self.emulator_name} avd in delete local avd list')
                        return False

    def user_update_check(self):
        if self.user.is_bio_updated == False :
            
            self.click_element('Edit profile','(//android.widget.Button[@class="android.widget.Button"])[1]',By.XPATH)
            self.click_element('Create avatar not now','com.instagram.android:id/negative_button',By.ID)
            add_btn = self.click_element('Add Bio btn','(//android.widget.EditText[@class="android.widget.EditText"])[4]',By.XPATH)
            if add_btn:
                self.bio = random_insta_bio()
                self.input_text(self.bio,"User's Bio", 'com.instagram.android:id/caption_edit_text',By.ID)
                check = self.click_element('tick btn','//android.widget.Button[@content-desc="Done"]/android.widget.ImageView')
                if check:
                    return True
                time.sleep(3)
    
    def check_profile(self,username):
        time.sleep(3)
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
        ProfileName = self.find_element('Profile name','com.instagram.android:id/action_bar_large_title_auto_size',By.ID)
        if ProfileName:
            if ProfileName.text == username: 
                # self.user.avd_pc = os.getenv('PC')
                return True
            else : return False
        else: return False
        
    def find_user(self):
        CanSearchUsers = User_details.objects.filter(status='ACTIVE').all()
        try:   
            for Follow_user in CanSearchUsers:
                self.Follow_user = Follow_user
                if self.search_user(Follow_user.username):
                    pass
                else:
                    ...
                    print('---->')
        except Exception as e :print(e)

    def check_notification(self):
        if self.click_element('notification','//android.widget.Button[@content-desc="Activity"]'):
            notifications = self.driver().find_elements(By.XPATH,'//*[@resource-id="com.instagram.android:id/row_container"]')
            for element in notifications:
                try:
                    text_elements = element.find_elements_by_xpath(".//android.widget.TextView")
                    for text_element in text_elements:
                        text = text_element.text
                        if 'following you' in text:
                            follow = element.find_element(By.XPATH,".//android.widget.Button[@text='Follow']")
                            # ...
                            if follow:
                                LOGGER.info('Follow back user')
                                follow.click()
                                self.bot_follow = True
                            break
                    random_sleep(1,1,reason='Follow user')
                except Exception as e:
                    random_sleep(1,1,reason='exception')
                    print(e)
            back = self.click_element('back','//android.widget.ImageView[@content-desc="Back"]')
            if not back:
                self.driver().back()
                
    def random_activity(self,random_=False):
        if random_:
            xpath = random.choice(['image_preview', 'image_button'])
            # //android.widget.Button[@content-desc="Activity"]
            if not self.find_element('Random', f"//*[@resource-id='com.instagram.android:id/{xpath}']"):
                for i in range(2):
                    if not self.click_element('Back','com.instagram.android:id/action_bar_button_back',By.ID):
                        self.driver().back()
            self.click_element('Random', f"//*[@resource-id='com.instagram.android:id/{xpath}']")
            if xpath == 'image_preview':
                for i in range(3):
                    random_sleep(3,7,reason='see reels')
                    self.swip_display(9)                    
            else:
                for i in range(random.randint(3,6)):
                    random_sleep(3,5,reason='Change post')
                    self.swip_display(9)
                    
            if not self.click_element('Back','com.instagram.android:id/action_bar_button_back',By.ID):
                self.driver().back()
                    
    def search_user(self,Username):
        self.click_element('Search btn','com.instagram.android:id/search_tab',By.ID)
        self.click_element('Search input','com.instagram.android:id/action_bar_search_edit_text',By.ID)
        if not self.find_element('Search input','com.instagram.android:id/action_bar_search_edit_text',By.ID):
            for i in range(2):
                self.click_element('Back','com.instagram.android:id/action_bar_button_back',By.ID,timeout=5)
        self.input_text(Username,'Search input','com.instagram.android:id/action_bar_search_edit_text',By.ID)
        time.sleep(3)
        try:
            search_results = WebDriverWait(self.driver(), 10).until(EC.presence_of_all_elements_located((By.XPATH, "//*[@resource-id='com.instagram.android:id/row_search_user_username']")))
        except:search_results = ''
        if search_results:
            for i in search_results:
                if str(i.text).lower() == str(Username).lower():
                    i.click()
                    break
        elif self.click_element('see all result','//android.widget.Button[@text="See all results"]'):
            time.sleep(2)
            if not self.find_element('no result',f'''//*[@text='No results found for "{Username}"']'''):
                self.click_element('account','//android.widget.TabWidget[@content-desc="Accounts"]')
                if not self.find_element('no result',f'''//*[@text='No results found for "{Username}"']'''):
                    try:
                        search_results = WebDriverWait(self.driver(), 10).until(EC.presence_of_all_elements_located((By.XPATH,f"//*[@resource-id='com.instagram.android:id/row_search_user_username' and @text='{Username}']")))
                    except TimeoutException as e: return False
                    if search_results:
                        for i in search_results:
                            if str(i.text).lower() == str(Username).lower():
                                i.click()
                                break
                else:return False
            else:return False
                    
        # check searched user
        SearchedUsername = self.find_element('Searched Username','com.instagram.android:id/action_bar_title',By.ID)
        if SearchedUsername:
            if str(SearchedUsername.text).lower() == str(Username).lower():
                return True
        else: return False
        
    def seen_story(self):
        start_time = time.time()
        while time.time() - start_time < 120:
            if self.click_element('seen story',"//android.widget.ImageView[contains(@content-desc, 'story at column 1. Unseen.') and @resource-id='com.instagram.android:id/avatar_image_view']",timeout=2):
                self.click_element('ok',"//android.widget.Button[@text='OK']",timeout=2)
                self.click_element('ok',"//android.widget.Button[@text='OK']",timeout=2)
                self.click_element('Tap',"//android.widget.FrameLayout[@resource-id='com.instagram.android:id/reel_viewer_media_layout']",timeout=1)
                for i in range(10):
                    self.click_element('ok',"//android.widget.Button[@text='OK']",timeout=1)
                    # element = self.find_element('story list',"//*[@resource-id='com.instagram.android:id/reel_viewer_text_container']")
                    # if element:
                    #     try:
                    #         content_desc = element.get_attribute("content-desc")
                    #         match = re.search(r"story \d+ of (\d+)", content_desc)    
                    #         story_count = int(match.group(1))
                    #         for i in range(story_count):
                    HomeBtn = self.find_element('Home page','com.instagram.android:id/feed_tab',By.ID,timeout=0.1)
                    if HomeBtn:
                        break
                    self.tap_left()
                        # except Exception as e:
                        #     print(e)
                        #     self.tap_left()
                        
                    # HomeBtn = self.find_element('Home page','com.instagram.android:id/feed_tab',By.ID,timeout=1)
                    # if HomeBtn:
                    #     break
            HomeBtn = self.find_element('Home page','com.instagram.android:id/feed_tab',By.ID,timeout=2)
            if not HomeBtn:
                self.driver().back()
                break
            else:
                break
                
    def scroll_home_page(self):
        post_count = 0
        for i in range(10):
            LOGGER.info(f'{post_count}')
            try:
                post = self.find_element('post','com.instagram.android:id/row_feed_photo_profile_name',By.ID,timeout=2)
                if post:
                    location = post.location
                    x = location['x']
                    y = location['y']
                    try:
                        action = TouchAction(self.driver())
                        action.long_press(x=x, y=y).move_to(x=x, y=0).release().perform()
                    except Exception as e:
                        print(e)
                    if post.text == 'xanametaverse' or  post.text =='xana_gpt' or post.text =='xana_rio':
                        post_count+=1
                        if self.click_element('play button','com.instagram.android:id/view_play_button',By.ID,timeout=2):
                            random_sleep(5,9,reason='scrolling home page')
                        PostDetails = self.click_element('Post Details','com.instagram.android:id/row_feed_comment_textview_layout',By.ID,timeout=3)
                        PostDetails = self.find_element('Post Details','com.instagram.android:id/row_feed_comment_textview_layout',By.ID,timeout=3)
                        if PostDetails :
                            PostDetailsText = str(PostDetails.text).replace('\n',' ')
                            try:
                                if self.find_element('Like btn','//android.widget.ImageView[@content-desc="Like"]',timeout=2):
                                    post_ = postdetails.objects.get(details=PostDetailsText)
                                    random_count = post_.like
                                    try:
                                        like_count= self.find_element('like count','com.instagram.android:id/row_feed_textview_likes',By.ID)
                                        like_count_text = like_count.text
                                        if 'and' and 'others' in like_count_text: 
                                            like_counts = int(re.search(r'and (\d+(?:,\d+)*) others', like_count_text).group(1).replace(",", ""))
                                        else:
                                            like_counts = int(re.search(r"([\d,]+) (?:likes|others)?", like_count_text).group(1).replace(',',''))
                                            post_.target_like = like_counts
                                    except AttributeError:
                                        like_counts = 0
                                    LOGGER.info(f'like count was {like_counts} and require count is {random_count}')
                                    if like_counts >=random_count:
                                        pass
                                    else:
                                        self.click_element('Like btn','//android.widget.ImageView[@content-desc="Like"]',timeout=2)
                            except:
                                post_count+=1
                                post_details_text = str(PostDetailsText).lower()
                                if 'xana_gpt' in post_details_text:
                                    self.click_element('Like btn','//android.widget.ImageView[@content-desc="Like"]',timeout=2)
                    self.swip_display(4)
                else:
                    self.swip_display(4)
            except AttributeError as a:
                print(a)
            except Exception as e:
                print(e)
                
    def Follow(self):
        FollowBtn = self.find_element('Follow btn','com.instagram.android:id/profile_header_follow_button',By.ID)
        if FollowBtn.text != 'Following': FollowBtn.click()
        
    def ChangeReels(self):
        random_sleep(8,10)
        self.swip_display(9)
        
    def ReelsView(self,reels_watch_time=9):
        aa = ''
        for i in range(3):
            if not self.find_element('User account',f'//android.widget.TextView[@content-desc="{self.engagement_user}"]'):
                if not self.get_user_on_screen() :
                    self.driver().terminate_app('com.instagram.android')
                    self.driver().start_activity('com.instagram.android','com.instagram.mainactivity.MainActivity')
                    random_sleep(reason='Wait till the app is opened properly')
                    self.get_user_on_screen()
                    self.make_grid_view_on_display()
                    if not self.find_element('User account',f'//android.widget.TextView[@content-desc="{self.engagement_user}"]'):
                        continue
            for _ in range(3) :
                aa = self.find_element('first three reels','(//android.widget.RelativeLayout[@class="android.widget.RelativeLayout"])[1]')
                if aa : break
                self.click_element('reels page','//android.widget.ImageView[@content-desc="Reels"]')
            else: 
                continue
            buttons = aa.find_elements_by_class_name('android.widget.ImageView')
            if len(buttons) == 0 : continue
            else : buttons[0].click()
            for _ in range(int(reels_watch_time)): self.ChangeReels()
            for _ in range(6):
                if  not self.find_element('User account',f'//android.widget.TextView[@content-desc="{self.engagement_user}"]') : break
                self.driver().back()
            # self.click_element('back','//android.widget.ImageView[@content-desc="Back"]')
    
    def check_story_permission(self):
        self.click_element('Allow camera','com.android.packageinstaller:id/permission_message',timeout=3)
        ...

    def stories_avds_permissions(self):
        for _ in range(3) : self.click_element('allow','com.android.packageinstaller:id/permission_allow_button',By.ID,timeout=1)
        ...

    def ActionOnPost(self,swipe_number=4,like_count_list=[],Comment = False, Share = False, Save = True):
        self.click_element('play button','com.instagram.android:id/view_play_button',By.ID,timeout=2)
        time.sleep(2)
        for _ in range(7):
            self.swip_display(swipe_number)
            more = self.click_element('more','//android.widget.Button[@content-desc="more"]',timeout=3)
            time.sleep(1)
            PostDetails = self.find_element('Post Details','com.instagram.android:id/row_feed_comment_textview_layout',By.ID,timeout=3)
            if PostDetails :
                if '… more' in PostDetails.text:
                    ...
                PostDetailsText = str(PostDetails.text).replace('\n',' ')
                try:
                    post_ = postdetails.objects.get(details=PostDetailsText)
                    random_count = post_.like
                except:
                    random_count = random.randint(like_count_list[0], like_count_list[1])
                    target_comment = random.randint(10,20)
                    post_ = postdetails.objects.create(details=PostDetailsText,like=random_count,target_comment=target_comment)
                break

        if self.find_element('Like btn','//android.widget.ImageView[@content-desc="Like"]',timeout=2):
            try:
                like_count= self.find_element('like count','com.instagram.android:id/row_feed_textview_likes',By.ID)
                like_count_text = like_count.text
                if 'and' and 'others' in like_count_text: 
                    like_counts = int(re.search(r'and (\d+(?:,\d+)*) others', like_count_text).group(1).replace(",", ""))
                else:
                    like_counts = int(re.search(r"([\d,]+) (?:likes|others)?", like_count_text).group(1).replace(',',''))
                post_.target_like = like_counts
                post_.save()
            except AttributeError:
                like_counts = 0
            LOGGER.info(f'like count was {like_counts} and require count is {random_count}')
            if like_counts >=random_count:pass
            else:
                self.click_element('Like btn','//android.widget.ImageView[@content-desc="Like"]',timeout=2)
                post_.target_like+=1
                post_.save()
        if Comment and post_.comment < post_.target_comment:
            if self.user not in post_.commented_users.all():
                CommentBtn = self.click_element('Comment btn', '//android.widget.ImageView[@content-desc="Comment"]')
                if CommentBtn and PostDetails:
                    self.input_text(GetInstaComments(PostDetailsText), 'Comment input', 'com.instagram.android:id/layout_comment_thread_edittext', By.ID)
                    self.click_element('Post comment btn', '//android.widget.Button[@content-desc="Post"]/android.widget.LinearLayout/android.widget.TextView')
                    post_.comment += 1
                    post_.commented_users.add(self.user)
                    post_.save()
                    random_sleep(3)
                    CommentHeadingEle = self.find_element('Comment header', '//android.widget.TextView[@content-desc="Comments"]')
                    if CommentHeadingEle and CommentHeadingEle.text == 'Comments':
                        LOGGER.info('Comment page found')
                        self.click_element('Back btn', '//android.widget.ImageView[@content-desc="Back"]')
            else:
                LOGGER.info('User has already commented on this post')
                
        if Share:
            if self.click_element('Share btn','//android.widget.ImageView[@content-desc="Send post"]'):
                self.click_element('Add reel to your story','//android.widget.Button[@content-desc="Add reel to your story"]',timesleep=2)
                for _ in range(20):
                    if self.driver().current_activity == 'com.instagram.modal.TransparentModalActivity':
                        random_sleep(1,1,reason='Wait untill story opens')
                        break
                random_sleep(2,3,reason='share to story')
                self.stories_avds_permissions()
                self.click_element('introducing longer stories','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.Button',timeout=1)
                self.click_element('Ok btn2','//android.widget.Button[@content-desc="Continue watching stories"]',By.XPATH,timeout=1)
                self.click_element('Ok btn','com.instagram.android:id/primary_button',By.ID,timeout=1)
                self.click_element('Share to','//android.widget.FrameLayout[@content-desc="Share to"]',timeout=3)
                self.click_element('Share btn','com.instagram.android:id/share_story_button',By.ID,timeout=2)
                self.click_element('share done btn','//android.widget.Button[@content-desc="Done"]')
                random_sleep(5,10,reason='Let story uploads')
            
            user_sheet_drag = self.find_element('User sheet drag','com.instagram.android:id/bottom_sheet_drag_handle',By.ID,timeout=3)
            if user_sheet_drag:
                try:
                    self.driver().back()
                except:
                    self.driver().back()
                    # self.swipe_up()
            elif self.click_element('cancel','//android.widget.Button[@content-desc="Discard video"]',timeout= 3):
                try:
                    self.driver().back()
                except:
                    pass
        
        
        # save post
        if Save :
            self.click_element('Save post btn','//android.widget.ImageView[@content-desc="Add to Saved"]',page="user's post",timeout=2)      
        
        post = self.find_element('posts','com.instagram.android:id/action_bar_title',By.ID,timeout=3)
        if post:
            try:
                self.click_element('Back','//android.widget.ImageView[@content-desc="Back"]')
            except:
                self.driver().back()
        else:
            self.driver().back()
        
            
    def update_follow_user_info(self):
        followers = self.find_element('Followers','com.instagram.android:id/row_profile_header_textview_followers_count',By.ID)
        if followers:
            if followers.text:
                self.Follow_user.followers = followers.text
        following = self.find_element('Following','com.instagram.android:id/row_profile_header_textview_following_count',By.ID)
        if following:
            if following.text:
                self.Follow_user.following = following.text

        self.Follow_user.save()
        
    def random_real_action(self):
        random_ = random.choice(range(1,3))
        if random_ == 1 and int(self.user.followers) !=0:
            self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
            followers = self.find_element('Followers','com.instagram.android:id/row_profile_header_textview_followers_count',By.ID)
            self.click_element('select followers','com.instagram.android:id/row_profile_header_followers_container',By.ID)
            selected  = random.sample(range(1, 6), k=3)
            for i in selected:
                self.click_element('select story',f'//android.widget.ImageView[@content-desc="Profile picture"])[{i}]')
        else:
            self.click_element('Search btn','com.instagram.android:id/search_tab',By.ID)
            xpath = random.choice(['image_preview', 'image_button'])
            if not self.find_element('Random', f"//*[@resource-id='com.instagram.android:id/{xpath}']"):
                for i in range(2):
                    self.click_element('Back','com.instagram.android:id/action_bar_button_back',By.ID)
            self.click_element('Random', f"//*[@resource-id='com.instagram.android:id/{xpath}']")
            if xpath == 'image_preview':
                for i in range(3):
                    time.sleep(random.randint(8,10))
                    self.random_like()
                    self.swip_display(9)
            else:
                for i in range(3):
                    for _ in range(7):
                        self.swip_display(4)
                        PostDetails = self.find_element('Post Details','com.instagram.android:id/row_feed_comment_textview_layout',By.ID,timeout=3)
                        if PostDetails :
                            break
                    self.random_like()
                    self.swip_display(9)
                    
            if not self.click_element('Back','com.instagram.android:id/action_bar_button_back',By.ID):
                self.driver().back()
            
    def update_user_follow_info(self):
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
        ProfileName = self.find_element('Profile name','com.instagram.android:id/action_bar_large_title_auto_size',By.ID)
        if ProfileName:
            if ProfileName.text == self.user.username: 
                # self.user.following = 
                followers = self.find_element('Followers','com.instagram.android:id/row_profile_header_textview_followers_count',By.ID)
                if followers:
                    if followers.text:
                        self.user.followers = followers.text
                following = self.find_element('Following','com.instagram.android:id/row_profile_header_textview_following_count',By.ID)
                if following:
                    if following.text:
                        self.user.following = following.text
                self.user.save()
                LOGGER.info(f'User followers :{self.user.followers}\n User following :{self.user.following}')
                self.click_element('Home page','com.instagram.android:id/feed_tab',By.ID)

    def check_login(self,):
        for i in range(2):
            try:
                self.driver().start_activity('com.instagram.android','com.instagram.mainactivity.MainActivity')
            except:
                self.driver().activate_app('com.instagram.android')
            random_sleep(12,15,reason='open insta')
            try:
                if self.driver().current_activity == 'com.instagram.nux.activity.SignedOutFragmentActivity':
                    return False
                time.sleep(random.randint(3,7))
                if self.driver().current_activity == 'com.instagram.mainactivity.MainActivity':
                    HomeBtn = self.find_element('Home page','com.instagram.android:id/feed_tab',By.ID)
                    # ...
                    if HomeBtn : 
                        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
                        ProfileName = self.find_element('Profile name','com.instagram.android:id/action_bar_large_title_auto_size',By.ID)
                        if ProfileName:
                            try:
                                if not User_details.objects.filter(username=ProfileName.text).exists():
                                    # usser = User_details.objects.create(username = ProfileName.text,avd_pc = "PC11",avdsname = avd)
                                    return True
                                else:
                                    LOGGER.info(f'Your username is {ProfileName.text}')
                                    usser = User_details.objects.filter(username=ProfileName.text).first()
                                    usser.avd_pc = os.getenv('PC')
                                    usser.save()
                                    return True
                            except Exception as e:
                                print(e)
                                ...
                prof_pic = self.find_element('profile photo','//android.widget.Button[@content-desc="Profile photo"]')
                if prof_pic: 
                    username = self.find_element('username','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup[1]/android.view.View')
                    if not username:
                        username = self.find_element('usernname','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup[1]/android.view.View')
                    if not username:
                        text_views = [view for view in self.driver().find_elements(By.XPATH,"//android.view.View[@text]") if view.is_displayed()]
                        text_list = [te.text for te in text_views]
                        username = [text for text in text_list if text and text !=  "Log in" and text !="Create New account"][0]
                    # ...
                    try:
                        username = username.text
                    except  AttributeError as a:
                        print(a)
                    try:
                        if not User_details.objects.filter(username=username).exists():
                            return True
                        else:
                            LOGGER.info(f'Your username is {username}')
                            usser = User_details.objects.filter(username=username).first()
                            usser.avd_pc = os.getenv('PC')
                            usser.save()
                            return True
                    except Exception as e:
                        print(e)
                        ...
                    return True
                
                create_btn = self.find_element('create account btn','//android.widget.Button[@content-desc="Create new account"]')
                if create_btn:
                    return False

            except Exception as e:
                print(e)
                continue
            
    def click_btn(self,name=''):
        self.click_element('Edit profile btn',f'//android.widget.Button[@text={name}]')
        
    def get_user_on_screen(self):
        for _i in range(3):
            self.logger.info(f'Trying to get user on display of time {_i}')
            if self.search_user(self.engagement_user) :
                self.logger.info(f'Found the user on screen {self.engagement_user}')
                return True
        return False
                
    def make_grid_view_on_display(self):
        
        ele = self.find_element('Grid View','//android.widget.ImageView[@content-desc="Grid view"]')
        while not ele:
            self.swip_display(4)
            ele = self.find_element('Grid View','//android.widget.ImageView[@content-desc="Grid view"]')
            if ele: 
                break
        location = ele.location
        x = location['x']
        y = location['y']
        try:
            action = TouchAction(self.driver())
            action.long_press(x=x, y=y).move_to(x=x, y=0).release().perform()
        except Exception as e:
            self.logger.error(e)
        ...
        
    def EngagementOnUser(self,share=True):
        self.click_element('Follow btn','com.instagram.android:id/row_right_aligned_follow_button_stub',By.ID,timeout=3)
        self.make_grid_view_on_display()
        
        for indexx in range(4):
            if not self.find_element('User account',f'//android.widget.TextView[@content-desc="{self.engagement_user}"]'):
                if not self.get_user_on_screen() :
                    self.driver().terminate_app('com.instagram.android')
                    self.driver().start_activity('com.instagram.android','com.instagram.mainactivity.MainActivity')
                    random_sleep(reason='Wait till the app is opened properly')
                    self.get_user_on_screen()
                    self.make_grid_view_on_display()
                    if not self.find_element('User account',f'//android.widget.TextView[@content-desc="{self.engagement_user}"]'):
                        continue
                
            parent_element = self.find_element('list','android:id/list',By.ID)
            buttons = parent_element.find_elements_by_class_name('android.widget.Button')
            try :
                buttons[indexx].click()
                share = True if 2 == random.randint(1,4) else False
                self.ActionOnPost(Share=share,like_count_list=[250,350],Comment=self.comment)
                time.sleep(1)
                
                # post = self.find_element('posts','com.instagram.android:id/action_bar_title',By.ID,timeout=2).text
                # if post == 'Posts':
                #     self.click_element('Back','//android.widget.ImageView[@content-desc="Back"]')
            except : ...

    
    def get_gender(self):
        name = self.user.password.split('@')[0]
        import requests

        url = "https://v2.namsor.com/NamSorAPIv2/api2/json/genderBatch"

        payload = {
        "personalNames": [
            {
            "id": "b590b04c-da23-4f2f-a334-aee384ee420a",
            "firstName": f"{name}",
            "lastName": "Haring"
            }
        ]
        }
        headers = {
            "X-API-KEY": "41f4a1395234b593b9cbf9c5f0b68417",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        data = response.json()
        print(response.text)
        return data["personalNames"][0]["likelyGender"]

    def check_profile_updated(self):
        if self.user.updated == True : return
        
        self.is_bio_text = False
        self.is_profile_photo = False
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
        self.click_element('Edit profile btn','//android.widget.Button[@text="Edit profile"]')
        containers = self.find_element('dialoag','com.instagram.android:id/dialog_container',By.ID,timeout=5)
        if containers:
            self.click_element('Not now btn','//android.widget.Button[@text="Not now"]')
        bio = self.find_element('bio','com.instagram.android:id/bio',By.ID)
        if bio:
            text = bio.find_element(By.CLASS_NAME,'android.widget.EditText')
            if text.text:
               self.user.bio = text.text
               self.user.is_bio_updated = True
               self.user.save()
               self.is_bio_text = True
        if self.click_element('Edit profile btn', '//android.widget.Button[@text="Change profile photo"]', timeout=3) or self.click_element('Edit profile btn', '//android.widget.Button[@text="Edit picture or avatar"]', timeout=3):
            if self.find_element('remove profile btn', '//android.widget.Button[@text="Remove profile photo"]',timeout=3) or self.find_element('remove profile btn', '//android.view.ViewGroup[@content-desc="Remove current picture"]',timeout=3):
                self.user.updated = True
                self.user.save()
                self.is_profile_photo = True
        self.driver().back()
        self.click_element('done','//android.widget.ImageView[@content-desc="Back"]')
        random_sleep(2,3,reason='done')
        if self.is_bio_text and self.is_profile_photo:
            return True
        else:
            self.is_profile_photo = False
            self.user.updated = False
            self.user.save()
            return False
                

    def download_profilepic(self):
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        from webdriver_manager.chrome import ChromeDriverManager
        import time
        gender = self.get_gender()
        # gender = "female"
        driver = webdriver.Chrome(executable_path=ChromeDriverManager().install())
        driver.get("https://this-person-does-not-exist.com")
        time.sleep(2)
        gender_select = Select(driver.find_element(By.NAME,"gender"))
        if gender == 'female':
            gender_select.select_by_value("female")
        else:
            gender_select.select_by_value("male")
        time.sleep(1)
        age_select = Select(driver.find_element(By.NAME,"age"))
        age_select.select_by_value("19-25")
        time.sleep(1)
        reload_button = driver.find_element(By.XPATH,"//button[@id='reload-button']")
        reload_button.click()
        time.sleep(15)
        image_element = driver.find_element(By.XPATH,"//img[@id='avatar']")
        url =  image_element.get_attribute("src")
        time.sleep(3)

        driver.get('https://www.watermarkremover.io/upload')
        time.sleep(5)
        driver.find_element(By.XPATH,'//*[@id="root"]/div/div[1]/div[2]/div[2]/div/div[1]/div[1]/div[1]/div/span[2]').click()
        time.sleep(1)
        driver.find_element(By.XPATH,'//*[@id="modal-root"]/div[1]/div/div[1]/div[1]/input').send_keys(url)
        time.sleep(3)
        element = driver.execute_script('return document.evaluate("//button[text()=\'Submit\']", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;')
        driver.execute_script("arguments[0].click();", element)
        time.sleep(15)
        try:
            image_element = driver.find_elements(By.XPATH,"//img[@data-testid='pixelbin-image']")        
            url =  image_element[1].get_attribute("src")
        except:
            time.sleep(7)
            image_element = driver.find_elements(By.XPATH,"//img[@data-testid='pixelbin-image']")        
            url =  image_element[1].get_attribute("src")            
        driver.get(url)
        time.sleep(3)
        
        file_name = "prof_img/profile_pic.jpg"
        profile_pic_path = os.path.join(os.getcwd(), file_name)
        try:
            driver.get_screenshot_as_file(profile_pic_path)
        except:
            driver.get_screenshot_as_file(profile_pic_path)
        driver.quit()
        run_cmd(f'adb -s emulator-{self.adb_console_port} push {profile_pic_path} /sdcard/Download')
    
    def set_profile_pic(self):
        gender = self.get_gender()
        if gender == 'female':
            profile_path = "prof_img/female"
        else:
            profile_path =  "prof_img/male"
        folder = os.path.join(os.getcwd(), profile_path)
        os.makedirs(folder, exist_ok=True)
        file_name = os.listdir(profile_path)
        if len(file_name) <= 1:
            print('add more profile pic in directory')
            ...
            file_name = os.listdir(profile_path)
        profile_pic_path = os.path.join(os.getcwd(), f'{profile_path}/{random.choice(file_name)}')
        run_cmd(f'adb -s emulator-{self.adb_console_port} push {profile_pic_path} /sdcard/Download')
        new_file_name = f"{self.user.username}.jpg"
        new_profile_pic_path = os.path.join(os.getcwd(), f'{profile_path}/{new_file_name}')
        os.rename(profile_pic_path, new_profile_pic_path)
        used_pic_path = os.path.join(os.getcwd(), 'prof_img/used_pic')
        os.makedirs(used_pic_path, exist_ok=True)
        os.replace(new_profile_pic_path, os.path.join(used_pic_path, new_file_name))

    def upload_post(self):
        self.click_element('create_btn','//android.widget.FrameLayout[@content-desc="Camera"]')
        self.click_element('next','//android.widget.ImageView[@content-desc="Next"]')
        self.click_element('next','//android.widget.ImageView[@content-desc="Next"]')
        self.click_element('ok','//android.widget.Button[@content-desc="OK"]')
        done_ele = self.click_element('done','//android.widget.ImageView[@content-desc="Share"]')
        
        random_sleep(4,6,reason=' for upload post')
        if done_ele : return True
        else : return False
        
        
    def update_profile(self):
        if self.user.updated == True : return
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
        self.click_element('Edit profile btn','//android.widget.Button[@text="Edit profile"]')
        containers = self.find_element('dialoag','com.instagram.android:id/dialog_container',By.ID)
        if containers:
            self.click_element('Not now btn','//android.widget.Button[@text="Not now"]')
        bio = self.find_element('bio','com.instagram.android:id/bio',By.ID)
        if bio:
            text = bio.find_element(By.CLASS_NAME,'android.widget.EditText')
            if not text.text:
                text.click()
                bio_text = random_insta_bio()
                self.input_text(bio_text,'add bio','//android.widget.EditText')
                self.click_element('Done','//android.widget.Button[@content-desc="Done"]')
                random_sleep(4,5,reason='upload bio')
                self.click_element('done','//android.widget.Button[@content-desc="Done"]')
            else:
                self.click_element('done','//android.widget.Button[@content-desc="Done"]')
        time.sleep(2)
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
        self.click_element('Edit profile btn','//android.widget.Button[@text="Edit profile"]')
        if self.click_element('Edit profile btn','//android.widget.Button[@text="Change profile photo"]',timeout=5):
            if not self.find_element('remove profile btn','//android.widget.Button[@text="Remove profile photo"]'):
                self.set_profile_pic()
                self.click_element('Edit profile btn','//android.widget.Button[@text="New profile photo"]')
                self.click_element('gallery','//android.widget.TextView[@text="GALLERY"]')
                self.click_element('select gallery','com.instagram.android:id/gallery_folder_menu',By.ID)
                self.click_element('Edit profile btn','//android.widget.Button[@text="Other…"]')
                time.sleep(3)
                menu_btn = self.driver().find_element_by_accessibility_id('Show roots').click()
                self.click_element('download','//android.widget.TextView[@text="Downloads"]')
                self.click_element('choose pic','com.android.documentsui:id/icon_thumb',By.ID)
                self.click_element('next','//android.widget.ImageView[@content-desc="Next"]')
                time.sleep(3)
                self.click_element('next','//android.widget.ImageView[@content-desc="Next"]')
                random_sleep(14,15,reason='upload photo')
                self.click_element('next','//android.widget.ImageView[@content-desc="Next"]')
                random_sleep(10,12,reason='upload photo')
                self.upload_post()

        if self.click_element('Edit profile btn','//android.widget.Button[@text="Edit picture or avatar"]',timeout=5):
            if not self.find_element('remove profile btn', '//android.view.ViewGroup[@content-desc="Remove current picture"]',timeout=3):
                self.set_profile_pic()
                self.click_element('New profile btn','//android.view.ViewGroup[@content-desc="New profile picture"]')
                self.click_element('gallery','//android.widget.TextView[@text="GALLERY"]')
                self.click_element('select gallery','com.instagram.android:id/gallery_folder_menu',By.ID)
                self.click_element('other','//android.widget.Button[@text="Other…"]')
                time.sleep(3)
                menu_btn = self.driver().find_element_by_accessibility_id('Show roots').click()
                self.click_element('download','//android.widget.TextView[@text="Downloads"]')
                self.click_element('choose pic','com.android.documentsui:id/icon_thumb',By.ID)
                self.click_element('next','//android.widget.ImageView[@content-desc="Next"]')
                random_sleep(14,15,reason='upload photo')
                self.click_element('next','//android.widget.ImageView[@content-desc="Next"]')
                random_sleep(10,12,reason='upload photo')
                self.upload_post()
            else:
                self.driver().back()
                self.click_element('done','//android.widget.Button[@content-desc="Done"]')
        self.check_profile_updated()
        try:
            command = f"adb -s emulator-{self.adb_console_port} shell rm -r /sdcard/Download/*"
            subprocess.run(command, shell=True, check=True)
        except Exception as e:
            print(e)
        

            
            
    def send_views(self,Username='xanametaverse',comment=False):
        self.bot_follow = False
        if random.randint(2,3) ==1 :
            self.check_notification()
            self.seen_story()
            self.scroll_home_page()
        
        if self.find_element('insta keeps stoping','//android.widget.TextView[@resource-id="android:id/alertTitle"]',timeout=5):
            self.click_element('close insta','//android.widget.Button[@resource-id="android:id/aerr_close"]')
        self.update_user_follow_info()
        if int(self.user.followers) <= 20:
            is_updated = self.check_profile_updated()
            if not is_updated:
                self.update_profile()
        if comment and int(self.user.followers) >= 20:
            self.comment = True
        else:
            self.comment = False
        if not self.bot_follow:
            self.Follow_4_Follow()
        self.follow_rio()
        if self.search_user(Username):
            self.engagement_user = Username
            self.Follow()
            self.EngagementOnUser()
            self.ReelsView()
        
        multiple_users = ["niamwangi63","imanijohnson132","deandrewashington652","haraoutp","HaileyMitchell161","rayaanhakim","haileymitchell161","4nanyaShah",'minjipark11','MalikRobinson726','TylerEvans2913']
        random.shuffle(multiple_users)
        for Username_multiple in multiple_users :
            try :
                self.engagement_user = Username_multiple
                self.search_user(Username_multiple)
                self.Follow()
                self.EngagementOnUser()
                self.ReelsView()
                
            except : ...
        if not self.user.avd_pc:
            self.user.avd_pc = os.getenv('PC')
        self.today_avd.loc['avd']=self.emulator_name
        self.today_avd.to_csv('today_avd.csv',index=False)
        
    def scroller(self):
        self.search_user(Username='xanametaverse')
        self.swip_display(4)
        for _ in range(int(999999999)):
            self.click_element('Reels','//android.widget.ImageView[@content-desc="Reels"]')
            self.click_element('First reel','(//android.widget.ImageView[@content-desc="Reel by xanametaverse. Double tap to play or pause."])[1]')
            for _ in range():
                if self.driver().current_activity != "com.instagram.mainactivity.MainActivity":
                    self.driver().start_activity('com.instagram.android','com.instagram.mainactivity.MainActivity')
                    time.sleep(10)
                    self.scroller()
                self.ChangeReels()
            try:
                self.driver().back()
            except Exception as e:print(e)
            if self.driver().current_activity != "com.instagram.mainactivity.MainActivity":
                self.driver().start_activity('com.instagram.android','com.instagram.mainactivity.MainActivity')
                time.sleep(10)
                self.search_user(Username='xanametaverse')
                self.swip_display(4)
            
    def follow_xana_girl(self):
        if self.user.updated:
            self.search_user('xanametaverse_girl')
            self.Follow() 
        
    def follow_gpt(self):
        # self.driver().start_activity('com.instagram.android','com.instagram.mainactivity.MainActivity')
        self.search_user('xana_gpt')
        self.Follow() 
        
    def follow_rio(self,like=True):
        self.engagement_user = 'xana_rio'
        self.search_user('xana_rio')
        self.Follow()
        if like:
            ele = self.find_element('Grid View','//android.widget.ImageView[@content-desc="Grid view"]')
            while not ele:
                self.swip_display(4)
                ele = self.find_element('Grid View','//android.widget.ImageView[@content-desc="Grid view"]')
                if ele: 
                    break
            location = ele.location
            x = location['x']
            y = location['y']
            try:
                action = TouchAction(self.driver())
                action.long_press(x=x, y=y).move_to(x=x, y=0).release().perform()
            except Exception as e:
                print(e)
            for indexx in range(4):
                parent_element = self.find_element('list','android:id/list',By.ID)
                buttons = parent_element.find_elements_by_class_name('android.widget.Button')
                buttons[indexx].click()
                self.ActionOnPost(Share=False,like_count_list=[250,350])
        try:
            self.click_element('Home page','com.instagram.android:id/feed_tab',By.ID)
            for i in range(2):
                self.click_element('Search btn','com.instagram.android:id/search_tab',By.ID)
        except Exception as e:
            print(e)
        
    def Follow_4_Follow(self):
        top_accounts = ['instagram', 'cristiano', 'therock', 'kimkardashian', 'kyliejenner', 'beyonce', 'justinbieber', 'taylorswift', 'neymarjr', 'leomessi', 'arianagrande', 'kendalljenner', 'natgeo', 'jlo', 'nickiminaj', 'khloekardashian', 'mileycyrus', 'katyperry', 'kourtneykardash', 'nike', 'kevinhart4real', 'theellenshow', 'realmadrid', 'fcbarcelona', 'iamcardib', 'zendaya', 'badgalriri', 'nasa', 'victoriassecret', 'davidbeckham', 'shakira', 'billieeilish', 'iamzlatanibrahimovic', 'drake', 'justintimberlake', 'emmawatson', 'jamesrodriguez10', 'lelepons', 'vindiesel', 'nickjonas', 'maluma', 'shawnmendes', 'emmahill', 'gigihadid', 'iamhalsey', 'dualipa', 'brunomars', 'harrystyles', 'laliga', 'priyankachopra', 'blakelively', 'zacefron', 'jenniferaniston', 'niallhoran', 'kourtneykardash', 'chrissyteigen', 'hugogloss', 'maddieziegler', 'iamamyjackson', 'caradelevingne', 'emmastone', 'serenawilliams', 'realbarbarapalvin', 'adidas', 'jw.anderson', 'lucyhale', 'selenagomez', 'snoopdogg', 'krisjenner', 'jasonstatham', 'alessandraambrosio', 'virat.kohli', 'caraashe', 'garethbale11', 'zara', 'lilireinhart', 'twhiddleston', 'harrykane', 'milliebobbybrown', 'vanessahudgens', 'karliekloss', 'shaymitchell', 'daddario', 'gigihadid', 'dovecameron', 'bellahadid', 'reesewitherspoon', 'robertdowneyjr', 'chrisbrownofficial', 'realdonaldtrump', 'travisscott', 'anushkasharma', 'ashleybenson', 'gisele', 'imdb', 'khloekardashian', 'milliebobbybrown', 'jonasbrothers', 'mileycyrus', 'maisie_williams', 'louisvuitton', 'krisjenner', 'jenniferlopez', 'zacbrownband', 'priyankachopra', 'marvel', 'milliebobbybrown', 'kimkardashian', 'zendaya']

        CanSearchUsers = User_details.objects.filter(status='ACTIVE', can_search=True).order_by('-updated_at')
        CanSearchUsers = [user for user in CanSearchUsers if int(user.followers) <20]
        if self.user in CanSearchUsers:
            CanSearchUsers.remove(self.user)
        top_accounts  = random.sample(top_accounts, k=1)
        for Follow_user in CanSearchUsers[:3]:
            try:
                self.Follow_user = Follow_user
                if self.search_user(Follow_user.username):
                    self.Follow()
                    self.update_follow_user_info()
                    print('---->')
                else:
                    print('2222---->')
                    self.Follow_user.can_search = False
                    self.Follow_user.save()
            except Exception as e :
                print(e)

        

        #     try:
        #         if self.search_user(account):
        #             self.Follow()
        #     except Exception as e:
        #         print(e)
            
    def random_action(self):
        
        self.click_element('Search btn','com.instagram.android:id/search_tab',By.ID)
        random_index = random.sample(range(0, 9), k=random.randint(3,6))
        
        for indexx in random_index:
            self.choose_random_image(indexx)
            self.ActionOnPost(swipe_number=3,RandomPostFollow=True,RandomPostFollowRation=30,like_count_list=[250,350])
            
            
    def Profile_update(self):
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
        ProfileName = self.find_element('Profile name','com.instagram.android:id/action_bar_large_title_auto_size',By.ID)
        if ProfileName:
            if ProfileName.text == self.user.username:
                print('yesss')

    def connect_urban(self, country):
        LOGGER.debug('Check if urbanvpn is installed')
        if not self.driver().is_app_installed('com.urbanvpn.android'):
            cmd = f"adb -s emulator-{self.adb_console_port} install -t -r -d -g {os.path.join(BASE_DIR, 'apk/urban-vpn-1-0-80.apk')}"
            p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
            p.wait()
            self.driver().activate_app('com.urbanvpn.android')
            self.click_element('skip', 'com.urbanvpn.android:id/choose_free_text_view', By.ID)
            self.click_element('agree', 'com.urbanvpn.android:id/acceptEULAButton', By.ID)
            self.click_element('accept', 'com.urbanvpn.android:id/agreeEnableButton', By.ID)
            self.click_element('accept', '//android.widget.Button[@text="Agree"]', By.ID)
            self.click_element('accept', 'com.urbanvpn.android:id/agreeEnableButton', By.ID)
            list_ = self.find_element('list','com.android.settings:id/list', By.ID)
            if list_ : 
                list_.find_element_by_xpath('//android.widget.TextView[@resource-id="android:id/title" and @text="UrbanVPN - Safe Browsing"]').click()
                self.click_element('enable btn', 'com.android.settings:id/switch_widget', By.ID)
                self.click_element('OK','android:id/button1', By.ID)
                random_sleep(1,2)
                self.driver().back()
                random_sleep()
                self.driver().back()
                # self.driver().terminate_app('com.urbanvpn.android')
                # self.driver().activate_app('com.urbanvpn.android')
                self.click_element('agree2', 'com.urbanvpn.android:id/agreeButton', By.ID)
                self.click_element('accept', 'com.urbanvpn.android:id/agreeEnableButton', By.ID)
            # self.click_element('skip', 'com.urbanvpn.android:id/skipButton', By.ID)
            self.click_element('search', 'com.urbanvpn.android:id/searchView', By.ID)
            self.input_text(country, 'search','com.urbanvpn.android:id/searchView', By.ID)
            country_btn = self.find_element('Country Btn', 'com.urbanvpn.android:id/suggestion_name', By.ID)
            if country_btn and country_btn.text == country:
                self.click_element('Country Btn', 'com.urbanvpn.android:id/suggestion_name', By.ID)
            self.click_element('OK','android:id/button1', By.ID)
            random_sleep(10,10)
            # self.click_element('start', 'com.urbanvpn.android:id/controlButton', By.ID, timeout=3)
            for i in range(10):
                timer =  self.find_element('timer','com.urbanvpn.android:id/timerView', By.ID)
                if timer and  timer.text is not None and timer.text != '00 : 00 : 00':
                    return True
                if i == 4 :
                    timer =  self.find_element('timer','com.urbanvpn.android:id/timerView', By.ID)
                    if timer and  timer.text is not None and timer.text == '00 : 00 : 00':
                        self.click_element('start', 'com.urbanvpn.android:id/controlButton', By.ID, timeout=3)
                else:
                    random_sleep(3,3)
            return False
        else:
            for i in range(5):
                self.driver().activate_app('com.urbanvpn.android')
                random_sleep(5,5)
                if self.click_element('search', 'com.urbanvpn.android:id/searchView', By.ID, timeout=5):
                    self.input_text(country, 'search','com.urbanvpn.android:id/searchView', By.ID, timeout=5)
                    country_btn = self.find_element('Country Btn', 'com.urbanvpn.android:id/suggestion_name', By.ID)
                    if country_btn and country_btn.text == country:
                        self.click_element('Country Btn', 'com.urbanvpn.android:id/suggestion_name', By.ID)
                        random_sleep(10,10)
                        timer =  self.find_element('timer','com.urbanvpn.android:id/timerView', By.ID)
                        if timer and  timer.text is not None and timer.text == '00 : 00 : 00' and self.find_element('...', '//android.widget.TextView[@resource-id="com.urbanvpn.android:id/indicatorValueView" and @text="..."]'):
                            self.click_element('play', 'com.urbanvpn.android:id/controlButton', By.ID)
                            random_sleep(7,9)
                        timer =  self.find_element('timer','com.urbanvpn.android:id/timerView', By.ID)
                        if timer and  timer.text is not None and timer.text != '00 : 00 : 00':
                            return True
                if self.find_element('alert' , 'android:id/alertTitle', By.ID):
                    self.click_element('later', '//android.widget.Button[@text="LATER"]')
                if self.find_element('message', 'android:id/parentPanel', By.ID):
                    self.driver().back()
            else: return False



def terminat_idel_connection():
        db_params = {
            'database': 'surviral',
            'user': 'surviraluser',
            'password': 'Surviral#806',
            'host': 'surviral-project.c4jxfxmbuuss.ap-southeast-1.rds.amazonaws.com',
            'port': '5432'
        }

        # SQL query to identify and terminate idle connections
        terminate_idle_connections_query = """
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = current_database() -- Optional: specify your database name here
        AND pid <> pg_backend_pid() -- Don't terminate the current connection
        AND state = 'idle' -- Look for idle connections
        AND state_change < current_timestamp - INTERVAL '1 hour';  -- Idle for more than 1 hour
        """

        # Connect to the database
        conn = psycopg2.connect(**db_params)

        # Create a cursor object
        cur = conn.cursor()

        try:
            # Execute the query to terminate idle connections
            cur.execute(terminate_idle_connections_query)
            # Commit the changes
            conn.commit()
            print("Idle connections have been terminated.")
        except Exception as e:
            # Rollback in case of any error
            conn.rollback()
            print(f"An error occurred: {e}")
        finally:
            # Close communication with the database
            cur.close()
            conn.close()
            