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
from selenium.common.exceptions import NoSuchElementException, TimeoutException,InvalidElementStateException
from exceptions import CannotStartDriverException
from appium import webdriver
from insta.utils import log_activity
from insta.cyberghostvpn import CyberGhostVpn
from .utils import get_sms,get_number,ban_number, NEW_INSTA_ACC_BIO

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
        # breakpoint()
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
        default_package = "system-images;android-28;default;x86"

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

        LOGGER.debug('Check if cyberghost is installed')
        self.driver().install_app('apk/cyberghost.apk')
            
        LOGGER.debug('Check if instagram is installed')        
        if not self.driver().is_app_installed("com.instagram.android"):
            LOGGER.debug('instagram is not installed, now install it')
            self.driver().install_app('apk/instagram.apk')
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
                self.driver().install_app('apk/instagram.apk')

            else:
                self.driver().terminate_app('com.instagram.android')
        
        try:
            command = f"adb -s emulator-{self.adb_console_port} shell rm -r /sdcard/Download/*"
            subprocess.run(command, shell=True, check=True)
        except Exception as e:
            print(e)

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

        phone_number = get_number()
        phone_number_digit = str(phone_number).isdigit()
        if phone_number_digit:
            for i in range(2):

                print(phone_number)
                self.input_text(phone_number,'phone number input','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.EditText')
                self.click_element('next btn','//android.widget.Button[@content-desc="Next"]')
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
                    if count == 5:
                        ban_number(phone_number)
                        self.back_until_number(2)
                        LOGGER.info(f'add this {self.emulator_name} avd in delete local avd list')
                        # self.user_avd.delete()
                        return False
                    
                if otp:
                    print(otp)
                    self.input_text(str(otp),'input otp','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
                    next_btn = self.driver().find_element(By.XPATH,'//android.widget.Button[@content-desc="Next"]')
                    next_btn.click()
                    break
            return phone_number
    def next_btn(self):    
        next_btn = self.driver().find_element(By.XPATH,'//android.widget.Button[@content-desc="Next"]').click()

    def swip_until_match(self,comperison_xpath,comperison_text):
        rect_ele = self.driver().find_element_by_xpath(comperison_xpath).rect
        start_x = rect_ele['x'] + rect_ele['width'] / 2
        start_y = rect_ele['y'] + rect_ele['height'] / 2
        end_x = start_x
        end_y = start_y + rect_ele['height']
        LOGGER.debug(f'start_x: {start_x}, start_y: {start_y}, end_x: {end_x}, end_y: {end_y}')
        while True:
            self.driver().swipe(start_x=start_x,start_y=start_y,end_x=end_x,end_y=end_y,duration=random.randrange(200, 250))
            time.sleep(0.20)
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
        self.next_btn()
    
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
        
    def create_account(self):
            number_bool = False
            allow_contacts_bool = False
            name_bool = False
            birthdate_bool = False
            breakpoint()
        # try:
            LOGGER.debug('Check if instagram is installed')        
            if not self.driver().is_app_installed("com.instagram.android"):
                LOGGER.debug('instagram is not installed, now install it')
                self.driver().install_app('/home/dell/Music/insta2.apk')
                self.driver().install_app('apk/instagram1.apk')
            random_sleep()
            self.driver().activate_app('com.instagram.android')
            
            create_btn = self.find_element('create account btn','//android.widget.Button[@content-desc="Create new account"]',timeout=20)

            if create_btn:
                self.click_element('create account btn','//android.widget.Button[@content-desc="Create new account"]')
            else:
                LOGGER.info(f'add this {self.emulator_name} avd in delete local avd list')
                return False
            
            self.set_birth_date()

            allow_contacts = self.find_element('allow contacts','com.android.permissioncontroller:id/permission_message',By.ID,timeout=4)
            if allow_contacts :
                if allow_contacts.text == "Allow Instagram to access your contacts?":
                    self.click_element('Allow contacts','com.android.permissioncontroller:id/permission_allow_button',By.ID)
            
            mobile_number_ele = self.find_element('mobile number input','//android.view.View[@content-desc="Mobile number"]',timeout=5)
            if mobile_number_ele :
                if mobile_number_ele.text == 'Mobile number':

                    phone_number = self.phone_number_proccess()
                    if not phone_number:
                        return False



            try:
                print(self.full_name)
                self.input_text(self.full_name,'first name input','//*[@class="android.widget.EditText"]')
                self.next_btn()
                print(self.password)
                time.sleep(5)
                self.input_text(self.password,'password input','//*[@class="android.widget.EditText"]')
                self.next_btn()
                self.click_element('save info','//android.widget.Button[@content-desc="Save"]')
            except Exception as e:
                print(e)

            self.set_birth_date()
            self.next_btn()
            time.sleep(10)
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
            
            i_agree = self.find_element('i_agree','//android.widget.Button[@content-desc="I agree"]')
            if i_agree:
                self.click_element('I agree','//android.widget.Button[@content-desc="I agree"]')
                time.sleep(13)
                add_profile = self.find_element('add_profile_btn','//android.widget.Button[@content-desc="Add picture"]')
                if add_profile:
                    user = User_details.objects.create(
                                avdsname=self.emulator_name,
                                username=self.i_username,
                                number=phone_number,
                                password=self.password,
                                birth_date=self.birth_date,
                                birth_month=self.birth_month,
                                birth_year=self.birth_year,
                                status='ACTIVE',
                                avd_pc = os.getenv('PC')
                            )
                    
                    self.add_profile_pic()
                    check_add_bio = self.add_bio()
                    time.sleep(5)
                    try:
                        user.bio = self.bio
                        user.is_bio_updated=check_add_bio
                    except AttributeError  as a:print(a)
                    except Exception as ee:print(ee)
                    user.updated=True
                    user.save()
                    return user
                else:
                    return False