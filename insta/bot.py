from conf import *
import  parallel, numpy as np, random, subprocess, time, os, traceback, difflib, requests
from dotenv import load_dotenv
from main import LOGGER
from insta.models import UserAvd, User_details
from surviral.settings import BASE_DIR
from ppadb.client import Client as AdbClient
from utils import run_cmd, get_installed_packages,random_sleep
from faker import Faker
from surviral import settings 
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException,InvalidElementStateException,InvalidSessionIdException
from exceptions import CannotStartDriverException
from appium import webdriver
from insta.utils import log_activity
from insta.cyberghostvpn import CyberGhostVpn
from .utils import get_sms,get_number,ban_number, random_insta_bio, get_image_for_create_account
from appium.webdriver.common.touch_action import TouchAction
from django.db import connection

def GetInstaComments(PostDetails):
    url = 'http://15.152.13.112:8088/get_comments/'
    params = {'text': PostDetails}
    headers = {'accept': 'application/json'}
    response = requests.get(url, params=params, headers=headers)
    CommentList = response.json()['Comments']
    return random.choice(CommentList)

timeout = 10
class InstaBot:
    def __init__(self, emulator_name, start_appium=True, start_adb=True,
                 appium_server_port=APPIUM_SERVER_PORT, adb_console_port=None):
        self.user = ''
        self.emulator_name = emulator_name
        load_dotenv()
        self.user_avd = UserAvd.objects.filter(name=emulator_name).first()
        
        if not self.user_avd:
            self.user_avd = UserAvd.objects.filter(name=emulator_name).first()
        # if not self.user_avd:
        #     UserAvd.objects.filter(name=emulator_name).first()
        self.logger = LOGGER
        #  self.kill_bot_process(appium=True, emulators=True)
        self.app_driver = None
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
    def get_parallel_opts(self):
        return {
            'appium:avd': self.emulator_name,
            'appium:avdArgs': ['-port', str(self.adb_console_port)] + self.get_avd_options(),
            'appium:systemPort': self.system_port,
            'appium:noReset': True,
            #  'appium:skipLogCapture': True,
        }

    @staticmethod
    def create_avd(avd_name, package=None, device=None):
        default_package = "system-images;android-28;default;x86_64"

        try:
            if not package:
                cmd = f'avdmanager create avd -n {avd_name} -k "{default_package}"'
                package = default_package
            else:
                cmd = f'avdmanager create avd --name {avd_name} --package "{package}"'

            if device:
                #  cmd += f" --device {device}"
                cmd += f" --force --device \"{device}\""

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
    def start_driver(self):
        try:
            opts = {
                "platformName": "Android",
                #  "platformVersion": "9.0",    # comment it in order to use other android version
                "automationName": "UiAutomator2",
                "noSign": True,
                "noVerify": True,
                "ignoreHiddenApiPolicyError": True,
                'autoGrantPermissions': True
                # "appWaitDuration": 10000
                # "newCommandTimeout": 30,
                #  #Don't use this
                #  "systemPort": "8210",
                #  'isHeadless': True,
                #  "udid": f"emulator-{self.emulator_port}",
            }

            opts.update(self.parallel_opts)

            #  LOGGER.debug('Start appium driver')
            LOGGER.debug(f'Driver capabilities: {opts}')
            LOGGER.debug(f"Driver url: http://{APPIUM_SERVER_HOST}:{self.appium_server_port}/wd/hub")
            self.app_driver = webdriver.Remote( f"http://{APPIUM_SERVER_HOST}:{self.appium_server_port}/wd/hub",desired_capabilities=opts)
            self.start_driver_retires = 0
            log_activity(
                self.user_avd.id,
                action_type="ConnectAppium",
                msg=f"Driver started successfully",
                error=None,
            )
        except Exception as e:
            LOGGER.warning(e)
            # if 'driver' in globals():
            #     self.app_driver.close()
            if not parallel.get_avd_pid(name=self.emulator_name, port=self.adb_console_port):
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

    def check_apk_installation(self):
        LOGGER.debug('Check if apk is installed')
        vpn = CyberGhostVpn(self.driver())
        if vpn.is_app_installed():
            vpn.terminate_app()

        

    def connect_to_vpn(self, fail_tried=0, vpn_type='cyberghostvpn',
                       country='', city=""):
        if not country:
            country = self.user_avd.country
        
        try :
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
        except :
            return False
        
    def back_until_number(self,number):
        try:
            for i in range(number):
                time.sleep(0.3)
                self.driver().back()
        except Exception as e :
            self.logger.info(f'Got an error in Go back to the number : {e}')

    def phone_number_proccess(self):
        
        mobile_number_ele = self.find_element('mobile number input','//android.view.View[@content-desc="Mobile number"]',timeout=5)
        if mobile_number_ele :
            if mobile_number_ele.text != 'Mobile number':
                return False
            
        else:return False
            
        phone_number = get_number()
        phone_number_digit = str(phone_number).isdigit()
        if phone_number_digit:
            for i in range(4):

                print(phone_number)
                self.input_text(phone_number,'phone number input','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.EditText')
                self.phone_number = phone_number
                self.click_element('next btn','//android.widget.Button[@content-desc="Next"]')

                trying_to_error = self.find_element('trying to find element','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.view.ViewGroup[2]/android.widget.ImageView',timeout=2)
                if trying_to_error :
                    ban_number(phone_number)
                    return "delete_avd"
                trying_to_error = self.find_element('trying to find element','//android.view.View[@content-desc="Please wait a few minutes before you try again."]',timeout=2)
                if trying_to_error :
                    ban_number(phone_number)
                    return "delete_avd"
                self.click_element('create a new account','//android.widget.Button[@content-desc="Create new account"]')
                confirmation_code = self.find_element('Confirmation code input','//android.view.View[@content-desc="Enter the confirmation code"]')
                if not confirmation_code :
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
                    if count == 10:
                        ban_number(phone_number)
                        self.back_until_number(2)
                        LOGGER.info(f'add this {self.emulator_name} avd in delete local avd list')
                        break
                    
                if otp:
                    print(otp)
                    self.input_text(str(otp),'input otp','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
                    next_btn = self.driver().find_element(By.XPATH,'//android.widget.Button[@content-desc="Next"]')
                    next_btn.click()
                    return phone_number
    def next_btn(self):    
        self.click_element('Next btn','//android.widget.Button[@content-desc="Next"]')

    def swip_until_match(self,comperison_xpath,comperison_text):
        rect_ele = self.driver().find_element_by_xpath(comperison_xpath).rect
        start_x = rect_ele['x'] + rect_ele['width'] / 2
        start_y = rect_ele['y'] + rect_ele['height'] / 2
        end_x = start_x
        end_y = start_y + rect_ele['height']
        LOGGER.debug(f'start_x: {start_x}, start_y: {start_y}, end_x: {end_x}, end_y: {end_y}')
        for _ in range(25):
            self.driver().swipe(start_x=start_x,start_y=start_y,end_x=end_x,end_y=end_y,duration=random.randrange(200, 250))
            # time.sleep(0.20)
            comperison_xpath_text = self.driver().find_element_by_xpath(comperison_xpath).text
            if comperison_xpath_text == comperison_text:
                break

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
    def profile_img_download(self):
        '''
        downloading the file and saving it in download folder
        '''
        
        profile_pic_path = get_image_for_create_account(self.user_gender)
        run_cmd(f'adb -s emulator-{self.adb_console_port} push {profile_pic_path} /sdcard/Download')
        if os.path.exists(profile_pic_path):
            os.remove(profile_pic_path)
            # '/home/dell/workspace2/auto_gender_definer/profile_pic/male/26423157.jpeg'
            self.logger.info(f"File '{profile_pic_path}' has been successfully removed.")
        else:
            self.logger.error(f"The file '{profile_pic_path}' does not exist.")

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
            else : return


            print(self.full_name)
            self.input_text(self.full_name,'first name input','''//*[@class="android.widget.EditText"]''')
            self.next_btn()
            print(self.password)
            time.sleep(5)
            if self.input_text(self.password,'password input','//*[@class="android.widget.EditText"]') :
                self.process_acc_creation.remove("enter_password")
            if self.next_btn() :
                random_sleep(5,10)
            if self.click_element('save info','//android.widget.Button[@content-desc="Save"]') :
                self.process_acc_creation.remove("save_info")
                random_sleep(5,10)

            return True

        except Exception as e:
            print(e)
            return False
    
    def create_set_username(self):
        create_username_title = self.find_element('username title','//android.view.View[@content-desc="Create a username"]')
        if create_username_title :
            if create_username_title.text == "Create a username" :
                username_input = self.find_element('username input','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
                self.user_username = str(self.full_name)+"_"+str(random.randint(1000000,9999999))
                self.input_text(self.user_username,'username input','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
                random_sleep(10,15)
                self.next_btn()
                return self.user_username

        ...
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
    def Install_new_insta(self,):
        apk_path = os.path.join(BASE_DIR, "apk/instagram1.apk")
        cmd = f'adb -s emulator-{self.adb_console_port} install -t -r -d -g {apk_path}'
        log_activity(
            self.user_avd.name,
            action_type="InstallInstagramApk",
            msg=f"Installation of instagram apk",
            error=None,
        )
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
        p.wait()

    def upload_post(self):
        self.click_element('create_btn','//android.widget.FrameLayout[@content-desc="Camera"]',timeout=30)
        self.click_element('next','//android.widget.ImageView[@content-desc="Next"]')
        self.click_element('next','//android.widget.ImageView[@content-desc="Next"]')
        self.click_element('ok','//android.widget.Button[@content-desc="OK"]')
        self.click_element('done','//android.widget.ImageView[@content-desc="Share"]')
        random_sleep(10,20,reason=' for upload post')
        # adb -s emulator-5622 -p 554 install -t -r -d -g /home/dell/Desktop/surviral-insta/apk/instagram.apk



    def create_account(self):
             
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
                return False

            refreash_ele = self.find_element('page isnt available','''//android.widget.TextView[@text="Page isn't available right now" and @class="android.widget.TextView"]''')
            if refreash_ele :
                if refreash_ele.text == "Page isn't available right now":
                    return False
            
            self.process_acc_creation = ['enter_password'
                                    ,"save_info"
                                    ,"set_birth_date"
                                    ,"phone_number_proccess"
                                    ,"create_set_username"
                                    ,"add_name_in_new_user"
                                        ]
            for i in range(9):
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
                    numberr = self.phone_number_proccess()
                    if numberr:
                        if numberr == "delete_avd" :
                            return False
                        self.process_acc_creation.remove("phone_number_proccess")
                    
                    

                if self.agree_btn() : 
                    break
            else :return False
            
            if self.other_stuff_create_account() == False : return False
            else :
            # add_profile = self.click_element('profile button','//android.widget.FrameLayout[@content-desc="Profile"]/android.view.ViewGroup',timeout=15)
            # if add_profile:
                connection.connect()
                self.user_gender = random.choice(['MALE','FEMALE'])
                self.user = User_details.objects.create(avdsname=self.emulator_name,username=self.user_username,number=self.phone_number,password=self.password,birth_date=self.birth_date,birth_month=self.birth_month,birth_year=self.birth_year,status='ACTIVE',avd_pc = 'local-rk',gender=self.user_gender)
                self.add_profile_pic()
                check_add_bio = self.add_bio()
                self.upload_post()
                try:
                    self.user.bio = self.bio
                    self.user.is_bio_updated=check_add_bio
                except AttributeError  as a:print(a)
                except Exception as ee:print(ee)
                self.user.updated=True
                connection.connect()
                self.user.save()
                return True
        return False
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

    def search_user(self,Username):
        self.click_element('Search btn','com.instagram.android:id/search_tab',By.ID)
        self.click_element('Search input','com.instagram.android:id/action_bar_search_edit_text',By.ID)
        if not self.find_element('Search input','com.instagram.android:id/action_bar_search_edit_text',By.ID):
            for i in range(2):
                self.click_element('Back','com.instagram.android:id/action_bar_button_back',By.ID,timeout=5)
        self.input_text(Username,'Search input','com.instagram.android:id/action_bar_search_edit_text',By.ID)
        time.sleep(3)
        search_results = WebDriverWait(self.driver(), 10).until(EC.presence_of_all_elements_located((By.XPATH, "//*[@resource-id='com.instagram.android:id/row_search_user_username']")))
        if search_results:
            for i in search_results:
                if str(i.text).lower() == str(Username).lower():
                    i.click()
                    break
        elif self.click_element('see all result','//android.widget.Button[@text="See all results"]'):
            time.sleep(2)
            self.click_element('account','//android.widget.TabWidget[@content-desc="Accounts"]')
            search_results = WebDriverWait(self.driver(), 10).until(EC.presence_of_all_elements_located((By.XPATH,f"//*[@resource-id='com.instagram.android:id/row_search_user_username' and @text='{Username}']")))
            if search_results:
                for i in search_results:
                    if str(i.text).lower() == str(Username).lower():
                        i.click()
                        break
                    
        SearchedUsername = self.find_element('Searched Username','com.instagram.android:id/action_bar_title',By.ID)
        # check searched user
        if SearchedUsername:
            if str(SearchedUsername.text).lower() == str(Username).lower():
                return True
        else: return False 
        
    def check_profile_updated(self):
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
        random_sleep(2,3)
        if self.is_bio_text and self.is_profile_photo:
            return True
        else:
            return False
    def Follow(self):
        FollowBtn = self.find_element('Follow btn','com.instagram.android:id/profile_header_follow_button',By.ID)
        if FollowBtn.text != 'Following': FollowBtn.click()

    def check_story_permission(self):
        self.click_element('Allow camera','com.android.packageinstaller:id/permission_message',timeout=3)
        ...

    def stories_avds_permissions(self):
        for _ in range(3) : self.click_element('allow','com.android.packageinstaller:id/permission_allow_button',By.ID,timeout=1)
        ...

    def ActionOnPost(self,swipe_number=4,Comment = False, Share = False, Save = True):
        self.click_element('play button','com.instagram.android:id/view_play_button',By.ID,timeout=2)
        time.sleep(2)
        for _ in range(7):
            self.swip_display(swipe_number)
            more = self.click_element('more','//android.widget.Button[@content-desc="more"]',timeout=3)
            time.sleep(1)
            PostDetails = self.find_element('Post Details','com.instagram.android:id/row_feed_comment_textview_layout',By.ID,timeout=3)
            self.click_element('more','//*[@text="… more"]')
            if PostDetails :break

        self.click_element('Like btn','//android.widget.ImageView[@content-desc="Like"]',timeout=2)
                
        if Share:
            if self.click_element('Share btn','//android.widget.ImageView[@content-desc="Send post"]'):
                self.click_element('Add reel to your story','//android.widget.Button[@content-desc="Add reel to your story"]',timesleep=2)
                while not self.driver().current_activity == 'com.instagram.modal.TransparentModalActivity':
                    random_sleep(1,1,reason='Wait untill story opens')
                random_sleep(2,3,reason='share to story')
                self.stories_avds_permissions()
                self.click_element('introducing longer stories','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.Button',timeout=3)
                self.click_element('Ok btn2','//android.widget.Button[@content-desc="Continue watching stories"]',By.XPATH,timeout=2)
                self.click_element('Ok btn','com.instagram.android:id/primary_button',By.ID,timeout=2)
                self.click_element('Share to','//android.widget.FrameLayout[@content-desc="Share to"]',timeout=2)
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
            
    def follow_rio(self,like=True):
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
                self.ActionOnPost(Share=False,Save=False)
        try:
            self.click_element('Home page','com.instagram.android:id/feed_tab',By.ID)
            for i in range(2):
                self.click_element('Search btn','com.instagram.android:id/search_tab',By.ID)
        except Exception as e:
            print(e)
    def EngagementOnUser(self,share=True):
        self.click_element('Follow btn','com.instagram.android:id/row_right_aligned_follow_button_stub',By.ID,timeout=3)
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
        PostCount =1
        for indexx in range(4):
            parent_element = self.find_element('list','android:id/list',By.ID)
            buttons = parent_element.find_elements_by_class_name('android.widget.Button')
            try :
                buttons[indexx].click()
                # Share = True if PostCount <= 4  else False
                self.ActionOnPost(Share=share)
                time.sleep(1)
                post = self.find_element('posts','com.instagram.android:id/action_bar_title',By.ID,timeout=2).text
                if post == 'Posts':
                    self.click_element('Back','//android.widget.ImageView[@content-desc="Back"]')
                    PostCount+=1 
            except : ...

    def ChangeReels(self): 
        random_sleep(7,10) 
        self.swip_display(9)

    def ReelsView(self,reels_watch_time=9):
        self.swip_display(4)
        self.click_element('Reels','//android.widget.ImageView[@content-desc="Reels"]')
        for i in range(3):
            self.click_element('First reel','(//android.widget.ImageView[@content-desc="Reel by xanametaverse. Double tap to play or pause."])[1]')
            for _ in range(int(reels_watch_time)):
                self.ChangeReels()
            self.driver().back()

    def set_profile_pic(self):
        gender = self.get_gender()
        if gender == 'female':
            profile_path = "profile_pic/female"
        else:
            profile_path =  "profile_pic/male"
        folder = os.path.join(os.getcwd(), profile_path)
        os.makedirs(folder, exist_ok=True)
        file_name = os.listdir(profile_path)
        if len(file_name) == 0:
            print('add more profile pic in directory')
            file_name = os.listdir(profile_path)

        profile_pic_path = os.path.join(os.getcwd(), f'{profile_path}/{random.choice(file_name)}')
        run_cmd(f'adb -s emulator-{self.adb_console_port} push {profile_pic_path} /sdcard/Download')
        new_file_name = f"{self.user.username}.jpg"
        new_profile_pic_path = os.path.join(os.getcwd(), f'{profile_path}/{new_file_name}')
        os.rename(profile_pic_path, new_profile_pic_path)
        used_pic_path = os.path.join(os.getcwd(), 'profile_pic/used_pic')
        os.makedirs(used_pic_path, exist_ok=True)
        os.replace(new_profile_pic_path, os.path.join(used_pic_path, new_file_name))

    def update_profile(self):
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
        time.sleep(3)
        self.click_element('Profile btn','com.instagram.android:id/tab_avatar',By.ID)
        self.click_element('Edit profile btn','//android.widget.Button[@text="Edit profile"]')
        if False and self.click_element('Change profile photo','//android.widget.Button[@text="Change profile photo"]',timeout=5):
            if not self.find_element('remove profile btn','//android.widget.Button[@text="Remove profile photo"]'):
                self.set_profile_pic()
                self.click_element('New profile photo','//android.widget.Button[@text="New profile photo"]')
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
        if False and self.click_element('Edit profile btn','//android.widget.Button[@text="Edit picture or avatar"]',timeout=5):
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
            else:
                self.driver().back()
                self.click_element('done','//android.widget.Button[@content-desc="Done"]')
        # self.upload_post()
        try:
            command = f"adb -s emulator-{self.adb_console_port} shell rm -r /sdcard/Download/*"
            subprocess.run(command, shell=True, check=True)
        except Exception as e: ...

    def Engagement_main(self,user,Username='xanametaverse',comment=False):
        LOGGER.debug('Check if instagram is installed')        
        if not self.driver().is_app_installed("com.instagram.android"):
            LOGGER.debug('instagram is not installed, now install it')

            self.driver().install_app('apk/instagram1.apk')
        random_sleep()
        self.driver().activate_app('com.instagram.android')
        self.user = User_details.objects.filter(id=user).first()
        
        # is_updated = self.check_profile_updated()
        # if not is_updated:
        #     self.update_profile()
        self.follow_rio()
        self.search_user(Username)
        self.Follow()
        self.EngagementOnUser()
        self.ReelsView()
        multiple_users = ["imanijohnson132","niamwangi63","lucamoretti6445","malikrobinson726","tylerevans2913","1aaliyahbrown","4nanyashah","haileymitchell161","tianaharris554","deandrewashington652","minjipark11","haraoutp","rayaanhakim"]
        for Username_multiple in multiple_users :
            try :
                self.search_user(Username_multiple)
                self.Follow()
                self.EngagementOnUser(share=False)
            except : ...
        if not self.user.avd_pc:
            self.user.avd_pc = os.getenv('PC')


   





    def kill_bot_process(self):
        """Kill the bot processes

        :param appium: Kill the Appium server if True (Default value = False)
        :param emulators: Kill the emulator if True (Default value = False)

        """
        LOGGER.debug(f'Start to kill the AVD: {self.emulator_name}')
        # terminate twitter to avoid using it before connecting vpn next time

        if self.app_driver:
            LOGGER.info(f'Stop the driver session')
            try:
                self.app_driver.quit()
            except InvalidSessionIdException as e:
                LOGGER.info(e)

        name = self.emulator_name
        port = self.adb_console_port
        parallel.stop_avd(name=name, port=port)