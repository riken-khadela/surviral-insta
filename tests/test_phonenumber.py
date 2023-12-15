import unittest, time
import os
import django
import appium,re, requests
import subprocess
import random

from appium.webdriver.appium_service import AppiumService
from appium import webdriver
from appium.webdriver.common.touch_action import TouchAction
from PIL import Image
from appium.webdriver.common.mobileby import MobileBy
from appium.webdriver.webdriver import WebDriver
from django.db.models import Q
from selenium.common.exceptions import InvalidElementStateException
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
timeout = 10
# setup django settings


username = "pay@noborders.net"
GETSMSCODE_API_KEY = "cfca2f0dd0be35a82de94e038ad2a7e8"
GETSMSCODE_PID = "8"
removevr = "0" 
endpoints = {
    "login": {"action": "login", "username": username, "token": GETSMSCODE_API_KEY},
    "get_mobile": {"action": "getmobile", "username": username, "token": GETSMSCODE_API_KEY, "pid": GETSMSCODE_PID, "removevr": removevr},
    "get_sms": {"action": "getsms", "username": username, "token": GETSMSCODE_API_KEY, "pid": GETSMSCODE_PID},
    "add_blacklist": {"action": "addblack", "username": username, "token": GETSMSCODE_API_KEY, "pid": GETSMSCODE_PID}


}
base_url = "http://api.getsmscode.com/do.php"
def make_request(endpoint, params=None):
    url = base_url
    data = endpoints[endpoint]
    if params:
        data.update(params)

    response = requests.post(url, data=data)
    return response

def get_number():
    while True:
        get_mobile_response = make_request("get_mobile")
        mobile_number = get_mobile_response.text.strip()
        if str(mobile_number) == 'Message|Capture Max mobile numbers,you max is 5':
            continue
        else:break
    return mobile_number

def get_sms(phone_number):
    response = make_request("get_sms", {"mobile": phone_number})
    if response.status_code == 200:
        response_text = response.text
        print(response_text)
        if str(response_text).isdigit() :
            return (response_text)
        if 'insta' in (response_text).lower():
            if '|' in (response_text).lower():
                match = response_text.split('|')
                print(response_text)
                message = match[1]
                code = re.search(r"\d{3}\s*\d{3}", message).group().replace(" ", "")
                return code
            else:
                response = response_text.split(' ')
                otp = response[1]+response[2]
                return otp


def ban_number(phone_number):
    add_blacklist_response = make_request("add_blacklist", {"mobile": phone_number})
    print(add_blacklist_response.text)
    return add_blacklist_response


def random_sleep(min_sleep_time=1, max_sleep_time=5,reason=''):
    sleep_time = random.randint(min_sleep_time, max_sleep_time)
    if not reason:print(f'Random sleep: {sleep_time}')
    else:print(f'Random sleep: {sleep_time} for {reason}')
    time.sleep(sleep_time)

