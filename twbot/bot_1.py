import difflib
import random
from faker import Faker
from pathlib import Path
from xml.etree.ElementTree import Comment
from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from appium.webdriver.common.touch_action import TouchAction
from numpy import number
from ppadb.client import Client as AdbClient
from selenium.common.exceptions import InvalidSessionIdException
from selenium.webdriver.common.keys import Keys
from core.models import user_detail
from twbot.models import User_details
import parallel
from conf import APPIUM_SERVER_HOST, APPIUM_SERVER_PORT
from conf import TWITTER_VERSIONS, RECAPTCHA_ALL_RETRY_TIMES
from conf import WAIT_TIME
from constants import COUNTRY_CODES
from exceptions import CannotStartDriverException
from twbot.models import *
from twbot.utils import *
from twbot.vpn.nord_vpn import NordVpn
from utils import get_installed_packages
from utils import run_cmd
from verify import RecaptchaAndroidUI, FuncaptchaAndroidUI
from accounts_conf import GETSMSCODE_PID
from .utils import get_sms,get_number,ban_number, GetInstaComments, INSTA_PROFILE_BIO_LIST, NEW_INSTA_ACC_BIO
timeout = 10
import pandas as pd


def random_sleep(min_sleep_time=1, max_sleep_time=5,reason=''):
    sleep_time = random.randint(min_sleep_time, max_sleep_time)
    if not reason:LOGGER.debug(f'Random sleep: {sleep_time}')
    else:LOGGER.debug(f'Random sleep: {sleep_time} for {reason}')
    time.sleep(sleep_time)

