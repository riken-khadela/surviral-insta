import difflib
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
from .utils import get_sms,get_number,ban_number, GetInstaComments, INSTA_PROFILE_BIO_LIST
timeout = 10


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
        LOGGER.debug('Terminate cyberghost vpn')
        vpn = CyberGhostVpn(self.driver())
        if vpn.is_app_installed():
            vpn.terminate_app()

        LOGGER.debug('Check if cyberghost is installed')
        self.driver().install_app('apk/cyberghost.apk')
    

        
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
                cmd = f"adb -s emulator-{port} install {os.path.join(BASE_DIR, 'apk/instagram.apk')}"
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
        self.check_apk_installation()
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

    # def find_element(self, element, locator, locator_type=By.XPATH,
    #         page=None, timeout=10,
    #         condition_func=EC.presence_of_element_located,
    #         condition_other_args=tuple()):
    #     """Find an element, then return it or None.
    #     If timeout is less than or requal zero, then just find.
    #     If it is more than zero, then wait for the element present.
    #     """
    #     time.sleep(3)
    #     try:
    #         if timeout > 0:
    #             wait_obj = WebDriverWait(self.app_driver, timeout)
    #             ele = wait_obj.until(
    #                     condition_func((locator_type, locator),
    #                         *condition_other_args))
    #         else:
    #             self.logger.debug(f'Timeout is less or equal zero: {timeout}')
    #             ele = self.driver().find_element(by=locator_type,
    #                     value=locator)
    #         if page:
    #             self.logger.debug(
    #                     f'Found the element "{element}" in the page "{page}"')
    #         else:
    #             self.logger.debug(f'Found the element: {element}')
    #         return ele
    #     except (NoSuchElementException, TimeoutException) as e:
    #         if page:
    #             self.logger.debug(f'Cannot find the element "{element}"'
    #                     f' in the page "{page}"')
    #         else:
    #             self.logger.debug(f'Cannot find the element: {element}')
    #         return False

    # def click_element(self, element, locator, locator_type=By.XPATH,
    #         timeout=timeout,page=None):
    #     time.sleep(3)
        
    #     """Find an element, then click and return it, or return None"""
    #     ele = self.find_element(element, locator, locator_type, timeout=timeout,page=page)
    #     if ele:
    #         ele.click()
    #         LOGGER.debug(f'Clicked the element: {element}')
    #         return ele

    # def input_text(self, text, element, locator, locator_type=By.XPATH,
    #         timeout=timeout, hide_keyboard=True,page=None):
    #     time.sleep(3)
        
    #     """Find an element, then input text and return it, or return None"""
    #     try:
    #         if hide_keyboard :
    #             self.logger.debug(f'Hide keyboard')
    #             try:self.driver().hide_keyboard()
    #             except:None

    #         ele = self.find_element(element, locator, locator_type=locator_type,
    #                 timeout=timeout,page=page)
    #         if ele:
    #             ele.clear()
    #             ele.send_keys(str(text))
    #             self.logger.debug(f'Inputed "{text}" for the element: {element}')
    #             return ele
    #     except Exception as e :
    #         self.logger.info(f'Got an error in input text :{element} {e}')

    # def find_element(self, element, locator, locator_type=By.XPATH,
    #         page=None, timeout=10,
    #         condition_func=EC.presence_of_element_located,
    #         condition_other_args=tuple()):
    #     """Find an element, then return it or None.
    #     If timeout is less than or requal zero, then just find.
    #     If it is more than zero, then wait for the element present.
    #     """
    #     time.sleep(3)
    #     try:
    #         if timeout > 0:
    #             wait_obj = WebDriverWait(self.driver(), timeout)
    #             ele = wait_obj.until(
    #                     condition_func((locator_type, locator),
    #                         *condition_other_args))
    #         else:
    #             self.logger.debug(f'Timeout is less or equal zero: {timeout}')
    #             ele = self.driver().find_element(by=locator_type,
    #                     value=locator)
    #         if page:
    #             self.logger.debug(
    #                     f'Found the element "{element}" in the page "{page}"')
    #         else:
    #             self.logger.debug(f'Found the element: {element}')
    #         return ele
    #     except (NoSuchElementException, TimeoutException) as e:
    #         if page:
    #             self.logger.debug(f'Cannot find the element "{element}"'
    #                     f' in the page "{page}"')
    #         else:
    #             self.logger.debug(f'Cannot find the element: {element}')
    #         return False


    
    # def click_element(self, element, locator, locator_type=By.XPATH,
    #         timeout=timeout,page=None):
    #     time.sleep(3)
        
    #     """Find an element, then click and return it, or return None"""
    #     ele = self.find_element(element, locator, locator_type, timeout=timeout,page=page)
    #     if ele:
    #         ele.click()
    #         LOGGER.debug(f'Clicked the element: {element}')
    #         return ele
        

    # def input_text(self, text, element, locator, locator_type=By.XPATH,
    #         timeout=timeout, hide_keyboard=True,page=None):
    #     time.sleep(3)
        
    #     """Find an element, then input text and return it, or return None"""
    #     try:
    #         if hide_keyboard :
    #             self.logger.debug(f'Hide keyboard')
    #             try:self.driver().hide_keyboard()
    #             except:None

    #         ele = self.find_element(element, locator, locator_type=locator_type,
    #                 timeout=timeout,page=page)
    #         if ele:
    #             ele.clear()
    #             ele.send_keys(text)
    #             self.logger.debug(f'Inputed "{text}" for the element: {element}')
    #             return ele
    #     except Exception as e :
    #         self.logger.info(f'Got an error in input text :{element} {e}')
            
            
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
            self.driver().swipe(start_x = x1,start_y = y1,end_x = x1,end_y = y2, duration=random.randrange(1050, 1250),)
        except Exception as e : print(e)
    
    def put_number(self):
        try:
            all_permission_id2 = 'com.android.packageinstaller:id/permission_allow_button'
            all_permission_ele = self.find_element('Allow files',all_permission_id2,By.ID,timeout=4)
            if all_permission_ele:
                all_permission_ele.click()
            else:
                allow_file_permission_id = 'com.android.permissioncontroller:id/permission_allow_button'
                self.click_element('allow file permission',allow_file_permission_id,By.ID,timeout=3)
            
            allow_file_permission_id = 'com.android.permissioncontroller:id/permission_allow_button'
            self.click_element('allow file permission',allow_file_permission_id,By.ID,timeout=3)
            

            self.driver().find_element(By.ID,'com.instagram.android:id/country_code_picker').click()
            search_country_input_id = 'com.instagram.android:id/search'
            country = 'Hong Kong'
            self.driver().find_element(By.ID,'com.instagram.android:id/search').send_keys(country)
            select_country_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout[2]/android.widget.LinearLayout/android.widget.ListView/android.widget.FrameLayout'
            self.click_element('Select country',select_country_xpath)

            phone_number = get_number()
            number = phone_number
            self.logger.info(f'number : {number}')
            time.sleep(2)
            self.input_text(number[3:],'Phone number field','com.instagram.android:id/phone_field',locator_type=By.ID)
            self.logger.info(f'number : {number}')
            try:
                please_wait = self.driver().find_element_by_id('com.instagram.android:id/notification_bar').is_displayed()
                if please_wait :
                    return False
            except : None
            time.sleep(3)
            self.click_element('Next btn','com.instagram.android:id/left_tab_next_button',By.ID)

            return phone_number
        except Exception as e :
            print(e)
            print('secound step')
            return False
        
    def put_otp(self, otp):
        try :
            time.sleep(0.5)
            self.driver().find_element_by_id('com.instagram.android:id/confirmation_field').send_keys(otp)

            time.sleep(0.5)
            self.driver().find_element_by_id('com.instagram.android:id/button_text').click()

            return True
        except Exception as e :
            self.logger.info(f'Got an error in Put the OTP : {e}')
        
        return False

    def go_back_to_number(self):
        try:
            time.sleep(0.3)
            self.driver().back()
            time.sleep(0.3)
            self.driver().back()
            time.sleep(0.3)
            self.driver().find_element_by_id('com.instagram.android:id/primary_button').click()
        except Exception as e :
            self.logger.info(f'Got an error in Go back to the number : {e}')

    def phone_number_proccess(self):
        phone_number = get_number()
        if phone_number:
            country_code = 852
            pattern = "^" + re.escape(str(country_code))
            final_numbar = re.sub(pattern, "", str(phone_number))
            phone_field = self.driver().find_element(By.ID,'com.instagram.android:id/phone_field')
            phone_field.clear()
            phone_field.send_keys(final_numbar)
            next_btn = self.driver().find_element(By.ID,'com.instagram.android:id/button_text')
            next_btn.click()
            time.sleep(5)
            otp = get_sms(phone_number)
            count = 0
            time.sleep(10)
            while not otp:
                otp = get_sms(phone_number)
                count+=1
                if count == 5:
                    ban_number(phone_number)
                    self.go_back_to_number()
                    self.phone_number_proccess()
            if otp:
                print(otp)
                self.driver().hide_keyboard()
                otp_field = self.driver().find_element(By.ID,'com.instagram.android:id/confirmation_field')
                otp_field.send_keys(otp)
                next_btn = self.driver().find_element(By.ID,'com.instagram.android:id/button_text')
                next_btn.click()
        return phone_number

    def profile_img_download(url, file_name):
        '''
        downloading the file and saving it
        '''
        with open(file_name, "wb") as file:
            response = requests.get(url)
            file.write(response.content)

            return file

    def start_file_manager(self):
        import os
        
        # self.app_driver.start_activity('com.instagram.android',"com.instagram.nux.activity.BloksSignedOutFragmentActivity")
        url = "https://source.unsplash.com/random"
        file_name = "prof_img/profile_pic.jpg"
        profile_pic_path = os.path.join(os.getcwd(), file_name)
        # from instagram.management.commands.merged import profile_img_download
        self.profile_img_download(url,file_name)
        LOGGER.info(f"profile image path : {profile_pic_path}")
        
        send_pic = run_cmd(f'adb -s emulator-{self.adb_console_port} push {profile_pic_path} /sdcard/Download')
        time.sleep(1)
        try:
            self.app_driver.activate_app('com.android.documentsui')
        except Exception as e:None
        try:
            self.app_driver.start_activity('com.android.documentsui',"com.android.documentsui.files.FilesActivity")
        except Exception as e:None
        Show_roots_xpath = '//android.widget.ImageButton[@content-desc="Show roots"]'
        self.click_element('triple rows for more folder',Show_roots_xpath,By.XPATH)
        time.sleep(4)
        try:
                all_elements_for_select_download_id = 'com.android.documentsui:id/drawer_roots' #com.android.documentsui:id/drawer_roots
                self.driver()
                all_elements_for_select_download_li = [self.app_driver.find_element_by_id(all_elements_for_select_download_id)]
                all_elements_for_select_download_li_loop = False
                for i in all_elements_for_select_download_li:
                    inside_all_ele = i.find_elements_by_xpath('//*')
                    for ia in inside_all_ele:
                        if ia.get_attribute('text') == 'Downloads':
                            ia.click()
                            all_elements_for_select_download_li_loop = True
                            break

                    if all_elements_for_select_download_li_loop == True :break
        except :None
        time.sleep(3)
        all_images_for_profile_pic_id = 'com.android.documentsui:id/dir_list'
        all_images_for_profile_pic_list1 = [self.find_element('All documents in directory',all_images_for_profile_pic_id,By.ID,'select img from download')]
        for i in all_images_for_profile_pic_list1:
            every_ele_insideof_downloads = i.find_elements_by_xpath('//*')
            for iwa in every_ele_insideof_downloads:
                try: 
                    iwa.click()
                    find_pic = True
                    # self.app_driver.back()
                    break
                except:None
        self.app_driver.activate_app('com.android.documentsui')
        # self.app_driver.start_activity('com.android.documentsui',"com.android.documentsui.files.FilesActivity")
        if send_pic and find_pic:return True
        else:return False

    def after_not_error(self):
        try:
            facebook_connect_skip = 'com.instagram.android:id/skip_button'
            facebook_connect_skip_btn =  self.driver().find_element(By.ID,facebook_connect_skip)
            if facebook_connect_skip_btn:
                facebook_connect_skip_btn.click()
            time.sleep(3)
            skip_follow_fri_id = 'com.instagram.android:id/negative_button'
            skip_follow_fri_btn = self.driver().find_element(By.ID,skip_follow_fri_id)
            if skip_follow_fri_btn:
                skip_follow_fri_btn.click()
            time.sleep(3)
            add_pic = True
            if add_pic:
                url = "https://source.unsplash.com/random"
                file_name = "prof_img/profile_pic.jpg"
                profile_pic_path = os.path.join(os.getcwd(), file_name)
                self.profile_img_download(url,file_name)
                
                send_pic = run_cmd(f'adb -s emulator-{self.adb_console_port} push {profile_pic_path} /sdcard/Download')
                time.sleep(3)

                next_btn = self.driver().find_element(By.ID,'com.instagram.android:id/button_text')
                next_btn.click()
                time.sleep(2)
                choose_from_lib_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ListView/android.widget.FrameLayout[3]/android.widget.LinearLayout'                  	
                choose_from_lib_btn = self.driver().find_element(By.XPATH,choose_from_lib_xpath)
                if choose_from_lib_btn:
                    choose_from_lib_btn.click()

                show_root_xpath = '//android.widget.ImageButton[@content-desc="Show roots"]'
                show_root_btn = self.driver().find_element(MobileBy().ACCESSIBILITY_ID,'Show roots')
                if show_root_btn:
                    show_root_btn.click()

                download_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout[2]/android.widget.FrameLayout/android.widget.ListView/android.widget.LinearLayout[2]'
                download_btn = self.driver().find_element(By.XPATH,download_xpath)
                if download_btn:
                    download_btn.click()
                time.sleep(2)
                self.driver().refresh()
                all_images_for_profile_pic_id = 'com.android.documentsui:id/dir_list'
                select_pic_btn = self.driver().find_element(By.XPATH,'/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.support.v7.widget.RecyclerView/android.widget.LinearLayout/android.widget.RelativeLayout')
                if select_pic_btn:
                    select_pic_btn.click()
                time.sleep(2)
                allow_btn_id = 'com.android.packageinstaller:id/permission_allow_button'
                allow_btn  = self.driver().find_element(By.ID,allow_btn_id)
                if allow_btn:
                    allow_btn.click()
                time.sleep(3)
                next_save_btn = self.driver().find_element(MobileBy().ACCESSIBILITY_ID,'Next')
                if next_save_btn:
                    next_save_btn.click()
            
                time.sleep(3)
                next_btn = self.driver().find_element(By.ID,'com.instagram.android:id/button_text')
                next_btn.click()
                time.sleep(3)
                next_next_save_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[3]/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ViewSwitcher/android.widget.ImageView'
                next_next_save_btn = self.driver().find_element(By.XPATH,next_next_save_xpath).click()
                if send_pic and next_next_save_btn:return True

            else:
                skip_profile_pic_id = 'com.instagram.android:id/skip_button'
                self.click_element('skip add profile pic btn',skip_profile_pic_id,By.ID)            

                skip_people_suggestions_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[3]/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ViewSwitcher/android.widget.ImageView'
                skip_people_suggestions_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[3]/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ViewSwitcher/android.widget.ImageView'
                skip_ppl_bool =self.click_element('skip people suggestion btn',skip_people_suggestions_xpath,By.XPATH)
                if skip_ppl_bool:return True
        except:None


    def create_account(self):
        self.driver().activate_app('com.instagram.android')
        time.sleep(7)
        singn_up_btn_home_id = 'com.instagram.android:id/sign_up_with_email_or_phone'
        create_acc = self.driver().find_element(By.ID,singn_up_btn_home_id)
        if create_acc:
            create_acc.click()
        else:
            self.create_account()
        try:
            all_permission_id2 = 'com.android.packageinstaller:id/permission_allow_button'
            all_permission_ele = self.driver().find_element(By.ID,all_permission_id2)
            if all_permission_ele:
                all_permission_ele.click()
        except:...
        try:
            allow_file_permission_id = self.driver().find_element(By.ID,'com.android.permissioncontroller:id/permission_allow_button')
            if allow_file_permission_id:
                allow_file_permission_id.click()
        except:...
        self.driver().hide_keyboard()
        self.driver().find_element(By.ID,'com.instagram.android:id/country_code_picker').click()
        country = 'Hong Kong'
        self.driver().find_element(By.ID,'com.instagram.android:id/search').send_keys(country)
        select_country_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout[2]/android.widget.LinearLayout/android.widget.ListView/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.TextView'
        self.driver().find_element(By.XPATH,select_country_xpath).click()
        phone_number = self.phone_number_proccess()
        
        import random
        from faker import Faker
        fake = Faker()
        name = fake.name()
        name_li = str(name).split(' ')
        fname = name_li[0]
        password = fname+'@1234'
        continue_without_sync = 'com.instagram.android:id/continue_without_ci'
        birth_year_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.DatePicker/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.NumberPicker[3]/android.widget.EditText'
        birth_year = str(random.randint(1990,2003))
        birth_date_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.DatePicker/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.NumberPicker[2]/android.widget.EditText'
        birth_date = str(random.randint(1,28))
        birth_month_xpath = '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.DatePicker/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.NumberPicker[1]/android.widget.EditText'
        birth_month_li = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        birth_month = random.choice(birth_month_li)
        birth_next = 'com.instagram.android:id/button_text'
        username_suggested_next = 'com.instagram.android:id/button_text'
        self.driver().hide_keyboard()
        self.driver().find_element(By.ID,'com.instagram.android:id/full_name').send_keys(name)
        time.sleep(2)
        self.driver().find_element(By.ID,'com.instagram.android:id/password').send_keys(password)
        time.sleep(2)
        self.driver().find_element(By.ID,'com.instagram.android:id/continue_without_ci').click()
        time.sleep(3)
        date_input = self.driver().find_element(By.XPATH,birth_date_xpath)
        date_input.clear()
        date_input.send_keys(birth_date)
        time.sleep(2)
        
        month_input = self.driver().find_element(By.XPATH,birth_month_xpath)
        month_input.clear()
        month_input.send_keys(birth_month)
        time.sleep(1)
        
        year_input = self.driver().find_element(By.XPATH,birth_year_xpath)
        year_input.clear()
        year_input.send_keys(birth_year)
        year_input.click()
        self.driver().hide_keyboard()
        time.sleep(3)
        
        next_btn = self.driver().find_element(By.ID,'com.instagram.android:id/button_text')
        next_btn.click()
        time.sleep(3)
       
        
        try:
            why_birth_id = 'com.instagram.android:id/field_detail_link'
            self.driver().hide_keyboard()
            why_birth_btn = self.driver().find_element(By.ID,why_birth_id)
            if why_birth_btn:
                why_birth_btn.click()
            close_birth_id = 'com.instagram.android:id/action_bar_button_back'    
            close_birth_btn = self.driver().find_element(By.ID,close_birth_id)
            if close_birth_btn:
                close_birth_btn.click()
            next_btn = self.driver().find_element(By.ID,'com.instagram.android:id/button_text')
            next_btn.click()
            
        except:...
        
        username_text = 'com.instagram.android:id/field_title_second_line'
        i_username = False
        try:
            username_ele = self.find_element("Users's Username",username_text,By.ID)
            i_username = username_ele.text
            next_btn = self.driver().find_element(By.ID,'com.instagram.android:id/button_text')
            next_btn.click()
        except:None
        try:
            if not i_username:
                i_username = str(fname)+str(random.randint(10000000,99999999))
                username_input_id = 'com.instagram.android:id/username'
                username_input_btn = self.driver().find_element(By.ID,username_input_id)
                username_input_btn.clear()
                time.sleep(2)
                username_input_btn.send_keys(i_username)
                time.sleep(2)
                next_btn = self.driver().find_element(By.ID,'com.instagram.android:id/button_text')
                next_btn.click()

        except : None
        restriction_ele = self.find_element('restriction ele for 30 days','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[2]/android.widget.FrameLayout/android.webkit.WebView/android.webkit.WebView/android.view.View/android.view.View[1]/android.view.View/android.view.View/android.view.View[2]/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View/android.view.View[1]/android.view.View/android.view.View/android.view.View[2]',By.XPATH)
        if restriction_ele:
            if restriction_ele.text == 'There are 30 days remaining to disagree with this decision.':
                return 'SUSPENSION'
        try:
            error_restriction_id = 'com.instagram.android:id/dialog_body'
            error_restriction_ele = self.find_element('Ristriction Error',error_restriction_id,By.ID)
            error_restriction = error_restriction_ele.text
            if error_restriction :
                with open('accounts_cred/all_accounts.txt', 'a+') as f:
                    f.write(f"{number}    {name}    {password}      {birth_date,birth_month,birth_date}     {i_username}   Got an error\n")
                LOGGER.info(f"{number}    {name}     {password}     {birth_date,birth_month,birth_date}    {i_username}     Got an error\n")
                LOGGER.info(f' Got en error : From Instagram --->{error_restriction}. \n')

                return False
        except :
            after_not_error = self.after_not_error()
            if after_not_error:
                user = User_details.objects.create(
                        avdname=self.emulator_name,
                        username=i_username,
                        number=phone_number,
                        password=password,
                        birth_date=birth_date,
                        birth_month=birth_month,
                        birth_year=birth_year)
                LOGGER.info('Not get en error : We restrict certain activity to protect our community.\n')
                try:
                    LOGGER.info(f"{number}  {name}  {password}  {birth_date,birth_month,birth_date}  {i_username} \n")
                    with open('accounts_cred/all_accounts.txt', 'a+') as f:
                        f.write(f"{number}  {name}  {password}  {birth_date,birth_month,birth_year}  {i_username} \n")
                        

                except :self.logger.info('counldnt add in file')
                return user
            else:
                return False
            
    def restart_Insta(self):
        self.driver().activate_app('com.instagram.android')
        random_sleep(3,5)
        self.driver().terminate_app('com.instagram.android')
        random_sleep(4,5)
        self.driver().activate_app('com.instagram.android')
        random_sleep(3,5)
        
        random_sleep()
        Old_application = self.find_element('Old application','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView[1]')
        if Old_application:
            self.Install_new_insta()
            random_sleep()
            self.driver().activate_app('com.instagram.android')
            
    def start_app(self,activity = ''):
        time.sleep(3)
        try:
            self.restart_Insta()
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

    def Install_new_insta(self):
        self.driver().remove_app('com.instagram.android')
        self.install_apk(self.adb_console_port, "instagram")


    def login(self,username,password):
        
        self.user = User_details.objects.filter(username=username).first()
        self.start_app('login')
        self.driver().activate_app('com.instagram.android')
        LOGGER.info("inside login methods")
        HomeBtn = self.find_element('Home page','com.instagram.android:id/feed_tab',By.ID)
        if HomeBtn : return True
        self.input_text(username,'Username','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
        self.input_text(password,'Password','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
        self.click_element('Login btn','//android.widget.Button[@content-desc="Log in"]')
        
        # save login info
        SaveInfo = self.find_element('save info','//android.view.View[@content-desc="Save your login info?"]',timeout=20)
        if SaveInfo:
            self.click_element('Save','//android.widget.Button[@content-desc="Save"]')
        else:
            # check need otp or not?
            # self.driver().find_elements(By.TAG_NAME,'android.widget.EditText')
            check_number_h1 = self.find_element('Confirm its you H1','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup/android.view.View[1]',timeout=12)
            if check_number_h1:
                if check_number_h1.text == "Confirm it's you":
                    self.user.status = 'LOGIN_ISSUE'
                    self.user.save()
                    return False
                
            check_number_h1 = self.find_element('Confirm its you H1','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup/android.view.View[1]',timeout=2)
            if check_number_h1:
                if check_number_h1.text == "Confirm it's you":
                    self.user.status = 'LOGIN_ISSUE'
                    self.user.save()
                    return False
                
            check_number_h2 = self.find_element('Confirm its you H2','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup/android.view.View[2]',timeout=2)
            if check_number_h2:
                if check_number_h2.text == "To secure your account, we'll send you a security code to this phone number":
                    self.user.status = 'LOGIN_ISSUE'
                    self.user.save()
                    return False
            # To secure your account, we'll send you a security code to this phone number
        
        
        
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
        for i in range(2,5):
            SearchedUser = self.find_element(f'search {i} user', f'/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[2]/android.widget.FrameLayout[1]/android.widget.FrameLayout/androidx.recyclerview.widget.RecyclerView/android.widget.FrameLayout[{i}]/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout[1]/android.widget.TextView',timeout=3)
            if SearchedUser :
                if SearchedUser.text == Username:
                    SearchedUser.click()
                    break
        else:
            abc = self.driver().find_elements(By.XPATH,'//*')
            for i in abc: 
                if i.text == 'xanametaverse':
                    i.click()
                    
        # check searched user
        SearchedUsername = self.find_element('Searched Username','com.instagram.android:id/action_bar_title',By.ID)
        if SearchedUsername.text == Username:return True
        else: return False        
        
    def Follow(self):
        FollowBtn = self.find_element('Follow btn','com.instagram.android:id/profile_header_follow_button',By.ID)
        if FollowBtn.text != 'Following': FollowBtn.click()
        
    def ChangeReels(self):
        random_sleep(15,20)
        self.swip_display(9)
        
    def ReelsView(self):
        self.swip_display(4)
        
        action = True        
        for _ in range(5):
            self.click_element('Reels','//android.widget.ImageView[@content-desc="Reels"]')
            self.click_element('First reel','(//android.widget.ImageView[@content-desc="Reel by xanametaverse. Double tap to play or pause."])[1]')
            for _ in range(9): 
                self.ChangeReels()
            self.driver().back()
            action = False
            
    def ActionOnPost(self,swipe_number=4,RandomPostFollow = False,Like=True,Comment = True, Share = True, Save = True,RandomPostFollowRation=100,LikeRation=100,CommentRation=100,ShareRation=100,SaveRation=100):
        Percentage_list = [i for i in range(100)]
            
        # Random post follow
        RandomFollowRequire = random.choice(Percentage_list)
        if RandomPostFollow and RandomFollowRequire < int(RandomPostFollowRation):
            self.click_element('Follow btn','com.instagram.android:id/row_right_aligned_follow_button_stub',By.ID)
        
        time.sleep(2)
        for _ in range(7):
            self.swip_display(swipe_number)
            PostDetails = self.find_element('Post Details','com.instagram.android:id/row_feed_comment_textview_layout',By.ID,timeout=3)
            if PostDetails : 
                PostDetailsText = PostDetails.text
                break
            
        # like
        LikeRequire = random.choice(Percentage_list)
        if Like and LikeRequire < int(LikeRation) :
            self.click_element('Like btn','//android.widget.ImageView[@content-desc="Like"]',timeout=2)
        
        # comment
        CommentRequire = random.choice(Percentage_list)
        if Comment and CommentRequire < int(CommentRation):
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
                self.click_element('Allow btn for camera permission','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.ScrollView/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout[2]/android.widget.Button[2]',timeout=2)
                self.click_element('Allow btn for audio','com.android.packageinstaller:id/permission_allow_button',By.ID,timeout=2)
                self.click_element('Allow btn for storage','com.android.packageinstaller:id/permission_allow_button',By.ID,timeout=2)
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
            
        # go back if post is open
        Explorare_post = self.find_element('Explore element','//android.widget.TextView[@content-desc="Explore"]',timeout=2)
        if Explorare_post:
            if Explorare_post.text == 'Explore':
                self.click_element('Back','//android.widget.ImageView[@content-desc="Back"]')
        
        PostsPage = self.find_element('post ele','//android.widget.TextView[@content-desc="Posts"]',timeout=2)
        if PostsPage:
            if PostsPage.text == 'Posts':
                self.click_element('Back','//android.widget.ImageView[@content-desc="Back"]')
    
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
                
                
    def EngagementOnUser(self):
        self.click_element('Grid View','//android.widget.ImageView[@content-desc="Grid view"]')
        
        PostCount = 1
        for column in range(1,4):
            for indexx in range(1,4):
                
                for _ in range(5):
                    post_ele = self.click_element(f'post : {PostCount}', f'//android.widget.Button[@content-desc="Reel by XANA | Metaverse at row {column}, column {indexx}"]')
                    if post_ele:
                        self.ActionOnPost()
                        PostCount+=1
                        break
                    else : self.swip_display(4)
            self.swip_display(4)
            
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
            
            
    def send_views(self,Username='xanametaverse'):
        
        self.search_user(Username)
        self.Follow()
        self.EngagementOnUser()
        self.ReelsView()
        
        
    def Follow_4_Follow(self):
        self.update_user_follow_info()
        CanSearchUsers = user_detail.objects.using('monitor').filter(can_search=True,status='ACTIVE')
        for Follow_user in CanSearchUsers[:100]:
            self.Follow_user = Follow_user
            if self.search_user(Follow_user.username):
                self.Follow()
                self.update_follow_user_info()
                ...
            else:
                self.Follow_user.can_search = False
                self.Follow_user.save()        
        
    def random_action(self):
        
        self.click_element('Search btn','com.instagram.android:id/search_tab',By.ID)
        random_index = random.sample(range(0, 9), k=random.randint(3,6))
        ...
        for indexx in random_index:
            self.choose_random_image(indexx)
            self.ActionOnPost(swipe_number=3,RandomPostFollow=True,RandomPostFollowRation=30)
            
            
    def Profile_update(self):
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
        ProfileName = self.find_element('Profile name','com.instagram.android:id/action_bar_large_title_auto_size',By.ID)
        if ProfileName:
            if ProfileName.text == self.user.username:
                print('yesss')
                
                
        ...
        ...