class TestAvd(unittest.TestCase):
    def __init__(self):
        self.get_driver()
        self.run_task()
        
    def driver(self):
        for _ in range(5):
            try:
                if not self.app_driver:
                    self.get_driver()
                session = self.app_driver.session
                return self.app_driver
            except Exception as e:
                print(e)
                self.get_driver()
            
        
    
    def get_driver(self, port=4724):
        try:
            opts = {
                "platformName": "Android",
                #  "platformVersion": "9.0",    # comment it in order to use other android version
                "automationName": "uiautomator2",
                "noSign": True,
                "noVerify": True,
                "ignoreHiddenApiPolicyError": True,
                #  "systemPort": "8212",
                # "udid": f"emulator-{self.emulator_port}",
            }

            print('Start appium driver')
            print(f'Driver capabilities: {opts}')

            self.app_driver = webdriver.Remote(
                f"http://localhost:{port}/wd/hub",
                desired_capabilities=opts,
                keep_alive=True,
            )
            self.start_driver_retires = 0
        except Exception as e:
            print(e)
            raise e

        return self.app_driver

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
                print(f'Timeout is less or equal zero: {timeout}')
                ele = self.driver().find_element(by=locator_type,
                        value=locator)
            if page:
                print(
                        f'Found the element "{element}" in the page "{page}"')
            else:
                print(f'Found the element: {element}')
            return ele
        except (NoSuchElementException, TimeoutException) as e:
            if page:
                print(f'Cannot find the element "{element}"'
                        f' in the page "{page}"')
            else:
                print(f'Cannot find the element: {element}')
    
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
                print(f'Timeout is less or equal zero: {timeout}')
                ele = self.driver().find_elements(by=locator_type,
                        value=locator)
            if page:
                print(
                        f'Found the element "{element}" in the page "{page}"')
            else:
                print(f'Found the element: {element}')
            return ele
        except (NoSuchElementException, TimeoutException) as e:
            if page:
                print(f'Cannot find the element "{element}"'
                        f' in the page "{page}"')
            else:
                print(f'Cannot find the element: {element}')

    def click_element(self, element, locator, locator_type=By.XPATH,
            timeout=timeout,page=None,timesleep=1):
        
        """Find an element, then click and return it, or return None"""
        ele = self.find_element(element, locator, locator_type, timeout=timeout,page=page,timesleep=timesleep)
        if ele:
            ele.click()
            print(f'Clicked the element: {element}')
            return ele

    def input_text(self, text, element, locator, locator_type=By.XPATH,
            timeout=timeout, hide_keyboard=True,page=None):
        
        """Find an element, then input text and return it, or return None"""
        try:
            if hide_keyboard :
                print(f'Hide keyboard')
                try:self.driver().hide_keyboard()
                except:None

            ele = self.find_element(element, locator, locator_type=locator_type,
                    timeout=timeout,page=page)
            if ele:
                ele.clear()
                ele.send_keys(text)
                print(f'Inputed "{text}" for the element: {element}')
                return ele
        except Exception as e :
            print(f'Got an error in input text :{element} {e}')  
    
    def phone_number_proccess(self):
        for phone_try in range(3):
            self.phone_number = get_number()
            phone_number_digit = str(self.phone_number).isdigit()
            if phone_number_digit:
                print(self.phone_number)
                self.input_text(self.phone_number,'phone number input','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.EditText')
                if self.click_element('Next btn','//android.widget.Button[@content-desc="Next"]') :
                    random_sleep(5,7,reason='next page')
                else :
                    ban_number(self.phone_number)
                    continue
                
                if self.find_element('Incorrect number','//android.view.View[@content-desc="Looks like your mobile number may be incorrect. Try entering your full number, including the country code."]'):
                    ban_number(self.phone_number)
                    continue
                
                elif self.click_element('Create account','//android.widget.Button[@content-desc="Create new account"]'):
                    ...
                    
                elif self.find_element('otp page', '//android.view.View[@text="Enter the confirmation code"]',timeout=5):
                    ...
                    
                elif self.find_element('something went wrong','//android.view.View[@content-desc="Something went wrong. Please try again later."]',timeout=2):
                    ban_number(self.phone_number)
                    self.df.loc['avd']=self.emulator_name
                    self.df.to_csv('delete_avd.csv', index=False)
                    print(f'add this {self.emulator_name} avd in delete local avd list')
                    self.user_avd.delete()
                    return 'delete_avd'  

                elif self.find_element('phone number page', '''//android.view.View[@text="What's your mobile number?"]''',timeout=2):
                    self.df.loc['avd']=self.emulator_name
                    self.df.to_csv('delete_avd.csv', index=False)
                    print(f'add this {self.emulator_name} avd in delete local avd list')
                    self.user_avd.delete()
                    return 'delete_avd'      
                
                elif self.find_element('name page', '''//android.view.View[@text="What's your name?"]''',timeout=2):
                    return True
                
                for I_otp in range(10) :
                    
                    otp = get_sms(self.phone_number)
                    if otp:
                        print(otp)
                        self.input_text(str(otp),'input otp','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.EditText')
                        next_btn = self.app_driver.find_element(By.XPATH,'//android.widget.Button[@content-desc="Next"]')
                        next_btn.click()
                        return True
                    if I_otp == 9:
                        ban_number(self.phone_number)
                        self.driver().back()
                    time.sleep(10)
                        
                if phone_try == 0:
                        self.df.loc['avd']=self.emulator_name
                        self.df.to_csv('delete_avd.csv', index=False)
                        print(f'add this {self.emulator_name} avd in delete local avd list')
                        return 'delete_avd'
                    
    def run_task(self):
        self.phone_number_proccess()
        print('The driver is connect :',self.app_driver)
        ...

tb = TestAvd()
breakpoint()