class InstaBot:
    def __init__(self, emulator_name, start_appium=True, start_adb=True,
                 appium_server_port=APPIUM_SERVER_PORT, adb_console_port=None):
        self.user = ''
        self.emulator_name = emulator_name
        self.user_avd = UserAvd.objects.get(name=emulator_name)
        self.logger = LOGGER
        #  self.kill_bot_process(appium=True, emulators=True)
        self.app_driver = None
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
        fake = Faker()
        name = fake.name()
        name_li = str(name).split(' ')
        self.fname = name_li[0]
        self.password = self.fname+'@1234'
        self.full_name = name_li[0]+name_li[1]
        self.birth_year = str(random.randint(1990,2003))
        self.birth_date = str(random.randint(1,28))
        if len(self.birth_date)==1:
            self.birth_date = f"0{self.birth_date}"
        # birth_month_li = ['January','February','March','April','May','June','July','August','September','October','November', 'December']
        birth_month_li = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov', 'Dec']
        self.birth_month = random.choice(birth_month_li)

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
            #  'appium:skipLogCapture': True,
        }

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

    def get_avd_options(self):
        emulator_options = [
            # Set the emulation mode for a camera facing back or front
            #  '-camera-back', 'emulated',
            #  '-camera-front', 'emulated',

            #  '-phone-number', str(self.phone) if self.phone else '0',

        ]

        if self.user_avd.timezone:
            emulator_options += ['-timezone', f"{self.user_avd.timezone}"]
        LOGGER.debug(f'Other options for emulator: {emulator_options}')
        return emulator_options

    def get_device(self):
        name = self.emulator_name

        #  LOGGER.debug(f'Start AVD: {name}')

        #  if not self.device:
        #      LOGGER.debug(f'Start AVD: ["emulator", "-avd", "{name}"] + '
        #                   f'{self.get_avd_options()}')
        #      self.device = subprocess.Popen(
        #          #  ["emulator", "-avd", f"{name}"],
        #          ["emulator", "-avd", f"{name}"] + self.get_avd_options(),
        #          stdout=subprocess.PIPE,
        #          stderr=subprocess.PIPE,
        #          universal_newlines=True,
        #      )
        #      time.sleep(5)
        #      log_activity(
        #          self.user_avd.id,
        #          action_type="StartAvd",
        #          msg=f"Started AVD for {self.user_avd.name}",
        #          error=None,
        #      )

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

    def check_apk_installation(self):
        
        # breakpoint()
        LOGGER.debug('Check if cyberghost is installed')
        if not self.driver().is_app_installed('de.mobileconcepts.cyberghost'):
            LOGGER.debug('cyberghost is not installed, now install it')
            self.driver().install_app('apk/cyberghost.apk')
        else:
            self.driver().terminate_app('de.mobileconcepts.cyberghost')

        
        LOGGER.debug('Check if instagram is installed')
        # if self.driver().is_app_installed("com.instagram.android"):
        #     self.driver().remove_app('com.instagram.android')
        
        if not self.driver().is_app_installed("com.instagram.android"):
            LOGGER.debug('instagram is not installed, now install it')
            self.install_apk(self.adb_console_port, "instagram")
            log_activity(
                self.user_avd.id,
                action_type="Installinstagram",
                msg=f"instagram app installed successfully.",
                error=None,
            )
        else:
            LOGGER.debug('Check instagram version')
            apk_version = self.get_apk_version('com.instagram.android')
            random_sleep()
            if apk_version != '273.1.0.16.72':
                LOGGER.debug('Install instagram new version')
                self.Install_new_insta()
                # breakpoint()
            else:
                self.driver().terminate_app('com.instagram.android')
            
            
            
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
                "appWaitDuration": 10000
                # "newCommandTimeout": 30,#Don't use this
                #  "systemPort": "8210",
                #  'isHeadless': True,
                # "udid": f"emulator-{self.emulator_port}",
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
            
        return self.app_driver

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
        device = self.adb.device(f'emulator-{self.adb_console_port}')
        if device:
            arch = device.shell('getprop ro.product.cpu.abi').strip()
            LOGGER.debug(f'Architecture of current device: {arch}')
            return arch

            
            
    def find_element(self, element, locator, locator_type=By.XPATH,
            page=None, timeout=10,timesleep=1,
            condition_func=EC.presence_of_element_located,
            condition_other_args=tuple()):
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
            self.driver().swipe(start_x = x1,start_y = y1,end_x = x1,end_y = y2, duration=random.randrange(1050, 1250))
        except Exception as e : print(e)

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


    def back_until_number(self,number):
        try:
            for i in range(number):
                time.sleep(0.3)
                self.driver().back()
        except Exception as e :
            self.logger.info(f'Got an error in Go back to the number : {e}')

    def phone_number_proccess(self):
        phone_number = get_number()
        if phone_number:
            for i in range(2):
                print(phone_number)
                self.input_text(phone_number,'phone number input','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.EditText')
                next_btn = self.driver().find_element(By.XPATH,'//android.widget.Button[@content-desc="Next"]')
                next_btn.click()
                otp = self.find_element('otp','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
                if otp:
                    pass
                else:
                    something_wrong_error = self.find_element('something went wrong','//android.view.View[@content-desc="Something went wrong. Please try again later."]')
                    if something_wrong_error:
                        return False
                time.sleep(5)
                otp = get_sms(phone_number)
                count = 0
                time.sleep(13)
                while not otp:
                    otp = get_sms(phone_number)
                    time.sleep(10)
                    count+=1
                    if count == 5:
                        ban_number(phone_number)
                        self.back_until_number(2)
                        phone_number = get_number()
                        if phone_number:
                            continue
                if otp:
                    print(otp)
                    self.input_text(otp,'input otp','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
                    next_btn = self.driver().find_element(By.XPATH,'//android.widget.Button[@content-desc="Next"]')
                    next_btn.click()
                    break
            return phone_number
        if not otp:
            print('account creation by phone number not successfull')
            return False
        

    def profile_img_download(self):
        '''
        downloading the file and saving it in download folder
        '''
        url = "https://source.unsplash.com/random"
        file_name = "prof_img/profile_pic.jpg"
        profile_pic_path = os.path.join(os.getcwd(), file_name)
        # file_name = '/media/rk/0B29CA554279F37D/Workspace/New_Insta/AVD_setup-main/prof_img/profile_pic.jpg'
        LOGGER.info(f"profile image path : {profile_pic_path}")
        with open(profile_pic_path, "wb") as file:
            response = requests.get(url)
            file.write(response.content)
        time.sleep(3)

        run_cmd(f'adb -s emulator-{self.adb_console_port} push {profile_pic_path} /sdcard/Download')
        
#             all_elements_for_select_download_id = 'com.android.documentsui:id/drawer_roots' #com.android.documentsui:id/drawer_roots
#             self.driver()
#             all_elements_for_select_download_li = [self.app_driver.find_element_by_id(all_elements_for_select_download_id)]
#             all_elements_for_select_download_li_loop = False
#             for i in all_elements_for_select_download_li:
#                 inside_all_ele = i.find_elements_by_xpath('//*')
#                 for ia in inside_all_ele:
#                     if ia.get_attribute('text') == 'Downloads':
#                         ia.click()
#                         all_elements_for_select_download_li_loop = True
#                         break

#                 if all_elements_for_select_download_li_loop == True :break

    def add_profile_pic(self):
        self.click_element('click on add_rofile','//android.widget.Button[@content-desc="Add picture"]')
        self.profile_img_download()
        time.sleep(3)
        self.click_element('choose from gallery','//android.view.View[@content-desc="Choose from Gallery"]')
        time.sleep(3)
        menu_btn = self.driver().find_element_by_accessibility_id('Show roots').click()
        self.click_element('download','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout[2]/android.widget.FrameLayout/android.widget.ListView/android.widget.LinearLayout[2]/android.widget.LinearLayout')
        self.click_element('choose pic','com.android.documentsui:id/icon_thumb',By.ID)
        self.click_element('also share post','//android.widget.Switch[@content-desc="Also share this picture as a post"]/android.view.ViewGroup/android.widget.FrameLayout/android.widget.Switch')
        self.click_element('Done','//android.widget.Button[@content-desc="Done"]')
        time.sleep(10)
        skip_profile_pic_id = 'com.instagram.android:id/skip_button'
        self.click_element('skip add profile pic btn',skip_profile_pic_id,By.ID)  
        self.click_element('Skip2','com.instagram.android:id/negative_button',By.ID)
        self.click_element('follow instagram','//android.widget.Button[@content-desc="Follow Instagram"]')
        self.click_element('next arrow','//android.widget.Button[@content-desc="Next"]/android.widget.ImageView')
        return True

    def delete_avd(self,emulator_name):
        try:
            cmd = f'avdmanager delete avd --name {emulator_name}'
            p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
        except Exception as e:
            pass
    
    def swip_until_match(self,comperison_xpath,comperison_text):
        rect_ele = self.driver().find_element_by_xpath(comperison_xpath).rect
        start_x = rect_ele['x'] + rect_ele['width'] / 2
        start_y = rect_ele['y'] + rect_ele['height'] / 2
        end_x = start_x
        end_y = start_y + rect_ele['height']
        LOGGER.debug(f'start_x: {start_x}, start_y: {start_y}, end_x: {end_x}, end_y: {end_y}')
        while True:
            self.driver().swipe(start_x=start_x,start_y=start_y,end_x=end_x,end_y=end_y,duration=random.randrange(200, 250))
            time.sleep(0.80)
            comperison_xpath_text = self.driver().find_element_by_xpath(comperison_xpath).text
            if comperison_xpath_text == comperison_text:
                break
            
    def set_birth_date(self):
        self.click_element('birthday input','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.widget.EditText')
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
        self.next_btn()
        
    
    def add_bio(self):
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
        for i in range(4):
            self.swip_display(4)
        # com.instagram.android:id/find_people_card_button
        self.click_element('Add Bio btn','com.instagram.android:id/find_people_card_button',By.ID)
        self.bio = NEW_INSTA_ACC_BIO
        self.input_text(self.bio,"User's Bio", 'com.instagram.android:id/caption_edit_text',By.ID)
        check = self.click_element('tick btn','//android.widget.Button[@content-desc="Done"]/android.widget.ImageView')
        if check:
            return True
        
    def next_btn(self):    
        next_btn = self.driver().find_element(By.XPATH,'//android.widget.Button[@content-desc="Next"]').click()

    def create_account(self):
        self.driver().activate_app('com.instagram.android')
        
        time.sleep(10)
        create_btn = self.find_element('create account btn','//android.widget.Button[@content-desc="Create new account"]')
        if create_btn:
            self.click_element('create account btn','//android.widget.Button[@content-desc="Create new account"]')
        else:
            return False
            
        phone_number = self.phone_number_proccess()
        if not phone_number:
            return False
        
        self.input_text(self.full_name,'first name input','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
        self.next_btn()
        self.input_text(self.password,'password input','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
        self.next_btn()
        self.click_element('save info','//android.widget.Button[@content-desc="Save"]')
        #  ----------------

        self.set_birth_date()
        time.sleep(10)
        green_tick = self.find_element('Green Tick','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.widget.ImageView')
        if green_tick:
            self.i_username = self.driver().find_element(By.XPATH,'/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText').text
            self.next_btn()
        else:
            user_ = self.find_element('username','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
            if user_:
                self.i_username = str(self.full_name)+str(random.randint(1000,9999))
                self.input_text(self.i_username,'input user_name','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
                time.sleep(3)
                self.next_btn()
        i_agree = self.find_element('i_agree','//android.widget.Button[@content-desc="I agree"]')
        if i_agree:
            self.click_element('I agree','//android.widget.Button[@content-desc="I agree"]')
            time.sleep(13)
            add_profile = self.find_element('add_profile_btn','//android.widget.Button[@content-desc="Add picture"]')
            check_add_bio = None
            if add_profile:
                self.add_profile_pic()
                check_add_bio = self.add_bio()
                
            if check_add_bio:
                user = User_details.objects.create(
                        avdname=self.emulator_name,
                        username=self.i_username,
                        number=phone_number,
                        password=self.password,
                        birth_date=self.birth_date,
                        birth_month=self.birth_month,
                        birth_year=self.birth_year,
                        bio=self.bio,
                        is_bio_updated=True,
                        updated=True,
                        status='ACTIVE'
                        )
                
                return user
            else:
                return False
        # else:
        #     return False
    
            
    # def restart_Insta(self):
    #     self.driver().activate_app('com.instagram.android')
    #     random_sleep(3,5)
    #     self.driver().terminate_app('com.instagram.android')
    #     random_sleep(4,5)
    #     self.driver().activate_app('com.instagram.android')
    #     random_sleep(3,5)
    #     apk_version = self.get_apk_version('com.instagram.android')
    #     random_sleep()
    #     if apk_version != '273.1.0.16.72':
    #         self.Install_new_insta()
    #         random_sleep()
    #         self.driver().activate_app('com.instagram.android')
            
    def start_app(self,activity = ''):
        time.sleep(3)
        try:
            time.sleep(3)
            if activity.lower() == 'login':
                LoginBtn = self.find_element('login btn','//android.view.View[@content-desc="Log in"]',timeout=15)
                if LoginBtn: 
                    if LoginBtn.text == 'Log in':
                        return True
            elif activity.lower() == 'sign up':
                self.click_element('Sign up btn','com.instagram.android:id/sign_up_with_email_or_phone',By.ID,timeout=3)
                allow_contacts_id = 'com.instagram.android:id/primary_button_row'
                self.click_element('Allow contact',allow_contacts_id,By.ID, timeout=3)

            time.sleep(0.5)
            try:self.driver().hide_keyboard()
            except Exception as e: ...

            return True
        except Exception as e:
            self.logger.info(f'Got an error in opening the instagram {e}')

    def Install_new_insta(self,):
        cmd = f"adb -s emulator-{self.adb_console_port} install -t -r -d -g {os.path.join(BASE_DIR, 'apk/instagram.apk')}"
        log_activity(
            self.user_avd.name,
            action_type="InstallInstagramApk",
            msg=f"Installation of instagram apk",
            error=None,
        )
        p = subprocess.Popen(
            [cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL
        )
        p.wait()

    def get_apk_version(self,package_name):
        dumpsys_output = subprocess.check_output(['adb', 'shell', 'dumpsys', 'package', package_name]).decode('utf-8')
        version_line = [line.strip() for line in dumpsys_output.split('\n') if 'versionName' in line][0]
        version_name = version_line.split('=')[1]
        return version_name

    def login(self,username,password):
        self.user = User_details.objects.filter(username=username).first()
        # self.driver().activate_app('com.instagram.android')
        # breakpoint()
        # self.start_app('login')
        try:
            self.driver().start_activity('com.instagram.android','com.instagram.mainactivity.MainActivity')
        except:
            self.driver().activate_app('com.instagram.android')
        time.sleep(12)
        LOGGER.info("inside login methods")
        
        # breakpoint()
        self.click_element('Allow Cookies','//android.widget.Button[@content-desc="Allow all cookies"]')
        HomeBtn = self.find_element('Home page','com.instagram.android:id/feed_tab',By.ID)
        if HomeBtn : return True
        prof_pic = self.find_element('profile photo','//android.widget.Button[@content-desc="Profile photo"]')
        if prof_pic:
            self.click_element('Login btn','//android.widget.Button[@content-desc="Log in"]')
            # /hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText
            self.input_text(password,'Password','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
            self.click_element('Login btn','//android.widget.Button[@content-desc="Log in"]')
            # save login info
            SaveInfo = self.find_element('save info','//android.view.View[@content-desc="Save your login info?"]',timeout=20)
            if SaveInfo:
                self.click_element('Save','//android.widget.Button[@content-desc="Save"]')
            time.sleep(5)
            self.click_element('Allow Cookies','//android.widget.Button[@content-desc="Allow all cookies"]')
            HomeBtn = self.find_element('Home page','com.instagram.android:id/feed_tab',By.ID)
            if HomeBtn : return True
            current_activity = self.driver().current_activity
            if current_activity != 'com.instagram.mainactivity.MainActivity':
                self.login(username,password)
            # breakpoint()
        else:
            if self.input_text(username,'username','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText'):pass
            else:
                self.input_text(username,'Username','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
            
            if self.input_text(password,'Password','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText'):pass
            else:
                self.input_text(password,'Password','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
            self.click_element('Login btn','//android.widget.Button[@content-desc="Log in"]')

        # save login info
        SaveInfo = self.find_element('save info','//android.view.View[@content-desc="Save your login info?"]',timeout=20)
        if SaveInfo:
            self.click_element('Save','//android.widget.Button[@content-desc="Save"]')
            time.sleep(7)
            self.click_element('Allow Cookies','//android.widget.Button[@content-desc="Allow all cookies"]')
            HomeBtn = self.find_element('Home page','com.instagram.android:id/feed_tab',By.ID)
            if HomeBtn : return True
        else:
            # check need otp or not?
            # self.driver().find_elements(By.TAG_NAME,'android.widget.EditText')
            unable_login = self.find_element('unable_login','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView')
            if unable_login:
                if unable_login.text =='Unable to log in':
                    self.user.status = 'LOGIN_ISSUE'
                    self.user.save()
                    df.loc['avd']=self.emulator_name
                    df.to_csv('delete_avd.csv', index=False)
                    LOGGER.info(f'add this {delete_avd.avdsname} avd in delete local avd list')
                    return False


            check_number_h1 = self.find_element('Confirm its you H1','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup/android.view.View[1]',timeout=12)
            if check_number_h1:
                if check_number_h1.text == "Confirm it's you":
                    self.user.status = 'LOGIN_ISSUE'
                    self.user.save()
                    df.loc['avd']=self.emulator_name
                    df.to_csv('delete_avd.csv', index=False)
                    LOGGER.info(f'add this {delete_avd.avdsname} avd in delete local avd list')
                    return False
                
            account_not_find = self.find_element('account not find','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView')
            if account_not_find:
                if account_not_find.text == "Can't Find Account":
                    self.user.status = 'LOGIN_ISSUE'
                    self.user.save()
                    df.loc['avd']=self.emulator_name
                    df.to_csv('delete_avd.csv', index=False)
                    LOGGER.info(f'add this {delete_avd.avdsname} avd in delete local avd list')
                    return False
                
            check_number_h1 = self.find_element('Confirm its you H1','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup/android.view.View[1]',timeout=2)
            if check_number_h1:
                if check_number_h1.text == "Confirm it's you":
                    self.user.status = 'LOGIN_ISSUE'
                    self.user.save()
                    df.loc['avd']=self.emulator_name
                    df.to_csv('delete_avd.csv', index=False)
                    LOGGER.info(f'add this {delete_avd.avdsname} avd in delete local avd list')
                    return False

            appeal = self.find_element('appleal','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.Button')
            if appeal:
                self.user.status = 'LOGIN_ISSUE'
                self.user.save()
                df.loc['avd']=self.emulator_name
                df.to_csv('delete_avd.csv', index=False)
                LOGGER.info(f'add this {delete_avd.avdsname} avd in delete local avd list')
                return False
                
            check_number_h2 = self.find_element('Confirm its you H2','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup/android.view.View[2]',timeout=2)
            if check_number_h2:
                if check_number_h2.text == "To secure your account, we'll send you a security code to this phone number":
                    self.user.status = 'LOGIN_ISSUE'
                    self.user.save()
                    df.loc['avd']=self.emulator_name
                    df.to_csv('delete_avd.csv', index=False)
                    LOGGER.info(f'add this {delete_avd.avdsname} avd in delete local avd list')
                    return False
            

        time.sleep(3)
        # To secure your account, we'll send you a security code to this phone number
        current_activity = self.driver().current_activity
        if current_activity != 'com.instagram.mainactivity.MainActivity':
            self.login(self,username,password)
        
        
        # check profile
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
        ProfileName = self.find_element('Profile name','com.instagram.android:id/action_bar_large_title_auto_size',By.ID)
        if ProfileName:
            if ProfileName.text == username: 
                return True
            else : return False
        else: return False
        
    def search_user(self,Username):
        self.click_element('Search btn','com.instagram.android:id/search_tab',By.ID)
        self.click_element('Search input','com.instagram.android:id/action_bar_search_edit_text',By.ID)
        self.input_text(Username,'Search input','com.instagram.android:id/action_bar_search_edit_text',By.ID)
        #  find which is correct user
        time.sleep(3)
        search_results = self.driver().find_elements(By.XPATH,"//*[@resource-id='com.instagram.android:id/row_search_user_username']")
        if search_results:
            for i in search_results:
                if i.text == Username:
                    i.click()
                    break
        else:
            abc = self.driver().find_elements(By.XPATH,'//*')
            for i in abc: 
                if i.text == 'xanametaverse':
                    i.click()
                    
        SearchedUsername = self.find_element('Searched Username','com.instagram.android:id/action_bar_title',By.ID)
        # check searched user
        if SearchedUsername:
            SearchedUsername.text == Username
            return True
        else: return False        
        
    def Follow(self):
        FollowBtn = self.find_element('Follow btn','com.instagram.android:id/profile_header_follow_button',By.ID)
        if FollowBtn.text != 'Following': FollowBtn.click()
        
    def ChangeReels(self):
        random_sleep(15,20)
        self.swip_display(9)
        
    def ReelsView(self,reels_watch_time=9):
        self.swip_display(4)
        action = True
        # for _ in range(int(reels_watch_time)):
        self.click_element('Reels','//android.widget.ImageView[@content-desc="Reels"]')
        self.click_element('First reel','(//android.widget.ImageView[@content-desc="Reel by xanametaverse. Double tap to play or pause."])[1]')
        for _ in range(9):
            self.ChangeReels()
        self.driver().back()
        action = False
            
    def ActionOnPost(self,swipe_number=4,RandomPostFollow = False,Like=True,Comment = True, Share = True, Save = True,random_= False,RandomPostFollowRation=100,LikeRation=100,CommentRation=100,ShareRation=100,SaveRation=100):
        Percentage_list = [i for i in range(100)]
            
        # Random post follow
        RandomFollowRequire = random.choice(Percentage_list)
        if RandomPostFollow and RandomFollowRequire < int(RandomPostFollowRation):
            self.click_element('Follow btn','com.instagram.android:id/row_right_aligned_follow_button_stub',By.ID)
        self.click_element('play button','com.instagram.android:id/view_play_button',By.ID)
        time.sleep(2)
        for _ in range(7):
            self.swip_display(swipe_number)
            PostDetails = self.find_element('Post Details','com.instagram.android:id/row_feed_comment_textview_layout',By.ID,timeout=3)
            if PostDetails : 
                PostDetailsText = PostDetails.text
                break
            
        # like
        if random_:
            anoynmas = [1,2]
            need = random.choice(anoynmas)
        else:
            need=1
        if need ==1:
            try:
                like_count= self.find_element('like count','com.instagram.android:id/row_feed_textview_likes',By.ID)
                like_count_text = like_count.text
                like_counts = int(re.search(r'\d+', like_count_text).group())
            except AttributeError:
                like_counts = 0
            # breakpoint()
            if like_counts >=200:pass
            else:
                LikeRequire = random.choice(Percentage_list)
                if Like and LikeRequire < int(LikeRation) :
                    self.click_element('Like btn','//android.widget.ImageView[@content-desc="Like"]',timeout=2)
        
        # LikeRequire = random.choice(Percentage_list)
        # if Like and LikeRequire < int(LikeRation) :
        #     self.click_element('Like btn','//android.widget.ImageView[@content-desc="Like"]',timeout=2)
        
        # comment
        # if random_:
        anoynmass = [1,2,3]
        need = random.choice(anoynmass)
        # else:
        #     need=1
        if need ==1:
            CommentRequire = random.choice(Percentage_list)
            if Comment and CommentRequire < int(CommentRation):
                print(Comment,CommentRequire)
                # breakpoint()
                CommentBtn = self.click_element('Comment btn','//android.widget.ImageView[@content-desc="Comment"]')
                if not PostDetails : self.logger.info('Posts details didnt found')
                if CommentBtn and PostDetails:
                    random_sleep(3)

                    self.input_text(GetInstaComments(PostDetailsText),'Comment input','com.instagram.android:id/layout_comment_thread_edittext',By.ID)
                    self.click_element('Post comment btn','//android.widget.Button[@content-desc="Post"]/android.widget.LinearLayout/android.widget.TextView')

                    random_sleep(3)
                    CommentHeadingEle = self.find_element('Comment header','//android.widget.TextView[@content-desc="Comments"]')
                    if CommentHeadingEle:
                        if CommentHeadingEle.text == 'Comments':
                            self.logger.info('Comment page found')
                            self.click_element('Back btn','//android.widget.ImageView[@content-desc="Back"]')

        #  share
        ShareRequire = random.choice(Percentage_list)
        if Share and ShareRequire < int(ShareRation):
            self.click_element('Share btn','//android.widget.ImageView[@content-desc="Send post"]')
            add_to_storyBTN = self.click_element('Add reel to your story','//android.widget.Button[@content-desc="Add reel to your story"]',timesleep=2)
            if add_to_storyBTN:
                random_sleep(10,15,reason='Wait untill story opens')
                
                # permissions
                # self.click_element('Allow btn for camera permission','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout[2]/android.widget.Button[2]',timeout=2)
                # self.click_element('Allow btn for audio','com.android.packageinstaller:id/permission_allow_button',By.ID,timeout=2)
                # self.click_element('Allow btn for storage','com.android.packageinstaller:id/permission_allow_button',By.ID,timeout=2)
                self.click_element('Ok btn2','//android.widget.Button[@content-desc="Continue watching stories"]',By.XPATH,timeout=2)
                self.click_element('Ok btn','com.instagram.android:id/primary_button',By.ID,timeout=2)
            
                self.click_element('Share to','//android.widget.FrameLayout[@content-desc="Share to"]')
                self.click_element('Share to your story','com.instagram.android:id/row_add_to_story_container',By.ID)
                self.click_element('Share btn','com.instagram.android:id/share_story_button',By.ID)
                
                self.click_element('share done btn','//android.widget.Button[@content-desc="Done"]')
                random_sleep(5,10,reason='Let story uploads')
                
            user_sheet_drag = self.find_element('User sheet drag','com.instagram.android:id/bottom_sheet_drag_handle',By.ID,timeout=3)
            if user_sheet_drag:self.driver().back()
            
        # save post
        SaveRequire = random.choice(Percentage_list)
        if Save and SaveRequire < int(SaveRation):
            self.click_element('Save post btn','//android.widget.ImageView[@content-desc="Add to Saved"]',page="user's post",timeout=2)
            
        self.driver().back()
        # go back if post is open
        # Explorare_post = self.find_element('Explore element','//android.widget.TextView[@content-desc="Explore"]',timeout=2)
        # if Explorare_post:
        #     if Explorare_post.text == 'Explore':
        #         self.click_element('Back','//android.widget.ImageView[@content-desc="Back"]')
        # PostsPage = self.find_element('post ele','com.instagram.android:id/media_group_container',By.ID,timeout=2)
        # if PostsPage:
        #     # if PostsPage.text == 'Posts':
        #         self.click_element('Back','//android.widget.ImageView[@content-desc="Back"]')
    
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
                
                
    def EngagementOnUser(self,comment):
        self.click_element('Grid View','//android.widget.ImageView[@content-desc="Grid view"]')
        share = random.randint(1,9)
        # share = 9
        PostCount = 1
        for column in range(1,4):
            for indexx in range(1,4):
                for _ in range(5):
                    post_ele = self.click_element(f'post : {PostCount}', f'//android.widget.Button[@content-desc="Reel by XANA | Metaverse at row {column}, column {indexx}"]')
                    if post_ele:
                        #if you want random then random_=True
                        Share = True if share == PostCount else False
                        comment = True if Share and comment else False
                        random_ = False if PostCount == (1 or 2 or 3) else True
                        self.ActionOnPost(Comment=comment,Share=Share,random_=random_,Like=False)
                        time.sleep(1)
                        break
                    else : 
                        if _ == 2 or 4:
                            self.swipe_up()
                        else:
                            self.swip_display(4)
                PostCount+=1

            # self.swipe_up()
            
    def choose_random_image(self,indexx=0):
        all_post = self.find_element('All post','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[2]/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.FrameLayout/androidx.recyclerview.widget.RecyclerView')
        if all_post:
            all_post = self.driver().find_elements(By.XPATH,'/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[2]/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.FrameLayout/androidx.recyclerview.widget.RecyclerView/*')
            aa = [i for i in all_post if i.get_attribute('resource-id') == 'com.instagram.android:id/image_button']
            if not indexx:
                random.choice(aa).click()
            else:
                aa[indexx].click()
    def change_profile_pic(self):
        random_sleep()
        self.click_element('Edit profile btn','//android.widget.ImageView[@content-desc="Edit profile picture"]')
        newProfilePicEle = self.click_element('New Profile pic','//android.view.ViewGroup[@content-desc="New profile picture"]/android.widget.TextView')
        if newProfilePicEle:
            ...
            
            
    
    def edit_profile(self):
        edit_btn = self.find_element('Edit profile btn','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[2]/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout[1]/android.widget.LinearLayout[1]/android.widget.Button[1]/android.widget.FrameLayout/android.widget.Button')
        if edit_btn:
            if edit_btn.text == 'Edit profile': 
                edit_btn.click()
                
                self.change_profile_pic()
                
                
                self.input_text(random.choice(INSTA_PROFILE_BIO_LIST),"User's Bio", '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[2]/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout[2]/android.view.ViewGroup[3]/android.widget.EditText')
        ...
            
            
    def send_views(self,Username='xanametaverse',comment=False):
        # self.Follow_4_Follow()
        TodayOpenAVD.objects.create(name=self.emulator_name)
        self.search_user(Username)
        self.Follow()
        self.EngagementOnUser(comment=comment)
        self.ReelsView()
    
    def scroller(self):
        self.search_user(Username='xanametaverse')
        self.swip_display(4)
        action = True        
        for _ in range(int(999999999)):
            self.click_element('Reels','//android.widget.ImageView[@content-desc="Reels"]')
            self.click_element('First reel','(//android.widget.ImageView[@content-desc="Reel by xanametaverse. Double tap to play or pause."])[1]')
            for _ in range(9):
                self.ChangeReels()
            self.driver().back()
    
    def follow_rio(self):
        self.driver().start_activity('com.instagram.android','com.instagram.mainactivity.MainActivity')
        self.search_user('rio_noborderz')
        self.Follow() 
        for i in range(3):self.swipe_up()
        # self.click_element('Grid View','//android.widget.ImageView[@content-desc="Grid view"]')
        # share = random.randint(1,9)
        # share = 9

        PostCount = 1
        # for column in range(1):
        for indexx in range(1,4):
                for _ in range(5):
                    # breakpoint()
                    post_ele = self.click_element(f'post : {PostCount}', f'//android.widget.Button[@content-desc="Photo by Rio Noborderz at Row 1, Column {indexx}"]')
                    if post_ele:
                        #if you want random then random_=True
                        Share = False
                        comment =  False
                        # random_ = False if PostCount == (1 or 2 or 3) else True

                        self.ActionOnPost(Comment=comment,Share=Share,Save=False)
                        time.sleep(1)
                        break
                    else : 

                        if _ == 2 or 4:
                            self.swipe_up()
                        else:
                            self.swip_display(4)
                PostCount+=1

        


        
        
    def Follow_4_Follow(self):
        self.update_user_follow_info()
        CanSearchUsers = user_detail.objects.using('monitor').filter(can_search=True,status='ACTIVE',followers=0)
        try:   
            for Follow_user in CanSearchUsers[:100]:
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
    def random_action(self):
        
        self.click_element('Search btn','com.instagram.android:id/search_tab',By.ID)
        random_index = random.sample(range(0, 9), k=random.randint(3,6))
        
        for indexx in random_index:
            self.choose_random_image(indexx)
            self.ActionOnPost(swipe_number=3,RandomPostFollow=True,RandomPostFollowRation=30)
            
            
    def Profile_update(self):
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
        ProfileName = self.find_element('Profile name','com.instagram.android:id/action_bar_large_title_auto_size',By.ID)
        if ProfileName:
            if ProfileName.text == self.user.username:
                print('yesss')
                
                
        
