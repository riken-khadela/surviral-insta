import json
import os
import random
import re
import string
import subprocess
import traceback
import urllib.request
from urllib.parse import urlencode

import requests
import unicodecsv
from appium.webdriver.common.mobileby import MobileBy
from appium.webdriver.webdriver import WebDriver
from django.db.models import Q
from selenium.common.exceptions import InvalidElementStateException
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from accounts_conf import *
from constants import XANALIA_TAGS
from exceptions import GetSmsCodeNotEnoughBalance
from main import LOGGER
from surviral_avd.settings import BASE_DIR
from twbot.models import UserAvd
from utils import get_comment


def GetInstaComments(PostDetails):
    url = 'http://15.152.13.112:8088/get_comments/'
    params = {'text': PostDetails}
    headers = {'accept': 'application/json'}
    response = requests.get(url, params=params, headers=headers)
    CommentList = response.json()['Comments']
    return random.choice(CommentList)

def get_number():
    while True:
        url = f"http://api.getsmscode.com/vndo.php?action=getmobile&username=pay@noborders.net&token={GETSMSCODE_API_KEY}&pid={GETSMSCODE_PID}&cocode={GETSMSCODE_COUNTRY}"
        payload={}
        headers = {}
        response = requests.request("POST", url, headers=headers, data=payload)
        if str(response) == 'Message|Capture Max mobile numbers,you max is 5':
            continue
        else:break
    return response.text

def get_sms(phone_number):
    url = f"http://api.getsmscode.com/vndo.php?action=getsms&username=pay@noborders.net&token={GETSMSCODE_API_KEY}&pid={GETSMSCODE_PID}&mobile={phone_number}&author=pay@noborders.net&cocode={GETSMSCODE_COUNTRY}"
    response = requests.post(url=url)
    if response.status_code == 200:
        response_text = response.text
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
    url = f"http://api.getsmscode.com/vndo.php?action=addblack&username=pay@noborders.net&token={GETSMSCODE_API_KEY}&pid={GETSMSCODE_PID}&mobile={phone_number}&author=pay@noborders.net&cocode={GETSMSCODE_COUNTRY}"
    response = requests.post(url=url)
    print(response.text)
    return response



def random_sleep(min_sleep_time=1, max_sleep_time=5):
    sleep_time = random.randint(min_sleep_time, max_sleep_time)
    LOGGER.debug(f'Random sleep: {sleep_time}')
    time.sleep(sleep_time)


def start_app(driver, app_name):
    LOGGER.info(f'Start the app: {app_name}')
    try:
        if app_name == 'twitter':
            driver().start_activity("com.twitter.android", "com.twitter.android.StartActivity")

        elif app_name == 'instagram':
            driver().start_activity("com.instagram.android", "com.instagram.mainactivity.LauncherActivity")

        elif app_name == 'surfshark':
            driver().start_activity("com.surfshark.vpnclient.android", ".StartActivity")

        elif app_name == 'webview':
            driver().start_activity('org.chromium.webview_shell', 'org.chromium.webview_shell.WebViewBrowserActivity')

        time.sleep(10)
    except Exception as e:
        pass


def close_app(driver, app_name):
    LOGGER.debug(f'Close the app: {app_name}')
    try:
        if app_name == 'twitter':
            driver().terminate_app("com.twitter.android")

        elif app_name == 'instagram':
            driver().terminate_app("com.instagram.android")

        elif app_name == 'surfshark':
            driver().terminate_app("com.surfshark.vpnclient.android")

        elif app_name == 'shadowsocks':
            driver().terminate_app("com.github.shadowsocks")

        time.sleep(10)
    except Exception as e:
        pass


def restart_app(driver, app_name):
    LOGGER.debug(f'Restart the app: {app_name}')
    if app_name == 'twitter':
        close_app(driver, 'twitter')
        start_app(driver, 'twitter')

    elif app_name == 'instagram':
        close_app(driver, 'instagram')
        start_app(driver, 'instagram')

    elif app_name == 'surfshark':
        close_app(driver, 'surfshark')
        start_app(driver, 'surfshark')


def goto_home(driver, tries=0):
    LOGGER.debug('goto home')
    retries = tries
    try:
        ele_one = driver().find_elements_by_xpath('//android.widget.LinearLayout[@content-desc="Home Tab"]')
        ele_two = driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Home Tab"]/android.view.View')
        ele_three = driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Home Tab. New items"]')

        # v9.9.0
        ele4 = driver().find_elements_by_accessibility_id('Home. New items')
        # v9.4.0
        ele5 = driver().find_elements_by_accessibility_id('Home')

        home_btn = ele_one or ele_two or ele_three or ele4 or ele5
        LOGGER.debug(f'home_btn: {home_btn}')
        if home_btn:
            home_btn[0].click()
        else:
            raise Exception('Cannot find home button')

        return driver
    except Exception as e:
        LOGGER.error(e)
        if retries >= 5:
            return False

        # click return icon to go to parent page
        return_icon_content_desc = 'Navigate up'
        click_element(driver, 'Return icon', return_icon_content_desc,
                      MobileBy.ACCESSIBILITY_ID)

        retries += 1
        if retries >= 5:
            restart_app(driver, 'twitter')

        goto_home(driver, tries=retries)


def goto_search(driver):
    LOGGER.debug('goto search box')
    retries = 0
    try:
        while True:
            retries += 1

            ele_one = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.view.ViewGroup/android.widget.FrameLayout[2]/android.view.ViewGroup/android.widget.HorizontalScrollView/android.widget.LinearLayout/android.widget.LinearLayout[2]/android.view.View')
            ele_two = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.view.ViewGroup/android.widget.FrameLayout[2]/android.view.ViewGroup/android.widget.HorizontalScrollView/android.widget.LinearLayout/android.widget.LinearLayout[2]')

            # v9.9.0
            ele3 = driver().find_elements_by_accessibility_id('Search and Explore')

            search = ele_one or ele_two or ele3
            if search:
                search[0].click()
                #  time.sleep(5)
                random_sleep()
                break

            else:
                ele_one = driver().find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.HorizontalScrollView/android.widget.LinearLayout/android.widget.LinearLayout[2]')
                ele_two = driver().find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/androidx.drawerlayout.widget.DrawerLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.HorizontalScrollView/android.widget.LinearLayout/android.widget.LinearLayout[2]/android.view.View')
                search = ele_one or ele_two
                if search:
                    search[0].click()
                    #  time.sleep(5)
                    random_sleep()
                    break

                ele_root = driver().find_elements_by_id(
                    'com.twitter.android:id/tabs')
                if ele_root:
                    LOGGER.debug('Find search tab using tabbar element')
                    ele = ele_root[0].find_elements_by_xpath(
                        '//android.widget.LinearLayout/android.widget.LinearLayout[2]')
                    if ele:
                        ele[0].click()
                        break

                else:
                    restart_app(driver, "twitter")

            if retries >= 3:
                return False

    except Exception as e:
        print(e)


def search_for_target(driver, target):
    LOGGER.debug(f'search for "{target}"')
    # click on search bar
    ele_one = driver().find_elements_by_xpath('//android.widget.RelativeLayout[@content-desc="Search Twitter"]')
    ele_two = driver().find_elements_by_xpath(
        '//android.widget.RelativeLayout[@content-desc="Search Twitter"]/android.widget.TextView'
    )

    search = ele_one or ele_two
    search[0].click()
    #  time.sleep(5)
    random_sleep()

    # input search query in search bar
    search_bar = driver().find_elements_by_xpath('//android.widget.EditText[@content-desc="Search"]')
    search_bar[0].send_keys(str(target))
    press_enter(driver)
    #  time.sleep(5)
    random_sleep()

    # open searched profile
    LOGGER.debug('open tab people')
    ppl_xpath1 = driver().find_elements_by_xpath('//android.widget.LinearLayout[@content-desc="People"]')
    ppl_xpath2 = driver().find_elements_by_xpath(
        '//android.widget.LinearLayout[@content-desc="People"]/android.widget.TextView'
    )
    ppl_btn = ppl_xpath1 or ppl_xpath2
    ppl_btn[0].click()
    #  time.sleep(5)
    random_sleep()

    # open profile
    for j in range(random.randint(3, 7)):
        for i in range(random.randrange(3, 8)):
            profile_btn = driver().find_elements_by_xpath(
                f'/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout'
                f'/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view'
                f'.ViewGroup/android.widget.LinearLayout/android.view.ViewGroup/androidx.viewpager.widget.ViewPager'
                f'/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/androidx.recyclerview'
                f'.widget.RecyclerView/android.view.ViewGroup['
                f'{i}]/android.widget.RelativeLayout/android.widget.LinearLayout[1]/android.widget.TextView[1]')
            if profile_btn:
                profile_handle = profile_btn[0].text.replace("@", "").lower()
                if target.lower() == profile_handle:
                    LOGGER.debug('click profile button')
                    profile_btn[0].click()
                    #  time.sleep(5)
                    random_sleep()
                    return True

        LOGGER.debug('do some swipes')
        driver().swipe(start_x=random.randrange(50, 100), start_y=random.randrange(300, 350),
                       end_x=random.randrange(50, 100), end_y=random.randrange(0, 10), duration=600)
        #  time.sleep(2)
        random_sleep()

    return False


def click_search_tab(driver):
    LOGGER.debug('click search tab')
    ele_one = driver().find_elements_by_xpath(
        '//android.widget.RelativeLayout[@content-desc="Search Twitter"]')
    ele_two = driver().find_elements_by_xpath(
        '//android.widget.RelativeLayout[@content-desc="Search Twitter"]'
        '/android.widget.TextView'
    )
    ele3 = driver().find_elements_by_id(
        'com.twitter.android:id/query_view')
    ele4 = driver().find_elements_by_accessibility_id(
        'Search and Explore')
    ele5 = driver().find_elements_by_xpath(
        '//android.widget.FrameLayout[@resource-id="com.twitter.android:id/bottom_bar"]'
        '/android.view.ViewGroup/android.widget.HorizontalScrollView/'
        'android.widget.LinearLayout/android.widget.LinearLayout[2]/android.view.View'
    )
    ele6 = driver().find_elements_by_xpath(
        '//android.widget.HorizontalScrollView/android.widget.LinearLayout'
        '/android.widget.LinearLayout[2]/android.view.View')
    search = ele_one or ele_two or ele3 or ele4 or ele5 or ele6
    search[0].click()


def click_search_result_people_tab(driver):
    # open tab 'People'
    LOGGER.debug('Open tab People')
    people_xpath1 = driver().find_elements_by_xpath(
        '//android.widget.LinearLayout[@content-desc="People"]')
    people_xpath2 = driver().find_elements_by_accessibility_id(
        'People'
    )
    people_btn = people_xpath1 or people_xpath2
    people_btn[0].click()


def click_search_result_top_tab(driver):
    # open tab 'People'
    LOGGER.debug('Open tab Top')
    people_xpath1 = driver().find_elements_by_xpath(
        '//android.widget.LinearLayout[@content-desc="Top"]')
    people_xpath2 = driver().find_elements_by_accessibility_id('Top')
    people_btn = people_xpath1 or people_xpath2
    if people_btn:
        people_btn[0].click()


def check_search_result_is_empty(driver):
    try:
        empty_container = driver().find_element_by_id(
            'com.twitter.android:id/empty_container')
        LOGGER.info(f'Empty result for the keyword: {keyword}')
        return True
    except NoSuchElementException as e:
        return False


def get_search_result_from_tab_people(driver, want_at=False, content='text'):
    """Get texts or elements for the result"""
    accounts_elements = driver().find_elements_by_xpath(
        '//androidx.recyclerview.widget.RecyclerView/'
        'android.view.ViewGroup')
    #  accounts = {}
    accounts = []
    for element in accounts_elements:
        try:
            name = element.find_element_by_id(
                'com.twitter.android:id/name_item').text
            screen_name = element.find_element_by_id(
                'com.twitter.android:id/screenname_item').text
            try:
                description = element.find_element_by_id(
                    'com.twitter.android:id/profile_description_item').text
            except NoSuchElementException as e:
                description = ''
            if screen_name.startswith('@') and not want_at:
                screen_name = screen_name[1:]

            LOGGER.debug(f'name: {name}, screen_name: {screen_name}')
            LOGGER.debug(f'description: {description}')

            if content == 'text':
                #  accounts[screen_name] = {
                #          'name': name,
                #          'screen_name': screen_name,
                #          'description': description}
                accounts.append({
                    'name': name,
                    'screen_name': screen_name,
                    'description': description})
            else:
                #  accounts[screen_name] = {
                #          'name': name,
                #          'screen_name': screen_name,
                #          'description': description,
                #          'element': element}
                accounts.append({
                    'name': name,
                    'screen_name': screen_name,
                    'description': description,
                    'element': element})
            #  LOGGER.debug(f'accounts: {accounts}')
        except Exception as e:
            LOGGER.warning(e)
    return accounts


def get_search_result_from_suggestion(driver, account_name, want_at=False,
                                      content='text'):
    """Get texts or elements for the suggestion list"""
    LOGGER.debug('Get accounts items from search suggestion list')
    list_id = 'com.twitter.android:id/search_suggestions_list'
    list_class = 'androidx.recyclerview.widget.RecyclerView'
    list_item_xpath = (f'//{list_class}[@resource-id="{list_id}"]/*')
    accounts_elements = driver().find_elements_by_xpath(list_item_xpath)
    accounts = []
    for element in accounts_elements:
        try:
            name = element.find_element_by_id(
                'com.twitter.android:id/name_item').text
            screen_name = element.find_element_by_id(
                'com.twitter.android:id/screenname_item').text
            if screen_name.startswith('@') and not want_at:
                screen_name = screen_name[1:]

            LOGGER.debug(f'name: {name}, screen_name: {screen_name}')

            if screen_name and account_name.lower() == screen_name.lower():
                if content == 'text':
                    accounts.append({
                        'name': name,
                        'screen_name': screen_name})
                else:
                    accounts.append({
                        'name': name,
                        'screen_name': screen_name,
                        'element': element})
                LOGGER.debug(f'accounts: {accounts}')
                return accounts
        except Exception as e:
            LOGGER.warning(e)

        try:
            title_element = element.find_element_by_id(
                'com.twitter.android:id/title')
            text = title_element.text
            compare_name = account_name if account_name.startswith('@') else '@' + account_name
            compare_text = f'go to {compare_name}'
            if text and compare_name.lower() in text.lower():
                if content == 'text':
                    accounts.append({
                        'name': account_name,
                        'screen_name': account_name})
                else:
                    accounts.append({
                        'name': account_name,
                        'screen_name': account_name,
                        'element': title_element})
                LOGGER.debug(f'accounts: {accounts}')
                return accounts
        except Exception as e:
            LOGGER.warning(e)

    return accounts


def search(text, driver):
    # input search query in search bar
    LOGGER.debug(f'Input search text: {text}')
    search_bar = driver().find_elements_by_xpath(
        '//android.widget.EditText[@content-desc="Search"]')
    search_bar1 = driver().find_element_by_id(
        'com.twitter.android:id/query')
    search_bar = search_bar or search_bar1
    search_bar[0].clear()
    search_bar[0].send_keys(text)
    press_enter(driver)


def search_without_enter(text, driver):
    # input search query in search bar
    LOGGER.debug(f'Input search text: {text}')
    search_bar = driver().find_elements_by_xpath(
        '//android.widget.EditText[@content-desc="Search"]')
    search_bar1 = driver().find_element_by_id(
        'com.twitter.android:id/query')
    search_bar = search_bar or search_bar1
    search_bar[0].clear()
    search_bar[0].send_keys(text)


def open_profile_by_search(account_name, driver, do_goto_home=True,
                           do_goto_search=True):
    if do_goto_home:
        goto_home(driver)

    if do_goto_search:
        goto_search(driver)
        click_search_tab(driver)

    search_without_enter(account_name, driver)
    random_sleep(5, 10)
    #  random_sleep(10, 20)
    # get accounts from suggestion list
    accounts = get_search_result_from_suggestion(driver, account_name, content='element')
    for account in accounts:
        screen_name = account['screen_name']
        if screen_name.strip().lower() == account_name.strip().lower():
            LOGGER.debug('Click one item of suggestion list')
            account['element'].click()
            return True

    press_enter(driver)
    click_search_result_people_tab(driver)
    random_sleep(10, 20)
    results = get_search_result_from_tab_people(driver, content='element')
    #  LOGGER.debug(f'results: {results}')
    for account in results:
        screen_name = account['screen_name']
        if screen_name.strip().lower() == account_name.strip().lower():
            LOGGER.debug('Click one item of research result')
            account['element'].click()
            return True

    return False


def swipe_up_element(driver, element, times=1, duration=5000, delta=10,
                     end_y=None):
    location = element.location
    size = element.size

    start_x = location['x'] + size['width'] // 2
    start_y = location['y'] + size['height']
    end_x = start_x
    if not end_y:
        end_y = location['y']

    while times > 0:
        LOGGER.debug(f'start_x: {start_x}, start_y: {start_y},'
                     f' end_x: {end_x}, end_y: {end_y}')
        try:
            driver().swipe(start_x, start_y, end_x, end_y, duration=duration)
        except InvalidElementStateException as e:
            LOGGER.error(e)
            driver().swipe(start_x, start_y - delta, end_x, end_y, duration=duration)
        times -= 1


def swipe_up_search_result(driver, times=1, duration=5000):
    LOGGER.debug('Swipe up element of search result list')
    result_element = driver().find_element_by_id(
        'android:id/list')
    swipe_up_element(driver, result_element, times, duration)


def open_messages(driver):
    pass


def open_notification(driver):
    pass


def open_target(driver, target):
    pass


def check_conditions(driver):
    pass


def press_enter(driver):
    driver().press_keycode(66)


def connect_vpn(driver, country):
    try:
        acc_email = 'admin@noborders.net'
        acc_pass = 'Surviraladmin789'

        # Launch surfshark
        start_app(driver, 'surfshark')

        # Login if required
        login_retries = 0
        while True:
            login_retries += 1

            login_btn_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/onboarding_login_action')
            login_btn_xpath = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.widget.TextView')

            if login_btn_id or login_btn_xpath:
                login_btn = login_btn_id or login_btn_xpath
                login_btn[0].click()
                time.sleep(3)

                email_input_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/login_email')
                email_input_xpath = driver().find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.ScrollView/android.view.ViewGroup/android.widget.LinearLayout[1]/android.widget.FrameLayout/android.widget.EditText')
                email_input = email_input_id or email_input_xpath
                email_input[0].send_keys(acc_email)
                time.sleep(3)

                password_input_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/login_password')
                password_input_xpath = driver().find_elements_by_id('//android.widget.EditText[@content-desc=" "]')
                password_input = password_input_id or password_input_xpath
                password_input[0].send_keys(acc_pass)
                time.sleep(3)

                login_btn_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/login_menu')
                login_btn_xpath = driver().find_elements_by_id(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.view.ViewGroup/androidx.appcompat.widget.LinearLayoutCompat/android.widget.TextView')
                login_btn = login_btn_id or login_btn_xpath
                login_btn[0].click()
                time.sleep(7)

                alert_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/alertTitle')
                alert_xpath = driver().find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/androidx.appcompat.widget.LinearLayoutCompat/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView')
                if not alert_id and not alert_xpath:
                    break

            if login_retries >= 3:
                return False

            else:
                break

        # Connect VPN
        connect_retires = 0
        while True:
            connect_retires += 1

            # check if vpn is already connected
            current_server_name_id = driver().find_elements_by_id(
                'com.surfshark.vpnclient.android:id/current_server_name')
            current_server_name_xpath = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.view.ViewGroup/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.TextView')

            if current_server_name_id or current_server_name_xpath:
                current_server = current_server_name_id or current_server_name_xpath

                if country in current_server[0].text:
                    return True
                else:
                    # Disconnect vpn
                    disconnect_btn = driver().find_elements_by_id(
                        'com.surfshark.vpnclient.android:id/main_disconnect_action')
                    if disconnect_btn:
                        disconnect_btn[0].click()
                        time.sleep(3)
                    else:
                        return False

            restart_app(driver, 'surfshark')
            time.sleep(10)

            location_btn_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/navigation_locations')
            location_btn_xpath1 = driver().find_elements_by_xpath(
                '//android.widget.FrameLayout[@content-desc="Locations"]/android.widget.ImageView')
            location_btn_xpath2 = driver().find_elements_by_xpath(
                '//android.widget.FrameLayout[@content-desc="Locations"]')

            if location_btn_id or location_btn_xpath1 or location_btn_xpath2:
                location_btn = location_btn_id or location_btn_xpath1 or location_btn_xpath2
                location_btn[0].click()
                time.sleep(3)

            search_btn_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/serverlist_search')
            search_btn_xpath = driver().find_elements_by_xpath('//android.widget.TextView[@content-desc="Search"]')

            if search_btn_id or search_btn_xpath:
                search_btn = search_btn_id or search_btn_xpath
                search_btn[0].click()
                time.sleep(3)

            search_bar_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/search_src_text')
            search_bar_xpath = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup[1]/androidx.appcompat.widget.LinearLayoutCompat/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.EditText')
            if search_bar_xpath or search_bar_id:
                search_bar = search_bar_xpath or search_bar_id
                search_bar[0].send_keys(country)
                time.sleep(3)

            country_btn_xpath1 = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup[2]/android.view.ViewGroup/android.widget.FrameLayout/android.widget.RelativeLayout/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]')
            country_btn_xpath2 = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup[2]/android.view.ViewGroup/android.widget.FrameLayout/android.widget.RelativeLayout/androidx.recyclerview.widget.RecyclerView/android.view.ViewGroup[2]/android.widget.TextView')

            if country_btn_xpath1 or country_btn_xpath2:
                country_btn = country_btn_xpath1 or country_btn_xpath2
                country_btn[0].click()
                time.sleep(25)
            else:
                print(f"{country} is not available in surfshark list.")
                return False

            # Check connection accept alert
            connection_alert_id = driver().find_elements_by_id('android:id/alertTitle')
            connection_alert_xpath = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView')
            connection_alert = connection_alert_id or connection_alert_xpath
            if connection_alert:
                accept_btn_id = driver().find_elements_by_id('android:id/button1')
                accept_btn_xpath = driver().find_elements_by_xpath(
                    '/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.Button[2]')
                accept_btn = accept_btn_id or accept_btn_xpath
                if accept_btn:
                    accept_btn[0].click()
                    time.sleep(5)

            # close avoid connection issue alert
            connection_issue_xpath = driver().find_elements_by_id(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.TextView[1]')
            if connection_issue_xpath:
                if connection_issue_xpath[0].text == "Avoid potential connection issues":
                    close_btn_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/close')
                    close_btn_xpath = driver().find_elements_by_xpath(
                        '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ScrollView/android.widget.LinearLayout/android.widget.TextView[4]')
                    close_btn = close_btn_id or close_btn_xpath
                    close_btn[0].click()
                    time.sleep(5)

            # Make sure that connection was successfull
            connection_status_id = driver().find_elements_by_id('com.surfshark.vpnclient.android:id/connection_status')
            connection_status_xpath = driver().find_elements_by_xpath(
                '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.view.ViewGroup/android.view.ViewGroup/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout[2]/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.TextView')
            connection_status = connection_status_id or connection_status_xpath
            if connection_status:
                if connection_status[0].text.lower() == "connected":
                    return True

            if connect_retires >= 3:
                print(f"Couldn't connect vpn in 3 tries.")
                return False

    except Exception as e:
        print(e)
        return False


def get_random_wait_time(min, max):
    random_time = random.randrange(min, max)
    time.sleep(random_time)


'''
*****************************************
GETSMSCODE FOR TWITTER
*****************************************
'''


def get_summary():
    url = "http://api.getsmscode.com/usdo.php?"
    payload = {
        "action": "login",
        "username": "pay@noborders.net",
        "token": GETSMSCODE_API_KEY,
    }
    #  payload = urlencode(payload)
    #  full_url = url + payload
    response = requests.post(url, data=payload)
    response = response.content.decode("utf-8")

    return response


def get_mobile_list():
    url = "http://api.getsmscode.com/usdo.php?"
    payload = {
        "action": "mobilelist",
        "username": "pay@noborders.net",
        "token": GETSMSCODE_API_KEY,
    }
    #  payload = urlencode(payload)
    #  full_url = url + payload
    response = requests.post(url, data=payload)
    response = response.content.decode("utf-8")

    return response


def get_twitter_number(mobile=None, pid=GETSMSCODE_PID):
    url = "http://api.getsmscode.com/usdo.php?"
    if mobile:
        payload = {
            "action": "getmobile",
            "username": "pay@noborders.net",
            "token": GETSMSCODE_API_KEY,
            "pid": pid,
            "mobile": mobile
        }
    else:
        payload = {
            "action": "getmobile",
            "username": "pay@noborders.net",
            "token": GETSMSCODE_API_KEY,
            "pid": pid,
        }
    payload = urlencode(payload)
    full_url = url + payload
    response = requests.post(url=full_url)
    response = response.content.decode("utf-8")

    LOGGER.debug(f'Response when getting number: {response}, pid: {pid}')
    try:
        Phone.objects.get_or_create(number=response, pid=pid)
    except Exception as e:
        LOGGER.error(e)

    return response


def get_twitter_number_ui(mobile=None, pids=('66', GETSMSCODE_PID), retry_times=3):
    # retry 3 times to get phone number
    # error: +Message|unavailable
    pids = list(pids)
    while retry_times > 0:
        if len(pids) == 0:
            pid = GETSMSCODE_PID
        else:
            pid = pids.pop()
        LOGGER.debug(f'The pid to get phone number: {pid}')
        phone = get_twitter_number(pid=pid)
        if "balance is not enough" in phone:
            raise GetSmsCodeNotEnoughBalance
        LOGGER.debug(f'phone number: {phone}')
        if 'unavailable' in phone:
            random_sleep(20, 30)
            retry_times -= 1
        else:  # otherwise got the right number
            return phone, pid
            break
        if retry_times <= 0:
            LOGGER.critical('Cannot get valid phone number,'
                            ' now stop the bot')
    return '', ''


def save_sms(phone, sms, pid, purpose=None):
    if purpose:
        LOGGER.debug(f'Save phone and sms for "{purpose}": {phone}, {pid}, {sms}')
    else:
        LOGGER.debug(f'Save phone and sms: {phone}, {pid}, {sms}')

    users = TwitterAccount.objects.filter(phone=phone)
    if len(users) == 1:
        user = users[0]
    else:
        user = None

    if user:
        (number, created) = Phone.objects.get_or_create(
            number=phone, pid=pid, user=user)
    else:
        (number, created) = Phone.objects.get_or_create(
            number=phone, pid=pid)

    if purpose:
        Sms.objects.get_or_create(number=number, content=sms, purpose=purpose)
    else:
        Sms.objects.get_or_create(number=number, content=sms)


def get_twitter_sms(phone_number, pid=GETSMSCODE_PID, purpose=None):
    # Do not Request Get SMS Fast , Every 10s is best.
    # Too Fast will be block our system
    url = "http://api.getsmscode.com/usdo.php?"
    payload = {
        "action": "getsms",
        "username": "pay@noborders.net",
        "token": GETSMSCODE_API_KEY,
        "pid": pid,
        "mobile": phone_number,
        "author": "pay@noborders.net",
    }
    payload = urlencode(payload)
    full_url = url + payload
    for x in range(10):
        response = requests.post(url=full_url).text
        LOGGER.debug(f'SMS content for {phone_number}: {response}')
        #  print(response)
        save_sms(phone_number, response, pid, purpose)
        code = [int(s) for s in response.split() if s.isdigit() if len(s) == 6 if s != 40404]
        if code:
            LOGGER.debug(f'SMS code for {phone_number}: {code[0]}')
            return code[0]
        if 'code is' in response:
            otp = response.split("code is ")[1][:6]
            LOGGER.debug(f'SMS code for {phone_number}: {otp}')
            return otp
        time.sleep(4)

    return False


def ban_twitter_number(phone_number, pid=GETSMSCODE_PID):
    url = "http://api.getsmscode.com/usdo.php?"
    payload = {
        "action": "addblack",
        "username": "pay@noborders.net",
        "token": GETSMSCODE_API_KEY,
        "pid": GETSMSCODE_PID,
        "mobile": phone_number,
        "author": "pay@noborders.net",
    }
    payload = urlencode(payload)
    full_url = url + payload
    response = requests.post(url=full_url)
    # save the result
    try:
        Phone.objects.update_or_create(number=phone_number, pid=pid,
                                       is_banned=True, ban_result=response)
    except Exception as e:
        LOGGER.error(e)
    return response


def get_random_password():
    alphaneumeric_characters = string.ascii_letters + string.digits
    result_str = 'Ang1' + ''.join(random.choice(alphaneumeric_characters) for i in range(4))
    return result_str


def get_real_random_password(passwd_start_len=8, passwd_end_len=20):
    pw_len = random.randint(passwd_start_len, passwd_end_len)
    all_char_set = string.digits + string.ascii_letters + string.punctuation
    pw_char_set = all_char_set.replace('\\', '')
    random_pw = ''.join(random.choices(pw_char_set, k=pw_len))
    return random_pw


def get_random_username():
    url = "https://randommer.io/Name"
    full_name = requests.post(url, data={"number": 1, "type": "fullname"}).json()[0]
    return full_name


def delete_download_files(port):
    LOGGER.debug('Delete all files in directory Download')
    cmd = f'adb -s emulator-{port} shell rm -rf /storage/emulated/0/Download/*'
    p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p.wait()
    return True


def push_image_to_device(file_path, port):
    LOGGER.debug(f'Push the file to directory Download: {file_path}')
    cmd = f'adb -s emulator-{port} push {file_path} /storage/emulated/0/Download/'
    LOGGER.debug(cmd)
    p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p.wait()
    return True


def download_image(url, image_name):
    local_path = os.path.join(BASE_DIR, 'images/' + image_name)
    LOGGER.debug(f'Download "{local_path}" from "{url}"')
    urllib.request.urlretrieve(url, local_path)


import time
from functools import wraps


def retry(tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """

    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            max_tries, max_delay = tries, delay
            while max_tries > 1:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), max_delay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(max_delay)
                    max_tries -= 1
                    max_delay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


def log_activity(avd_id, action_type, msg, error):
    try:
        details = {
            "avd_id": avd_id,
            "action_type": action_type,
            "action": msg,
            "error": error,
        }
        LOGGER.debug(f'Log Activity: {details}')
    except Exception as e:
        print(e)


def terminate_device(port):
    cmd = f'lsof -t -i tcp:{port} | xargs kill -9'
    process = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
    process.wait()


def terminate_appium(port):
    # get appium running pid
    try:
        cmd = f"ss -l -p -n | grep {port}"
        output = subprocess.getoutput(cmd)
        pid = output.split("pid=")[-1].split(",")[0]
    except:
        pass

    # kill process
    if pid:
        cmd = f"kill -9 {pid}"
        process = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        process.wait()
        time.sleep(2)


def swipe_up_half_screen(driver, duration=2000):
    size = driver().get_window_size()
    position = driver().get_window_position()

    x = position['x']
    y = position['y']
    width = size['width']
    height = size['height']

    LOGGER.debug(f'x: {x}, y: {y}, width: {width}, height: {height}')

    start_x = x + width // 2
    start_y = y + int(height * 0.8)
    end_x = start_x
    end_y = y + int(height * 0.2)

    LOGGER.debug(f'start_x: {start_x}, start_y: {start_y},'
                 f' end_x: {end_x}, end_y: {end_y}')

    driver().swipe(start_x, start_y, end_x, end_y, duration)
    time.sleep(1)


def swipe_up(driver):
    size = driver().get_window_size()
    x = size['width']
    y = size['height']

    x1 = x * 0.5
    y1 = y * 0.8
    y2 = x * 0.1
    t = 5000

    driver().swipe(x1, y1, x1, y2, t)
    time.sleep(1)


def swipe_down(driver):
    size = driver().get_window_size()
    x = size['width']
    y = size['height']

    x1 = x * 0.5
    y1 = y * 0.1
    y2 = y * 0.8
    t = 5000

    driver().swipe(x1, y1, x1, y2, t)
    time.sleep(1)


def perform_random_action(driver, bot_name):
    """Search one random topic, and select some tweets in the tab latest,
    then like them.
    """
    LOGGER.debug('perform random actions')
    try:
        followed_accounts = []

        # tags_list = XANALIA_TAGS + CAZICAZI_TAGS
        tags_list = XANALIA_TAGS

        n_likes = random.randrange(4, RANDOM_LIKE_MAX_NUMBER)
        n_follows = random.randrange(4, RANDOM_FOLLOW_MAX_NUMBER)
        search_tag = random.choice(tags_list)

        LOGGER.debug(f'n_likes: {n_likes}, n_follows: {n_follows},'
                     f' search_tag: {search_tag}')

        goto_home(driver)
        goto_search(driver)

        # click on search bar
        #  LOGGER.debug('click on search bar')
        click_search_tab(driver)
        random_sleep()

        # input search query in search bar
        #  LOGGER.debug('input search query in search bar')
        search_without_enter(search_tag, driver)
        press_enter(driver)
        #  time.sleep(3)
        random_sleep(5)

        # open searched profile
        LOGGER.debug('open searched profile')
        latest_xpath1 = driver().find_elements_by_xpath('//android.widget.LinearLayout[@content-desc="Latest"]')
        latest_xpath2 = driver().find_elements_by_xpath(
            '//android.widget.LinearLayout[@content-desc="Latest"]/android.widget.TextView'
        )
        latest_btn = latest_xpath1 or latest_xpath2
        LOGGER.debug('click tab latest')
        latest_btn[0].click()
        #  time.sleep(3)
        random_sleep()

        # Like posts
        LOGGER.debug('Like posts')
        total_followed = 0
        liked = 0
        total_tries = 0

        while True:
            total_tries += 1

            if total_tries >= (liked + 7):
                LOGGER.debug(f'total_tries: {total_tries}, liked: {liked}')
                LOGGER.debug(f'total_tries >= (liked + 7), now break loop')
                break

            if liked >= n_likes:
                LOGGER.debug(f'n_likes: {n_likes}, liked: {liked}')
                LOGGER.debug(f'liked >= n_likes, now break loop')
                break

            # get all tweets on the page
            # wait the element appear
            if hasattr(driver, '__self__') and hasattr(driver.__self__, 'wait_obj'):
                LOGGER.debug('Wait for search result')
                locator_type = By.ID
                element_locator = 'com.twitter.android:id/outer_layout_row_view_tweet'
                try:
                    element = driver.__self__.wait_obj.until(EC.presence_of_element_located(
                        (locator_type, element_locator)))
                except Exception as e:
                    LOGGER.exception(e)

            tweets = driver().find_elements_by_id('com.twitter.android:id/outer_layout_row_view_tweet')
            LOGGER.debug(f'len(tweets): {len(tweets)}')

            # loop over the tweets and like them
            for x in range(len(tweets)):
                # Open tweet
                LOGGER.debug('Open tweet')
                refreshed_tweets = driver().find_elements_by_id('com.twitter.android:id/outer_layout_row_view_tweet')
                tweet = refreshed_tweets[x]
                element_xy_bounds = tweet.get_attribute('bounds')
                element_coordinates = element_xy_bounds.replace("'", " ").replace("][", ",").replace("[", " ").replace(
                    "]", " ").replace(" ", "").split(",")
                x1 = int(element_coordinates[0])
                y1 = int(element_coordinates[1])
                driver().tap([(x1, y1)])
                time.sleep(2)

                # Follow Process
                if total_followed <= n_follows:
                    profile_btn_id_1 = driver().find_elements_by_id('com.twitter.android:id/name')
                    profile_btn_id_2 = driver().find_elements_by_id('com.twitter.android:id/screen_name')
                    profile_btn = profile_btn_id_1 or profile_btn_id_2
                    profile_btn[0].click()
                    time.sleep(5)

                    follow_btn_id = driver().find_elements_by_id('com.twitter.android:id/button_bar_follow')
                    follow_btn_acc_id = driver().find_elements_by_accessibility_id('Follow MOBOX. Follow.')
                    follow_btn_xpath = driver().find_elements_by_xpath(
                        '//android.widget.Button[@content-desc="Follow MOBOX. Follow."]')
                    follow_btn = follow_btn_id or follow_btn_acc_id or follow_btn_xpath
                    if follow_btn:
                        follow_btn[0].click()
                    time.sleep(1)

                    # get username of account on which action is being performed
                    account_username_id = driver().find_elements_by_id('com.twitter.android:id/user_name')
                    account_username_xpath = driver().find_elements_by_xpath(
                        '/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.widget.RelativeLayout/android.view.ViewGroup/android.widget.RelativeLayout/android.widget.FrameLayout[1]/android.widget.LinearLayout/android.widget.LinearLayout[2]/android.widget.LinearLayout/android.widget.LinearLayout[1]/android.widget.TextView')
                    account_username = account_username_id or account_username_xpath
                    account_username = account_username[0].text.replace('@', '')
                    if account_username not in followed_accounts:
                        followed_accounts.append(account_username)
                    time.sleep(1)

                    driver().press_keycode(4)
                    time.sleep(1)

                # Liking process
                for i in range(5):
                    time.sleep(2)

                    # check if already liked
                    already_liked_btn_accs_id = driver().find_elements_by_accessibility_id('Like (Liked)')
                    already_liked_btn_xpath = driver().find_elements_by_xpath(
                        '//android.widget.ImageButton[@content-desc="Like (Liked)"]')
                    already_liked = already_liked_btn_xpath or already_liked_btn_accs_id
                    if not already_liked:
                        # find like button
                        like_btn_accs_id = driver().find_elements_by_accessibility_id('Like')
                        like_btn_xpath = driver().find_elements_by_xpath(
                            '//android.widget.ImageButton[@content-desc="Like"]')
                        like_btn = like_btn_accs_id or like_btn_xpath

                        if like_btn:
                            like_btn[0].click()
                            liked += 1
                            break
                        else:
                            swipe_up(driver)

                driver().press_keycode(4)

            swipe_up(driver)

        goto_home(driver)

        # Write random action data in csv
        # followed_accounts_str = ""
        # for x in followed_accounts:
        #     if not followed_accounts_str:
        #         followed_accounts_str = x
        #     else:
        #         followed_accounts_str += ", " + x
        # write_output([UserAvd.objects.get(name=bot_name).twitter_account.screen_name, followed_accounts[1:], search_tag, len(followed_accounts[1:]), len(followed_accounts[1:])], f"random_action_{str(datetime.date.today())}")

        
        return True

    except Exception as e:
        tb = traceback.format_exc()
        
        LOGGER.exception(e)
        return False


def get_random_profile_banner_image():
    pages_list = [x for x in range(20)]
    banner_query_list = ["mountain",
                         "universe",
                         "forest",
                         "waterfall",
                         "river",
                         "pets",
                         "cats",
                         "wild",
                         "abstract",
                         "group",
                         ]

    random.shuffle(pages_list)
    page = random.choice(pages_list)
    profile_data = requests.get(
        url="https://api.unsplash.com/search/photos/?client_id=35p1IHnOOwBqsSYny6EAteB9EpApVsiWwZLzefiG0sA&query"
            f"=face&per_page=50&page={page} "
    )
    time.sleep(3)
    profile_data = json.loads(profile_data.content.decode('utf-8'))
    profile_image_list = [x['urls']['regular'] for x in profile_data.get('results')]

    random.shuffle(pages_list)
    random.shuffle(banner_query_list)
    page = random.choice(pages_list)
    query = random.choice(banner_query_list)
    banner_data = requests.get(
        url=f"https://api.unsplash.com/search/photos/?client_id=35p1IHnOOwBqsSYny6EAteB9EpApVsiWwZLzefiG0sA&query"
            f"={query}&per_page=50&page={page} "
    )
    time.sleep(3)
    banner_data = json.loads(banner_data.content.decode('utf-8'))
    banner_image_list = [x['urls']['regular'] for x in banner_data.get('results')]

    return profile_image_list, banner_image_list


def update_blank_images():
    ta_qs = TwitterAccount.objects.filter(Q(profile_image__isnull=True)
                                          | Q(banner_image__isnull=True)
                                          )
    if ta_qs:
        count = ta_qs.count()
        profiles, banners = [], []
        while len(profiles) <= count and len(banners) <= count:
            profiles_list, banners_list = get_random_profile_banner_image()
            profiles += profiles_list
            banners += banners_list

        for x, ta in enumerate(ta_qs):
            ta.profile_image = profiles[x]
            ta.banner_image = banners[x]
            ta.save()


def string_to_int(number_str):
    multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000, 'T': 1000000000000}

    number_str = number_str.replace(",", "")

    if number_str[-1].isdigit():
        return int(number_str)

    mult = multipliers[number_str[-1]]
    return int(float(number_str[:-1]) * mult)


def write_output(data, file_name):
    write_mode = "ab"
    logs_folder = "../logs"

    if not os.path.exists(logs_folder):
        os.mkdir(logs_folder)

    file_path = logs_folder + "/" + file_name + ".csv"

    with open(file_path, mode=write_mode) as csvFile:
        row = unicodecsv.writer(csvFile, delimiter=",", lineterminator="\n")
        row.writerow(data)


def get_real_driver(driver):
    if isinstance(driver, WebDriver):
        return driver
    else:
        return driver()


def find_element(driver, element, locator, locator_type=By.XPATH, page=None,
                 timeout=10):
    """Waint for an element, then return it or None"""
    driver = get_real_driver(driver)
    wait_obj = WebDriverWait(driver, timeout)
    try:
        ele = wait_obj.until(
            EC.presence_of_element_located(
                (locator_type, locator)))
        if page:
            LOGGER.debug(
                f'Find the element "{element}" in the page "{page}"')
        else:
            LOGGER.debug(f'Found the element: {element}')
        return ele
    except (NoSuchElementException, TimeoutException) as e:
        if page:
            LOGGER.warning(f'Cannot find the element "{element}"'
                           f' in the page "{page}"')
        else:
            LOGGER.warning(f'Cannot find the element: {element}')


def click_element(driver, element, locator, locator_type=By.XPATH,
                  timeout=10):
    driver = get_real_driver(driver)
    """Find an element, then click and return it, or return None"""
    ele = find_element(driver, element, locator, locator_type, timeout=timeout)
    if ele:
        ele.click()
        LOGGER.debug(f'Click the element: {element}')
        return ele


def find_page(driver, page, element, locator, locator_type=By.XPATH, timeout=10):
    """Find en element of a page, then return it or return None"""
    return find_element(driver, element, locator, locator_type, page, timeout)


def find_element_from_parent(parent_element, element, locator,
                             locator_type=By.XPATH):
    """Find child element from parent, then return it or None"""
    try:
        ele = parent_element.find_element(by=locator_type, value=locator)
        LOGGER.debug(f'Found the element: {element}')
        return ele
    except NoSuchElementException as e:
        LOGGER.warning(f'Cannot find the element: {element}')


def check_pinned_tweet(tweet_element):
    #  pin_icon_id = 'com.twitter.android:id/social_context_badge'
    #  if find_element_from_parent(tweet_element, 'pinned tweet',
    #          pin_icon_id, By.ID):
    #      return tweet_element

    content = tweet_element.get_attribute('content-desc')
    LOGGER.debug(f'content: {content}')
    if '. . . . Pinned Tweet.' in content:
        LOGGER.debug('Find pinned tweet by content-desc')
        return tweet_element


def check_promoted_tweet(driver, tweet_element):
    promote_id = 'com.twitter.android:id/tweet_promoted_badge'
    if find_element_from_parent(tweet_element, 'promoted tweet',
                                promote_id, By.ID):
        return tweet_element

    promote_id1 = 'com.twitter.android:id/tweet_promoted_badge_bottom'
    if find_element_from_parent(tweet_element, 'promoted tweet',
                                promote_id1, By.ID):
        return tweet_element

    content = tweet_element.get_attribute('content-desc')
    LOGGER.debug(f'content: {content}')
    if '. . . Promoted.' in content:
        LOGGER.debug('Find promoted tweet by content-desc')
        return tweet_element

    promote_frame_xpath = ('//android.widget.TextView'
                           '[@resource-id="com.twitter.android:id/title"]/..')
    title_id = 'com.twitter.android:id/title'
    ele = find_element(driver, 'title', title_id, By.ID)
    if ele:
        if 'Promoted Tweet' in ele.text:
            LOGGER.debug(f'Find promoted tweet by title: {ele.text}')
            return driver().find_element_by_xpath(promote_frame_xpath)


def ignore_pinned_promoted_tweet(driver, tweet_element):
    flag = False
    ele = check_pinned_tweet(tweet_element)
    if ele:
        LOGGER.debug('Ignore one pinned tweet')
        swipe_up_element(driver, ele)
        return True

    ele = check_promoted_tweet(driver, tweet_element)
    if ele:
        LOGGER.debug('Ignore one promoted tweet')
        swipe_up_element(driver, ele)
        return True

    return flag


def get_latest_tweet1(driver):
    LOGGER.debug('Get latest tweet other than pinned or promoted tweet')

    while True:
        random_sleep()
        tweet_elements = driver().find_elements_by_id("com.twitter.android:id/row")
        if not tweet_elements:
            LOGGER.error('Cannot find tweet element')
            return None

        for tweet_element in tweet_elements:
            if ignore_pinned_promoted_tweet(driver, tweet_element):
                continue
            else:
                return tweet_element


def get_latest_tweet(driver):
    LOGGER.debug('Get latest tweet other than pinned or promoted tweet')

    times = 0
    while True:
        random_sleep()
        tweet_elements = driver().find_elements_by_id("com.twitter.android:id/row")
        if not tweet_elements:
            LOGGER.error('Cannot find tweet element')
            return None

        element = None
        for tweet_element in tweet_elements:
            if check_pinned_tweet(tweet_element) or check_promoted_tweet(
                    driver, tweet_element):
                element = tweet_element
                continue
            else:
                return tweet_element

        #  swipe_up(driver)
        #  element = driver().find_element_by_id(
        #          'com.twitter.android:id/outer_layout_row_view_tweet')
        if element:
            swipe_up_element(driver, element, duration=2000)
        #  swipe_up_half_screen(driver)
        times += 1
        if times > 20:
            LOGGER.error('Some error happened, and exit loop')
            break


def check_element_is_tweet_element(element):
    tweet_row_id = 'com.twitter.android:id/row'
    if find_element_from_parent(element, 'tweet element', tweet_row_id, By.ID):
        return True
    else:
        return False


def get_latest_tweet_by_viewgroup(driver, except_ids=[]):
    LOGGER.debug('Get latest tweet by ViewGroup other than pinned or promoted tweet')
    all_list_id = 'android:id/list'
    tweet_viewgroup_element_xpath = ('//androidx.recyclerview.widget.RecyclerView'
                                     '[@resource-id="android:id/list"]/android.view.ViewGroup')
    tweet_row_id = 'com.twitter.android:id/row'
    times = 0
    while True:
        random_sleep()
        tweet_viewgroup_elements = driver().find_elements_by_xpath(
            tweet_viewgroup_element_xpath)
        if not tweet_viewgroup_elements:
            LOGGER.error('Cannot find tweet ViewGroup element')
            return None

        element = None
        for tweet_viewgroup_element in tweet_viewgroup_elements:
            if not check_element_is_tweet_element(tweet_viewgroup_element):
                continue

            tweet_element = tweet_viewgroup_element.find_element_by_id(
                tweet_row_id)
            if check_pinned_tweet(tweet_element) or check_promoted_tweet(
                    driver, tweet_element):
                element = tweet_viewgroup_element
                continue

            content = tweet_element.get_attribute('content-desc')
            #  LOGGER.debug(f'content: {content}')
            p = '(.*( \.){2,})'
            m = re.match(p, content, re.MULTILINE | re.DOTALL)
            if m:
                effect_content = m[0]
                if effect_content in except_ids:
                    LOGGER.debug(f'Ignore the element content: {effect_content}')
                    element = tweet_viewgroup_element
                    continue
                else:
                    return tweet_viewgroup_element
            else:
                LOGGER.error('Cannot find effective content')
                #  effect_content = ''

        #  swipe_up(driver)
        #  element = driver().find_element_by_id(
        #          'com.twitter.android:id/outer_layout_row_view_tweet')
        if element:
            swipe_up_element(driver, element, duration=2000)
            #  swipe_up_tweet(driver, element, duration=2000)
        #  swipe_up_half_screen(driver)
        times += 1
        if times > 20:
            LOGGER.error('Some erroe happened, and exit loop')
            break


def click_suggested_follows_close_button(driver):
    suggested_account_dismiss_button_id = 'com.twitter.android:id/dismiss'
    suggested_account_dismiss_button_id1 = 'com.twitter.android:id/dismiss_btn'
    click_element(driver, 'dismiss button',
                  suggested_account_dismiss_button_id, By.ID)  # close suggested panel
    click_element(driver, 'dismiss button',
                  suggested_account_dismiss_button_id1, By.ID)  # close suggested panel


def tap_element(driver, element):
    LOGGER.debug('Tap the element')
    location = element.location
    size = element.size
    x = location['x'] + size['width'] // 2
    y = location['y'] + size['height'] // 2
    driver().tap([(x, y)], duration=1000)


def click_tweet_by_header(driver, tweet_element):
    header_id = 'com.twitter.android:id/tweet_header'
    try:
        driver().find_element_by_id(header_id).click()
        LOGGER.debug('Click the tweet header')
    except Exception as e:
        LOGGER.exception(e)
        tweet_element.click()
        LOGGER.debug('Click the tweet')


def swipe_up_tweet(driver, tweet_element, duration):
    container_id = 'android:id/list'
    header_tab_id = 'com.twitter.android:id/tabs_holder'

    container = driver().find_element_by_id(container_id)
    header = driver().find_element_by_id(header_tab_id)

    container_x = container.location['x']
    container_y = container.location['y'] - header.size['height']
    swipe_up_element(driver, tweet_element, duration=duration, end_y=container_y)


def update_or_create_comment(tweet_object, comment, is_used=False):
    return Comment.objects.update_or_create(tweet=tweet_object,
                                            comment=comment, is_used=is_used)


def update_or_create_comments(tweet_object, comments, is_used=False):
    for comment in comments:
        #  c = Comment(tweet=tweet_object, comment=comment, is_used=is_used)
        #  c.save()
        update_or_create_comment(tweet_object, comment=comment,
                                 is_used=is_used)


def check_comment_exists(comment):
    return Comment.objects.filter(comment=comment, is_used=True).exists()


def get_comment_from_db(tweet, retry_times=3, timeout=120, is_used=True):
    LOGGER.debug('Get comments from DB or API')
    (tweet_object, created) = Tweet.objects.get_or_create(text=tweet)
    get_one_from_api = False
    # this tweet doesn't exist in db, then get comment from API
    if created:
        get_one_from_api = True
    # The tweet existed
    else:
        comments = Comment.objects.filter(tweet=tweet_object, is_used=False)
        # no required comments, then get them from API
        if not comments:
            get_one_from_api = True
        else:
            LOGGER.debug('Get comments from DB')
            #  obj = comments.first()
            obj = random.choice(comments)

            # check comment existence
            if check_comment_exists(obj.comment):
                LOGGER.error(f'This comment existed in DB: {obj.comment}')
                return
            else:
                if is_used:
                    obj.is_used = is_used
                    obj.save()
                return obj.comment

    if get_one_from_api:
        LOGGER.debug('Get comments from API')
        comments = get_comment(tweet, retry_times=retry_times, timeout=timeout,
                               get_one=False)
        if not comments:
            LOGGER.warning(f'Cannot get comments from comment API')
            return
        # save the comments into db
        update_or_create_comments(tweet_object, comments)

        # get random comment
        c = random.choice(comments)

        # check comment existence
        if check_comment_exists(c):
            LOGGER.error(f'This comment existed in DB: {obj.comment}')
            return
        else:
            update_or_create_comment(tweet_object, c, is_used=is_used)
            return c

def delete_avd_by_name(avdname):
    try:
        cmd = f'avdmanager delete avd --name {avdname}'
        p = subprocess.Popen([cmd], stdin=subprocess.PIPE, shell=True, stdout=subprocess.DEVNULL)
    except Exception as e:
        pass

INSTA_PROFILE_BIO_LIST = [
"Making every day magical.",
"Loving fiercely. Stopping along the way to take photos.",
"Captivated from life, showing it here.",
"Trying to become the best. That is why first I am being the worst.",
"Creating a life I love.",
"Trying to remember who I was before the world told me who to be.",
"Girl with a strong desire to travel the world and explore new places.",
"We have tomorrows for a reason.",
"Serving you a feast of vibrant grids.",
"Just making sure to love life.",
"When it rains look for rainbows when it’s dark I look for stars.",
"I don’t want to forget something that once made us smile.",
"I survived because the fire inside me burned brighter than the fire around me.",
"You is kind, you is smart, you is important.",
"Die having memories don’t die with just dreams.",
"Take care of your body, it’s the only place you have to live.",
"Stay humble. Be kind. Work hard.",
"Throwing kindness around like confetti.",
"Don’t ever be afraid to shine.",
"Creating my own sunshine.",
"Going where I feel most alive.",
"Your life does not get better by chance. It gets better by a change.",
"Life is not a problem to be solved but a reality to be experienced.",
"I would rather die of passion than of boredom.",
"When daydreams become reality.",
"Perseverance pays… a lot!",
"If I was a writer I’d have a better Instagram bio quote.",
"The best of me is yet to come.",
"It wasn’t always easy but it’s worth it.",
"Gifted napper, talker, and ice cream eater.",
"Do you know what I like about people? Their dogs.",
"First I drink the coffee. Then I do things.",
"I already want to take a nap tomorrow.",
"Good times and tan lines.",
"My mission in life is not merely to survive but thrive.",
"Everything has beauty but not everyone can see.",
"Remember to always be yourself.",
"Happiness often sneaks in through a door you didn’t know you left open.",
"If I cannot do great things, I can do small things in a great way.",
"The bad news is time flies. The good news is you’re the pilot.",
"Sometimes you will never know the value of a moment until it becomes a memory.",
"We have nothing to fear but fear itself.",
"“Be strong” I whisper to my WiFi signal.",
"Chocolate never asks me any questions chocolate understands me.",
"Recovering from donuts addiction.",
"A preview of my life. This is not the whole movie. P.S.: if you wanna get behind the scenes just head to my stories.",
"Words cannot express my love and passion for Fridays. The photos might help",
"I’m starting to like Instagram, which is weird because I hate pictures.",
"I woke up and… posted this.",
"Sometimes I just want to give it all up and become a handsome billionaire.",
"Here to serve… The cat overlord.",
"I’m actually not funny. I’m just really mean and people think I’m joking.",
"Life is short… smile while you still have teeth.",
"I’m not sure how many problems I have because math is one of them.",
"A caffeine dependent life form.",
"I always prefer my puns to be intended.",
"Life is too short to wear boring undies.",
"Being a fruit loop in a bowl of cheerios.",
"We’re all just molecules.",
"Single and ready to get nervous around anyone I find attractive.",
"Hard work never killed anyone, but why take the chance?",
"My relationship status? Netflix, Oreos, and sweatpants.",
"I hope one day I will love something the way women in commercials love yogurt.",
"I still don’t understand Instagram, but here I am anyway.",
"We are born naked, hungry and wet. Then things just get worse.",
"One of the few people on Instagram who doesn’t claim to be a social media guru.",
"My hobbies are breakfast, lunch, and dinner.",
"Don’t listen to what they say, go see.",
"Chasing destinations around the globe.",
"Go the extra mile, it’s never crowded.",
"To truly live is the greatest adventure there is.",
"Catching flights, not feelings.",
"Escaping the ordinary.",
"Continuously traveling with my mind. My body sometimes joins.",
"Those who do not travel only read one page.",
"Better to see something once than hear about it a thousand times.",
"Is The journey (and the memories), not the arrival, what matters.",
"Travel far enough you meet yourself.",
"You can’t buy happiness but you can buy a plane ticket, and that’s kind of the same",
"All you need to know is that it’s possible.",
"Remember that happiness is a way of travel, not a destination.",
"Jobs fill your pocket but adventures fill your soul.",
"If you think adventures are dangerous, try routine: it’s lethal.",
"In love with cities I’ve never been to. Wanna discover them with me?",
"Take only memories, leave only footprints.",
"Never. Stop. Exploring.",
"Sand in my toes and saltwater in my curls.",
"Turning my dreams into my vision and my vision into reality.",
"Believing in making the impossible possible.",
"I’m not perfect but stories are always better with a touch of imperfection, right?",
"Leaving a bit of sparkle everywhere I go (Yes I do carry glitter in my pockets).",
"Smart. Strong. Silly.",
"Strong women rule the world.",
"I am cool but global warming made me hot.",
"Authentic Insta Bio Girl.",
"I’m a woman with ambition and a heart of gold.",
"Always wearing my invisible crown.",
"I feel like making my dreams come true.",
"I’d rather be hated for who I am than loved for who I am not.",
"Sometimes depressed, stressed…, but still well dressed.",
"So many books, so little time.",
"To infinity and beyond.",
"The bags under my eyes are Gucci.",
"Always give 100% — unless you’re donating blood.",
"Who runs the world? Repeat loud in front of a mirror: ME!",
"Happiness is always trendy.",
"I shine from within so no one can dim my light.",
"We are born to be real, not perfect.",
"Doing all things with kindness",
"Single, focused, blessed. Living life.",
"My standards are high. Just like my heels",
"A messy bun and having fun",
"Voice of the wild within every woman",
"I am a girl. I don’t smoke, drink or party every weekend. And I don’t sleep around or start drama to get attention. Yes, we do still exist!",
"Who cares, I am awesome.",
"Being worn a girl is the worst and the best that happened to me.",
"A great girl is classy, not trashy.",
"Who runs the world? GIRLS.",
"Don’t tell her how to dress, tell him not to rape.",
"Sassy, classy, and bad-assy.",
"Pour yourself a drink, put on some lipstick, and pull yourself together.",
"Leave a little sparkle everywhere you go.",
"Girls don’t wait for the prince anymore. They just pack and travel the world.",
"Simplicity is the key to happiness.",
"The best ist yet to come.",
"Slowing Down.",
"9-GRID Storyteller.",
"Spreading Smiles.",
"Creativity solves everything.",
"To travel is to live.",
"This seat is taken.",
"World’s most annoying couple.",
"I don’t make mistakes, I date them.",
"“99% coffee”.",
"Nothing but blue skies.",
"Go wild for a while.",
"Optimism is contagious.",
"Making history, I mean… Insta stories…",
"Nobody is perfect.",
"Stay classy.",
"Namast’ay (in bed).",
"There is beauty in simplicity.",
"As free as the ocean.",
"Just keep moving.",
"I woke up like this.",
"A camera in hand.",
"Instagram nerd.",
"Your vibe attracts your tribe.",
"L💖VE is in the air",
"Just click follow button 😉",
"L❤️ ver not a fighter spreading ✌️ all over the 🌎",
"Laugh while you have teeth 😀",
"Welcome to my d👑m",
"Currently hanging out in 🇵🇹 (+ flag country)",
"I love all animals 🐶",
"Survivor 🎗️",
"Traveller ✈️ Book Lover 📖",
"Obsessed with tacos 🌮",
"Saving trees by not doing my homework ✏️📚📖",
"Sleep 💤 and get relax. Great Ideas will come 💭",
"Never Hear Bad 🙉, Never Look Bad 🙊, Never Talk Badly 🙊",
"👇 Check out my photos 👇",
"Living my dreams.",
"WiFi + food + my bed = PERFECTION.",
"Don’t like me? Don’t care.",
"Bad decisions make for the best stories.",
"Kind of a good samaritan, terrible athlete, but extremely blessed in the napping skills department.",
"All you hipsters need to stop wearing Nirvana shirts if you don’t even listen to them.",
"Keep the dream alive: Hit the snooze button.",
"Don’t follow me because I don’t even know where I’m going.",
"I smile because I have no idea what is going on anymore.",
"Naturally and artificially flavored.",
"God gave me a lot of hair, but not a lot of height.",
"Acting like summer & walking like rain.",
"A Nomad in search of the perfect burger.",
"Never forget, the world is yours. Terms and conditions may apply.",
"I can resist everything except temptation.",
"My blood is made of coffee.",
"Maybe I’m born with it.",
"It’s not a phase, it’s who I am.",
"You can’t make everybody happy, you aren’t a jar of Nutella.",
"My only real long term goal is to end up on Ellen’s show.",
"Give me the chocolate and nobody will get hurt.",
"The future is shaped by your dreams. Stop wasting time and go to sleep!",
"This is my simple Coffee dependent life.",
"I need 6 months of vacation twice a year.",
"All my life I thought the air was free until I bought a bag of chips.",
"Cupcakes are muffins that believed in miracles.",
"If you fall, worry not. The floor will be there.",
"I followed my heart, it led me to the fridge.",
"I don’t look like this in real life.",
"Taking naps is so childish, I prefer to call them horizontal life pauses.",
"Ugg life.",
"It’s never too late to be who you might have been.",
"Savage attitude but a golden heart.",
"Make peace with your broken pieces.",
"Why blend in when you born to stand out.",
"I have to be funny because being hot just isn’t an option for me at this point.",
"God bless this hot mess!",
"Where the heck am I? How did I get here?",
"Hi, my hobbies include breakfast, lunch, and dinner.",
"I was not born for mediocre.",
"Just a cupcake looking for a stud muffin.",
"Insert pretentious stuff about myself here.",
"Living vicariously through myself.",
"You’re just jealous cuz I got swag.",
"Good girl with a good playlist.",
"Don’t try to change me.",
"Stay a mystery, it attracts more curious people.",
"Forgive? Yes. Forget? Never.",
"I get it from my mama.",
"Why look up at the stars when the biggest star is me.",
"A coconut a day keeps the doctor away.",
"Risk-taker. Adventurer. Globetrotter.",
"Living my life on my own terms.",
"I might look like I’m doing nothing, but in my head, I’m quite busy.",
"Life is either a daring adventure or nothing at all.",
"I was born to… do exactly what I’m doing today.",
"I might not be where I want to be yet but I get closer every day.",
"One day, I hope to be a happy old man telling wild stories from my Instagram grid.",
"I don’t care what people think of me. This is me in the rawest form.",
"Born to express, not impress.",
"You couldn’t handle me even if I came with instructions.",
"I got here by being me, so I’ll continue being me.",
"Be all in or get out. There is no in-between.",
"Kilometers are shorter than miles. To save gas I’ll take my next trip in kilometers.",
"Being positive in a negative situation is not naïve, it’s leadership.",
"Attitudes are contagious. Make your worth catching.",
"One bad chapter does not mean the story is over.",
"Your life becomes a masterpiece when you learn to master peace.",
"Change your life today.",
"Your best teacher is your last mistake.",
"Every day is a second chance.",
"You are never too old to set another goal or to dream a new dream.",
"Happiness is not by chance but by choice.",
"Keep your face to the sunshine and you won’t see a shadow.",
"A champion is defined not by their wins but by how they can recover when they fall.",
"How we live our life is far more important than how we say we live our life.",
"Knowledge is like underwear, important to have, but not necessary to show off.",
"Attitudes are contagious.",
"By all means: Do it!",
"Wherever life plants you bloom with grace.",
"I don’t need any part-time people in my life.",
"Your life does not get better by chance. It gets better by change.",
"Life goes on.",
"Only I can change my life. Only you can change yours.",
"Fair is where you get cotton candy.",
"If you dare you will win.",
"Smile big. Laugh Often. Never take life for granted.",
"The road to success is always under construction.",
"Find comfort in the chaos.",
"I’d rather be someone’s Sunday morning than their Saturday night.",
"This above all, to thine own self, be true.",
"Try to be a rainbow in someone’s cloud.",
"There’s no fun in giving up.",
"No matter what people tell you, words and ideas can change the world.",
"Life is 10% what happens to you and 90% how you react to it.",
"You miss 100% of the shots you don’t take.",
"With confidence, you have won before you have started.",
"Go confidently in the direction of your dreams and live the life you have imagined.",
"If you look at what you already have in life, you’ll always have more.",
"You are enough just as you are.",
"Always aiming to be a rainbow at the end of a thunderstorm.",
"You must do the things you think you cannot do.",
"Pursue your passion and you’ll never work a day in your life.",
"Don’t quit your daydream.",
"Life is short. Do stuff that matters.",
"No te preocupes = Don’t worry",
"Solo se vive una vez = #YOLO, you only live once",
"Vive hoy. Ayer y mañana no existen = Enjoy life today. Yesterday & Tomorrow is gone",
"Amo la fiesta = I love to party",
"Vive la vida loca = Go wild",
"Feliz como una perdiz = happy as a partridge",
"Vive tus sueños = Live your dreams",
"Lo mejor está por venir = The best is yet to come",
"Pasito a pasito, suave suavecito = Step by step, softly softly",
  "Leaving a bit of sparkle everywhere I go ✨",
  "I believe in making the impossible possible because there’s no fun in giving up",
  "Turned my dreams into my vision and my vision into my reality",
  "Smart. Strong. Silly. Straight up class act.",
  "I’m not perfect, but stories are always better with a touch of imperfection",
  "My standards are high… just like my heels",
  "Me: Happy girls are the prettiest. Also me: I’d like to buy 15 pounds of makeup, please.",
  "Who runs the world? ME.",
  "Happiness never goes out of style",
  "I’m a woman with ambition and a heart of gold",
  "I shine from within so no one can dim my light",
  "Non-binary biased bitch",
  "Músico",
  "Ababol o esas palabras de culto nacional",
  "Laputalesbianaesa",
  "Ex-Retrasada",
  "Ex-Amante",
  "Ex-Puritana",
  "Ex-Puta",
  "No soy perra",
  "soy amante en serie.",
  "Be classy🔥",
  "If Nigeria Happen to you, you will understand that you need APC/PDP out.",
  "My habits make me special",
  "NFT lover - Collabs projects - Community builder - GameFi",
  "Co-Founder of@TwinBirchUSA(coming soon)","My tweets aren't financial/investment advice",
  "Co-host@OfficialXPod.",
  "BREAKING news.$TSLAinvestor/fan.",
  "Muchas gracias afición,esto es para vos otros,siuuuuuu",
  "Me gusta tocar la guitarra sin albur",
  "Follow Me I Will Follow You Follow me i follow you Follow me i follow u❤️",
  "I’m predicting that Bitcoin will reach $69420 and $80085 first before reaching $100k!",
  "Btech -Cse undergrad",
  "Im luving n caring",
  "I breathe for a living 26",
  "It's not how much you buy a#doken, but how hard you hold it.🔥",
  "#pheleecx.,..cruise#😉😎🌚",
  "Deputy Relationship Manager - American Express",
  "Fun and loud",
  "Common man",
  "My name is lalleiba oinam Im from Manipur hahaha",
  "Playing drums, shotgun operator",
  "Ya Özgür bi yaşam,Ya’da Görkemli bir Direniş.",
  "Hello world, I'm an Egyptian citizen.",
  "Legal and political activities",
  "do not judge me before u know me, but just to inform u, you won’t like me😇A human. Being.",
  "Una cosa de locos🫧",
  "Fun loving positive person",
  "Simply Confident, Avid Arsenal Fan.🎾NADAL and🏀Steph Stan, Hustle Hard, Chill Softly. God's gat me🙏",
  "Hard work then achievement",
  "local optimal",
  "electric cars, giant batteries and solar",
  "Just a programmer.",
  "Save our planet",
  "Stand up comic/mixed martial arts fanatic/psychedelic adventurer Host of The Joe Rogan Experience#FreakParty JOEROGAN",
  "- Sometimes Life Ain't Hard Ya Just Need To Understand That's It's A Mystery Full Of Wonders",
  "CA still studying , movies and web series person and politics etc",
  "Akdeniz Üniversitesi",
  "#Sufi,#Sindhi",
  "Every day, just spend a little time on diet and take weight loss pills, you can keep yourself a slim figure like many women dream.",
  "CEO@binance, holder of",
  "Follow for,,$BTC🤩",
  "Digital Creator | Amazon Affiliate | Influencer | YouTuber",
  "Fanatico del Rock",
  "#1 Kanye Fan",
  "Sick to death of Net Zero, the British Government, Illogical Covid rules and the poor quality and low level thinking of most of our MPs.",
  "Good luck!",
  "Entrepreneur",
  "PIzza Time.🇺🇦❤️",
  "All Jokes Sports Governments & Politics And Simple Me",
  "You absolute fucking legend I love you bro, Rest in peace Alexander Technoblade. Fuck cancer",
  "StevenCrowderand Apple Podcast. Join#MugCluband follow on Instagram: @ louderwithcrowder | Truth Social: @ StevenCrowder",
  "Sad birds still fly.",
  "Born in Ogobiri, sagbama LGA of Bayelsa state",
  "work hard ,work play",
  "Çi kesê ku ruhê netewayetî pê re tune be, wê rojekê îxanetê li milletê xwe bike.",
  "Simpatico y alegre",
  "#DCsteady chasing bags and nfts of course@primatesnftHOLDER Hardcore#DegenNFT Enthusiast and Collector#DOTHEWORK",
  "SpaceX designs, manufactures and launches the world’s most advanced rockets and spacecraft",
  "90% with psychology°",
  "Sport",
  "Just a Simple Guy with BIG DREAMS!",
  "tell me i cant and i'll embarrass you",
  "#Crazybharbie💘❤️",
  "Introduce Chinese tea",
  "Top Crypto YouTuber! Final Stand is my channel.❤️#Dogecoin❤️Subscribe/Follow & turn the#notificationson for BIG Real Time Updates!🔻Crypto picks club🔻:)",
  "Any one can tag me no problem😇Im an airdrop worker😙Follow me for follow back",
  "Patience is power💥",
  "Just finished +2 exam likes dhoni|CR7|buttler|emma watson|suriya|williamson| like virat kohli but not his toxic rcb gang science lover❤️❤️#arrestnupursharma",
  "Anime, Nasa, Música .-. Weno no se que poner aquí ala v .___.",
  "Unity- United as one, one race, one color. BLACK MATTERS #53-Salute🌳#53-Nation🍁#53-Built🍀",
  "BASKETBALL #5 COLOMBIA",
  "visione politica",
  "Pk, Phi.1:21💛Family and friends mean everything to me💛",
  "Mẹ lỡ nặng lời, lỡ nặng lời làm con thấy chơi vơi.",
  "Life is strange but death sucks😞",
  "Official account of Transparent training bra. Get the best transparent training bra is here in affordable price. Visit official website and check now.",
  "Artist",
  "Catch me cloud surfin with your land dolphins",
  "Dietician- Nutritionist (RD)",
  "Chlamydea speedrunner",
  "On a mission to eliminate KBA through Contactless technologies led by#VoiceBiometrics",
  "She is Reptilian.",
  "Living past a $",
  "Managing Partner, The Future Fund LLC, SEC registered investment adviser.",
  "Fight for peace",
  "Fx trader📉📈First do ,then talk",
  "Je ne suis pas homophobe💀🔫",
  "it's all for good cause🙇just a dollar for you, it's a fortune for them please donate",
  "I was born in Kharkov",
  "I am a people’s person👍",
  "top 0.09 click to see why",
  "Former dentist. Book worm",
  "Im a student .my hoby a phtographar .",
  "Dad & financial analyst.",
  "#localforvocal#corruptionfreemumbai#liveindia",
  "Мужчина в самом рассвете сил!",
  "Positive vibes only..",
  "attitude haters🤪",
  "#tourism#cooking#fitness#knowledge",
  "Medico🙂|GMCB 24'| Anime💝",
  "hello friends chai pi lo",
  "Test Engineer",
  "Shytoshi Kusama™ of Shiba Inu decentralized community and Shiba Inu Games.",
  "DYOR NFA. BEWARE, SCAMMER copycats that have less than 800k! followers.",
  "Professional rocket orientation specialist.", 
  "chasing rockets and capturing photons.",
  "Bringing space down to Earth for everyday people🚀",
  "Nutricionista",
  "Financial markets expert",
  "Attention creates impact",
  " .ph.D in Business Administration",
  "i live anime",
  "Co-Founder, Co-CEO, and lowercase god-king of@realDailyWireand@JeremysRazors.",
  "Pronouns: You can call me Al.",
  "I am a proud Trump Patriot",
  "I don't have something called bio",
  "I do guitar things",
  "Creator of Dogecoin| My NFT | Probably shouldn’t take me seriously, I am a dumb",
  "Since 2004",
  "30 I g I ♧ ☆ •○●°¤□",
  "share knowledge",
  "Minded business",
  "Be kind, honest and respectful to everyone.",
  "I'm a guy with ZORO worry",
  "Thanks for following and support wrestler. God bless you all🙏",
  "I really enjoy singing, it's entirely different to acting because I'm just being myself..!!",
  "'We are all in the gutter, but some of us are looking at the stars' - Oscar Wilde",
  "Typical Leo",
  "Born in 1981.Physicist, photographer, graphic designer...",
  "My life my goals me making my life",
  "1st software platform that automates Audio-Visual project design & documentation#avtweeps#infocom2022",
  "A passionate full stack developer.",
  "I adore singer Cam Ly",
  "There are three kinds of lies: lies, damned lies, and statistics.",
  "Starting fresh✨",
  "mamba mentality",
  "Capricorn",
  "Idk add me on oculus kprince4life",
  "Ing. Civil || UCAP",
  "4 hit shows; 5 NYTs bestsellers & also ridiculously good looking. Watch Gutfeld!",
  "Mi educación",
  "I love my Hindu",
  "Good hearted",
  "Imma degenerate",
  "Nothing spesial",
  "Social media assistant. Social media marketing.",
  "Deflationary meme of BSC hold, pet, love, & help save dogs!👀",
  "Hardwork and trust",
  "Bodybuilder Engieer",
  "Student, avid cricketer and enjoy playing chess, football, tennis and badminton",
  "Not seen since July 2021!",
  "☯️🌫️⚔️🛡️👑NTGNEVERDIES👑🛡️⚔️🌫️☯️",
  "Para el que se pregunte por qué no tengo twits: no me interesa compartir mi vida con quien no conozco. Solo disfruto del contenido de twitter y de quienes sigo.",
  "Never surrender",
  "Leading UK consultancy specialising in business performance management solutions for#CFO#Financedirectorswith@workday#ibmplanninganalytics📞01565 831900",
  "Love you#Krew💚she/her♡",
  "Business oriented",
  "I’m down to earth and loving",
  "Just don't give a fuck!",
  "fighting to create equitable markets for all",
  "We are on a mission to improve mental health and wellbeing in the LGBTQ+ community by providing research, training and support.",
  "Não sou bom com nada mais si precisar eu ajudo",
  "girl at@realdailywire⚡️host of The Comments Section⚡️opinions are my own⚡️",
  "I love to walk like me..💛And I love my loved ones very much💖✨And like to travel🌏🌻",
  "Enjoy life. Ignore negativity and embrace changes.",
  "Hi! I am Vietnamese🇻🇳. I am a female gamer of the game Arena Of Valor and I am also an artist. I am the admin of the K.Emon page on facebook.Nice to meet you✨",
  "Bitcoin is an open source censorship-resistant peer-to-peer immutable network. Trackable digital gold. Don't trust; verify. Not your keys; not your coins.",
  "Nfts hodler",
  "Am a simple lady that loves to be treated the way I treat others",
  "🇬🇧🇺🇸Memes🤪&🐶#Aspielike@ElonMusk#anxietyDMs open for banter/chat🤪No bitcoin/scams for my💰#ASD#Aspergers#OCD#COYSPro🇺🇸Pro Military#YIDS",
  "Knıtted Fabric",
  "Good for F",
  "OT9EXO-L, Shawol, Once, IGot7 OT8Stay OT9S💜ne Neverland MY MOA NCTzen Reveluv Engene Nswer Wonderful Elf Me+U Midzy Forever Carat Blink",
  "i don't know how to write",
  "No competition in Destiny",
  "Future Fashion",
  "and miles to go before i sleep",
  "🇱🇷🇺🇸Beautiful😍| Fitness | Gym | Music |",
  "Love u bebe:bapu",
  "Chaitanya varangaonkar",
  "ROEVSWADE#EVILSOCIETY😈DOWN W FASCIST CHRISTIAN ASSHOLE GOVERNMENT! AND ALL EVIL IN THIS🌍DAY OF Reckoning HAS ARRIVED!🙏THE HEART OF FAIRY🧚‍♂️",
  "Chartered Accountant",
  "I love india🖤🖤",
  "“A King only bows down to his Queen”..",
  "I'm😈😈rajput👿😈boy",
  "nationalist,",
  "Lover family",
  "Photographer🇮🇳",
  "Health department",
  "Science project, science experiments, project videos upload YouTube",
  "Sameer m deshmukh",
  "Bhamare Akshay shantaram",
  "I am Student",
  "production engineer in oppo mobile india pvt ltd",
  "I am professor.",
  "Everyday New Life, Everyday New Journey",
  "Nimikha lover",
  "I am hrishikesh nath s/o- Lt. atul ch. nath. i am a social warkar and i exeucative member of maddhya karbi anglong gou seba samitee. state assam",
  "I LIKE HINDU",
  "Executive for an e-Governance.",
  "Jaspal Singh village jharmajri post office Barotiwala tehsil Baddi district solan Himachal Pradesh",
  "“We don't design clothes. We design dreams.",
  "Twitter account o Shri Yogi Adityanath Ji personal website & office",
  "Khawaja Gareeb Nawaz.......",
  "Jai pasuram",
  "Be human. It’s important to make sure whatever you write........ displays🙂",
  "External Affairs Minister of India. Member of Parliament (Rajya Sabha) from Gujarat State.",
  "🙏Jai Shree Ram🙏⚔️Jai Rajputana⚔️",
  "Fight For Truth....🙏🙏socialist, secular, activist, humanist..",
  "I'm a Good girl✌🏻because I believe in love❤️Integrity and Respect✨Mahadev❤️🌍",
  "🖥️🖱️Shinde Computer Typing And Xerox🖥️🖱️",
  "जय हिन्द वन्दे मातरम् जय श्री राम🙏🚩🚩",
  "I love hardwork",
  "Horticulture Landscape garden specialist and farmhouse development with maintenance",
  "#instagramid_sanketwaghmarek",
  "IF YOU BORN IN POOR IT'S NOT YOUR MISTAKE BUT IF YOU CAN DIE IN POOR IT'S YOUR MISTAKE",
  "Love zindagi",
  "I am ABINASH SARMA",
  "Ajeeb ladki",
  "Entrepreneur",
  "I support nupur sharma",
  "Incorporated In 2007, Linux Laboratories is an emerging global pharmaceutical company based at Chennai, India.",
  "यतो धर्मः ततो जयः।",
  "Gyne Oncologist, nutritionist, integrative medicine expert, follower of Sadguru",
  "Being chased by the devil can be angelic.",
  "I'm All time happy😊",
  "Physionix HealthCare Clinic is a Multispeciality clinic located in Delhi which hosts some of the best doctors and healthcare professionals in Delhi. It provides",
  "I am affiliate marketing amazon and all service providers and services products all India services products Digital marketing services products services COD",
  "createar .. Kisan",
  "I'm Hindu I'm student Barth:August 18,2004",
  "Student by profession, reader by passion",
  "Akash kashiram govare( kashya) X ray technician in meditech hospital mira road, cathlab technician Kabaddi district and state level refri",
  "हिंदुत्व मेरी जान है और भारत मेरा देश है , जियेंगे हिंदुत्व के लिए",
  "I am a soicial worker. I allways help to people.",
  "Love💕family activities water spots",
  "Krishan rodha",
  "Just a simple man",
  "Blessed Soul",
  "Yet to make an impact..",
  "Proud to be Santali❤️❤️",
  "Jayashree Shrigire",
  "Self respect",
  "Ajab Gajab Duniya provides the latest news from India and around the world in Technology, Business, Sports, Lifestyle, Health & Fitness and much more.",
  "Gujarat police👮",
  "Tera vaibhav amar rahe maa hum din 4 rahe ya na rahe🇮🇳",
  "Cake🎂🎂🎁🍰muder hindiday September",
  "Always positive",
  "I'm electrician",
  "Chase your dreams, but always know the road that will lead you home again...",
  "Shubham jumde",
  "Life is beautiful",
  "I'm just a mere spectator",
  "Jyoti uikey",
  "Am fun loving and adventurous person loves to enjoy nature.",
  "Environmental Photographer",
  "I like holidays",
  "Wish me on 1Dec Dream doctor Pcmb student",
  "ॐ नमो नारायण🌹🚩🙏",
  "Video comedy DA song",
  "जनसेवा हीच ईश्वर सेवा",
  "Those who know me dont need it those who dont know dont require",
  "जय श्री राम🚩जय राजपूताना⚔️",
  "VERY UNIQUE",
  "Hindu College,DU, Economics Graduate'19. observations|Humour|Sarcasm| Economics.",
  "Our Culture Is Agriculture...",
  "Govind Choudhary First cry on 16 Sep 2007😊☺मैथिल bøy😈💪Call me ब्राह्मण बाबु🙋🙌",
  "i dont know",
  "My Love is Allah",
  "मला बाबासाहेबांच्या उपकाराची ‘‘जान आहे म्हणुनच मी श्रद्धेय बाळासाहेबांचा ( फॅन ) आहे",
  "मराठी माणूस🚩",
  "Don't underestimate the power of common man",
  "Not me, But you.",
  "निमित जायसवाल (पत्रकार) क्षेत्रीय सह मीडिया प्रभारी, भाजपा पश्चिम क्षेत्र, उप्र",
  "Computer science engineer👨‍🔧(cse)",
  "Vishal sulane",
  "आम आदमी हु मै",
  "Tanisha♥️ROCKY",
  "insta id - tanmaysingh9926",
  "I support nationalisam",
  "Nathing is impossible life",
  "भरोसा और आशीर्वाद कभी दिखाई नही देते हैं. लेकिन असंभव को संभव बनाने की क्षमता रखते हैं.",
  "#MahiMar Raha Hai#Csk#Indiawon T20 world cup 2022.#India",
  "I am a teacher ......",
  "Chess master",
  "Medico🥼🩺Intention Is Nothing Without Action But Action Is Nothing Without Intention💯✌️",
  "Doesn't Matter What People Think About You If You Are Right Then The World Is Right",
  "Islam zandabad",
  "I am a social worker .",
  "You are bro",
  "Motoring Journalist / Transportation Designer",
  "तू हज़ार बार भी रूठे तो मना लूँगा तुझे मगर देख मोहब्बत में शामिल कोई दूसरा ना हो",
  "satyam mishra",
  "Makeup artist",
  "Always out of the box🚀",
  "Hii my all friends this is my channel link please help subscribe it",
  "everybody Follow government rules",
  "Social worker",
  "सत्यमेव जयते",
  "Naveen Dudi i am student",
  "I like politics very much",
  "Rohit kashyap I am attude boy",
  "Swapnil Masne{ Oracle DBA}",
  "Maintenance department I like it",
  "I am youtube video creater I am many many xml girls video please support my youtube videos .",
  "I'm next capture see",
  "An army aspirent",
  "CA ASPIRANT♡",
  "Bsc agriculture student",
  "I love crypto",
  "Ph.D in Pharmacology from Mumbai University.",
  "Pharmacologist",
  " toxicologist and clinical research consultant.",
  "Never Stop Learning, Because Life Never Stop Teaching",
  "BGMI gamer or wot..",
  "Nothing....",
  "Jai Mahakal Bharat Mata Jai🇮🇳",
  "Black day dill Mangea more",
  "I,am a yoga instructor",
  "Love yourself",
  "Student. | Seeking for betterment.",
  "Student ...",
  "Union Home Minister, Minister of Cooperation and MP, Gandhinagar Lok Sabha.",
  "Everyone is special",
  "C k banna vagad",
  "Jai Shree Ram🙏🙏",
  "Waheguru ji🙏🏻🙏🏻",
  "Simple living & high thinking✨",
  "Åñïl rock🌟Flipper🤸Dance lover🕺Dhf@viratKohli",
  "As a self employed at lic india also I have worked abssl ltd",
  "Fight for your dreams and your dreams will fight for you",
  "NEVER SETTLE",
  "Imstampvendor",
  "Nirmal Kumar Parmar PET DAV PUBLIC SCHOOL HAVELI KHARAGPUR",
  "💖༒︎.❁.Mᵒh̆̈ꪖn̥ͦ.❁.༒︎➪💖",
  "progenbiolabs for reliable medical diagnostics",
  "My Name Jitendra Kumar hailing from deviganj narpatganj araria Bihar education iam doing Bsc form Forbesganj college Forbesganj",
  "NSS PROGRAMME, NSS VOLUNTEER",
  "धिरज राजेघाटगे जिंदगी ' तेरी है और तू अकेला ... जीत पक्की है ..... सातारकर",
  "Kabir is god",
  "😎My life,My🤞rules that's My attitude😈*Ganeshsoni * Life on earth is expensive, but it includes a free trip around the sun...!!",
  "I’m not always sarcastic. Sometimes, I’m sleeping Intern@CollegeTips_in",
  "My name is Rubal Thakur .I am a student . I am 15 year old . I am student of+1 class .",
  "find me😎where dreams are lost in reality.",
  "Knowing new things around the world. Wanna stay connected with current affairs.",
  "Greatness from small beginnings.",
  "Welcome to the content of my head.",
  "Manik singh",
  "Bhartiya Janata party ( Mondal vice president - pandabeswar )",
  "Simpl life style",
  "Mankant Chaubhary",
  "💙》Royal Entry↪️20 june🎂🗡️༒◥█◣V.I.P Account◢█◤༒😎SînGle👉Wish Me 20 june🎂🤓Simple Boy🏍📸hØlîC💥I’m not Rich but I’m Royal👑👍Friends😍lOveR🚬",
  "I come with an instruction manual. Handle with care.....",
  "Say no to tobacco🤐Stay healthy💪",
  "I love you ma❤️😊",
  "क्षत्रिय कुलावतंस सिंहासनाधीश्वर महाराजाधिराज योगिराज श्रीमंत श्री छत्रपती शिवाजी महाराज की जय",
  "Santosh patil.",
  "A Researcher by nature, a Philanthropist by intent and a Trainer by profession!",
  "My love you appa",
  "Trader for life",
  "My Right my power",
  "Dinesh bade patil",
  "Prem pal Singh chaudhary",
  "💖Panda Doodle is a collection of 10000 unique Pandadles that exist on the Polygon Sidechain (no gas fees when buying or selling a Panda Doodles!)💖",
  "Advocate Liver Donor",
  "I am a teacher cum house maker",
  "I m 29 yr gujju boy looking for paid fun",
  "youtube vloger",
  "Madeshwaran and MOHANESHWAR",
  "निस्वार्थ सेवा",
  "I am very good HVAC ENGINEENNR & Stock market Tredar. Stock market call providar",
  "Smart workers",
  "Pharmacist..❣️",
  "• 𝙼𝚛.𝙳𝚑𝚊𝚒𝚛𝚢𝚜𝚑𝚒𝚕 . 𝙼. 𝙿𝚛𝚊𝚍𝚑𝚊𝚗 • ʙᴜsɪɴᴇssᴍᴀɴ😎📍ᴊɪᴠᴀɴᴅᴀɴ ᴛʀᴜsᴛ ᴋᴏʟʜᴀᴘᴜʀ🤝📍ᴊɪᴠᴀɴᴅᴀɴ ɪɴsᴛɪᴛᴜᴛᴇ ᴋᴏʟʜᴀᴘᴜʀ🏢",
  "Always Smile😊",
  "Gshfhfdgcbj",
  "Being real make me more speacial",
  "Giving India a Cyber Security Blanket",
  "🤗🤗Deep voice and messy hair. Also, tall and cute.🤗🤗",
  "Always support to right one",
  "TaraChanD Bogia@sanskritवसुधैव कुटुंबकम्🙏",
  "Mujhe modi se Melanie ha",
  "जय श्री राम🚩🙏",
  "Government employees",
  "It all depends on your mindset👐👐Be strong Fitness freak💪🏻💪🏻💪🏻",
  "Always smile",
  "dharmray62@",
  "Social sevice and harmoney",
  "pimpalgaon baswant",
  "Chartered accountant",
  "I am a social media influencer",
  "its not for everyone",
  "Karma Believer",
  "Vegan, spiritual",
  "Hatters makes me famous",
  "I am a sabatani",
  "Student of Allahabad university🤗",
  "I am a teacher and post office agent",
  "Hi hello everyone",
  "Business Man",
  "Football Analysis Memes Reviews",
  "This is my youtube channel link share and subscribe plz🙏🙏🙏🙏",
  "Minsarul sk",
  "I don't react..But trust me..I notice everything...",
  "Abuzaid Ansari Azamgarh Uttar Pradesh India",
  "𝙷𝚒 𝚏𝚛𝚒𝚎𝚗𝚍𝚜 𝚖𝚒 𝚜𝚊𝚞𝚛𝚊𝚋𝚑 𝚐𝚊𝚒𝚔𝚠𝚊𝚍",
  "𝙉𝙚𝙫𝙚𝙧 𝙜𝙞𝙫𝙚 𝙪𝙥 !",
  "Life is very short nanba",
  "Belive in karma😌",
  "Mahender sangat",
  "Funny mind always cool day",
  "खुद से नहीं हारे तो आपकी जीत सुनिश्चित हैं.",
  "I am studeant",
  "उगाओ पकाओ खिलाओ",
  "Software Tester, Trekker, Blogger, मराठी ब्लॉगर,Marathi blogger",
  "My name is Devendra and l am a fitness boy so hardwork out and gym motivation trainer.",
  "#selfobsessed..❤️🦋♡Hodophile|| Bibliophile  . मंज़िल के मिलने पर ठहर जाती है ज़िंदगी, मज़ा तो राहों के संग चलने में है।।⭐💫",
  "Patience is power💥",
  "Officeal account👍",
  "BJP Karkarta",
  "Member of BJP",
  "Tweets about Cybersecurity, Malware, Hacking, Programming, and Infosec. Contact: infosec@ethanabraham.com",
  "I am a gvot emp",
  "Just flow with life",
  "Love music🎼Addicted to art🎨🖌️",
  "Student /Baba hospital",
  "Ca final - student Dreamer",
  "I will earn money",
  "I’m not always sarcastic",
  "My name is lalleiba oinam Im from Manipur hahaha",
  "I don't love to talk that much",
  "Still learning",
  "894*5*^**^^^",
  "꧁👑I AM THE KING👑꧂♥️ONLY FOR MY QUEEN♥️༺∆Mahakal Ka Ladla∆༻😍Naa जीने की खुशी ☠️Naa मौत का गम Jab तक है दम 🕉️Mahakal के भक्त रहेंगे हम🕉️",
  "Vishal Rajbhar",
  "I A STUDENT BIHAR",
  "I m student",
  "ITS ME..👿MAHH SELF...🙌AND I...😎",
  "Making fun.... Not much know about twitter🐦🐦",
  "Software developer Gamer",
  "Good though",
  "My life,,,my rules,, that's my attitude.",
  "I am coming to twitter so late, this makes me special",
  "Krushna chavan",
  "Main Rajpal Singh Nagar Panchayat mewada Agra jaspur dhan Singh Nagar Uttrakhand 244712",
  "do not judge me before u know me, but just to inform u, you won’t like me😇A human. Being.",
  "Whenever is rightness there is victory",
  "Amol Jadhao",
  "Allahabad university student",
  "₹3000 पेंशन पाने के लिए प्रधान मंत्री श्रम योगी मानधन योजना से जुड़ें- सीएससी से सम्पर्क करें (ई-श्रम)",
  "NSS team SKV Rajouri Garden Extn school I'd 1515021",
  "I'm students of pharmacy",
  "my dream IAS is my hobby",
  "Shyam singh Rathore",
  "Prem👑27/11🎂",
  "NEED A SECOND CHANCE...😳DESPERATELY!?",
  "Life stayle",
  "MY LIFE MY RULES NØT YØUR BUSINESS",
  "Vantalakka Mogudu",
  "Child Psychologist Public Speaker School Counselor RCI registered Rehabilitation Psychologist",
  "I love India",
  "Mayursinh chudasama",
  "A neet spirant Sports lover & ABD fan❤️❤️",
  "I am a bisexual",
  "Simplicity and genuinity",
  "पंकज तलावलिय",
  "Bike rider and😎",
  "asdasdas dasfsdf sdaf asd",
  "Be flirty addicted🚗Happy Soul🖤....",
  "I❤️ISLAM... Alhamdulillah😊",
  "Saffron warrior",
  "📚کوئی رفیق نہیں ہے کتاب سے بڑھ کر.📚📚No friends better than the book📚",
  "🙏🏻*स्वर्गात पण जे सुख मिळणार नाही* *ते तुझ्या👣चरणाशी आहे....* *कितीही मोठी समस्या असुदे😍आई नावातच समाधान आहे.....🙏🏻😊😇",
  "Keep calm and be positive",
  "मोबाइल 8510015031",
  "I am walking on the never-ending path of success.",
  "Understand me or Forget me....",
  "I’m good boy",
  "The LallanPost News - Hindi News Channel",
  "My dream is to",
  "Sanghan ktl",
  "medical student",
  "Weight lose now ask me how cnt this whtspp no. 7015532428",
  "Hamri Instagram kii Id shi nhi chal Rahi",
  "Think Big, Think High, Think Positive",
  "Duplicate shares/Transmission Procedure/IEPF share procedure",
  "Love the life you live live the life you love",
  "I have seen my limits",
  "Every second enjoy",
  "Indian public",
  "Set your destiny",
  "Share market resarch",
  "Being normal is new special",
  "I am very hard person",
  "ಹಾವೇರಿ ಜಿಲ್ಲೆ ಹಾವೇರಿ ತಾಲೂಕು, ಹಾವನೂರು",
  "Love myself...❤️❤️❤️",
  "My name pranshu",
  "Mahendra Nimse",
  "Come meteor.. TAKE ME",
  "I am manoj Kushwaha I resident of mp in bina sagar I graduated of maharaja chatrasal chattarpur University",
  "I am indian",
  "Contribute towards environmental protection , youth empowerment and health",
  "Politicion प्रेसिडेंट भारतीय जनता सेक्युलर पार्टी नई दिल्ली",
  "Mukesh kumar dhal Army brat Fearless",
  "Om namah shivay❣️",
  "Sports Entertainment Music Bollywood and Celebrities",
  "🙏Jai Gurudev🙏",
  "AajTak covers breaking news, latest news in politics, sports, business & cinema. Follow us & stay ahead! Download the App:",
  "Md janisar akhtar",
  "तुम्ही किती जगलात ह्यापेक्षा कसं जगलात याला जास्त महत्त्व आहे.",
  "I am the student",
  "All Time Happy",
  "Karna kumar",
  "Hello I am a youtuber My youtube channel name aniket Chauhan Haryanvi",
  "Kushal medhi morigaon gashbari assam",
  "graphic designer",
  "Animal and Nature Lover",
  "◆━━━━━━━▣✦▣━━━━━━━━◆#दिखावा_नही_किया_कभी_हमने,❤️😙#बस_दिल_से_चाहा_है_अपने_चाहने_वालो_को◆━━━━━━━▣✦▣━━━━━━━━◆🔥Jai hind🇮🇳",
  "Optimistic, and ambivert",
  "Mai khud se hi Aanjan noon",
  "I am Sanjit Prasad Verma",
  "Free Fire My love you so",
  "Sanjay Sharma",
  "India अखंड भारत",
  "Mr. Shivaji Thete",
  "THE CONSTRUCTIONS बांधकाम ठेकेदार ,राहुरी",
  "रक्षा मंत्री, Defence Minister of India",
  "In a world of worriers, be a warrior",
  "😎...எண்ணம் போல் வாழ்க்கை..💯",
  "The Godfather",
  "Simplicity is the best policy❤️",
  "प्रतिपच्चंद्रलेखेव वर्धिष्णुर्विश्ववन्दिता ।। शाहसूनोः शिवस्यैषा मुद्रा भद्राय राजते ।। !! जय महाराष्ट्र !! जय शिवराय !!",
  "Shubham Gangurde",
  "I am searching for good people Not a attitude people",
  "Deepak Kumar village mangurahi ps mahua vaishali bihar pin cod 844122",
  "माणूस तोंडाने कडवा असावा....🚩पण तो गोडबोल्या भडवा नसावा...🙏",
  "CG life....",
  "Naye Rahi is a community of such people who have courage to make their own path by their Art & Talents.✌It is a platform to all kinds of talents.",
  "•|mechanical engineer •|Believe in yourself😎•|Photography📸",
  "Mr Shankar dhone patil",
  "Happy or sad",
  "Iam also happy",
  "Army lover🇮🇳🎖️",
  "Mr. Vijay Surya",
  "Live your life live your dream👊",
  "Medico @ GMC guntur",
  "मारुत सुत मैं कपि हनुमाना🙏🏻",
  "I love you❤️",
  "Raju Mobile gaming anupama",
  "DrEaM mErChAnt.....",
  "Developing people bringing smiles😊",
  "Niraj Kumar",
  "I'm a student",
  "Name is enough🔥✌🏻",
  "My self sidhesh swain. Son of kalndi swain. My village name is badalapandua sahi",
  "#Queen's entry on 10th April..😎#Medico..doctor🩺💉#bestie_Mubeena..",
  "I am friendly",
  "standing in front of evil yo",
  "NDA aspirant🇮🇳सेवा परमो धर्म:🇮🇳",
  "हमारे ट्विटर में आपका स्वागत है",
  "Learner , love for environment ,thinker Hunger to succeed",
  "CLAT ASPIRANT FUTURE LAWYER",
  "i love twitter",
  "#ram❤️#kattarhindu❤️🚩शुभ परिवर्तन करने को अब❤️हम ऐसा संकल्प करे❤️अखंड भारत का वह सपना❤️सब मिलकर साकार करे🚩",
  "Think Like A Monk",
  "I am a youtuber",
  "ST. XAVIER'S HIGH SCHOOL KONARK",
  "Painting artist",
  "Graphic Designer",
  "Sandeep Kumar age15",
  "Be you, the world will adjust.",
  "Middle bencher",
  "#गुलामेंसंकटमोचन#",
  "Allah is Almighty❤️",
  "Would Be Medical Technologist❤",
  "change your thoughts and you change your destiny!",
  "Undergraduate with working professional for 6 years.",
  "Rohit patel",
  "Got that drip!",
  "I'm students.",
  "Venkatean.dhananal.purachithalaivi.amma avargalin unmai thondan",
  "Digital Growth Consultant & Founder of Digital Dominators Hub ",
  " Tweeting about#marketing,#ads,#funnels,#growth,#bootstrappingand some other stuff😃",
  "Manindra Shankar Mishra",
  "Waheguru Ji",
  "Nothing my bio yet",
  "I'm VijayRao Shitole..",
  "Official Twitter account of the Bharatiya Janata Party (BJP), world's largest political party. भारतीय जनता पार्टी (भाजपा)",
  "14🥂📍Don Bosco - Astrophile",
  "Govt.boys Has Para सहायक शिक्षक",
  "Pradeep Kumar",
  "Music lover💫Being cute,not fake🙈",
  "#neetaspirant..",
  "BSC STUDENT",
  "Praveen devpura",
  "Observable Universe Explorer🔭🌌",
  "Name.pradeep Kumar study.farmacy At job.Ambrin hospital Address",
  "Student life is beautiful like.",
  "WHYNOTBHIMAVARAM",
  "# Entrepreneur...#BusinessCoach...#PublicSpeaker...",
  "I Am A Constructive Person",
  "Doing Business in Readymades garments & Seasonal items",
  "Bihar Board Maths is a Complete Professional Channel of Mathematics of Class 11th & 12th",
  "landed on may 26, Doing what we think is not freedom it's a privelage",
  "📮to young entrepreneur..Doing business of 21century.💫",
  "market is the",
  "𝕴 𝖆𝖒 𝖈𝖔𝖑𝖑𝖊𝖌𝖊 𝖇𝖔𝖞 𝖆𝖓𝖉 𝕸𝖞 𝖇𝖊𝖚𝖘𝖘𝖓𝖊𝖘𝖍 𝖎𝖘 𝖈𝖆𝖙𝖊𝖗𝖎𝖓𝖌",
  "Advocate at district and session court Meerut",
  "Mahi😌Creating my own sunshine.,😌",
  "सत्य मेव जयते",
  "Curious & Dreamy🐦😍",
  "Video creator",
  "उत्तर प्रदेश गोरखपुर",
  "My self vishal I m a youtuber My channel link given below",
  "Nation first🇮🇳Hindu🚩Mom Dad love😘❤️",
  "Customer service",
  "Retired govt officer",
  "iam digital marketer",
  "Jay shitla maa",
  "वक्त बदलता नही बदलना पड़ता है ।",
  "I am student. my name is krishna sah baniya",
  "I Am Simple boy",
  "Qureshi boy‼️‼️",
  "Mr. Yorum Nyamdek Taigh",
  "मेरा सपना मेरा संकल्प मरते दम तक अखिलेश भैया के संग जय अखिलेश जय समाजवाद❤️💚🇧🇫🔥💪🏼🇧🇫",
  "As long as they get rich",
  "Photographer",
  "Waheguru maher kere",
  "Businessman",
  "राहुल फ्लावर्स नागपूर..7066050788",
  "Islampur Bihar",
  "I love my mom",
  "Photographer😇❤️😇",
  "A simple man",
  "Ever tried ever failed try again fail again fails better. treat everyone kindly",
  "Here to make myself successful",
  "I am Advertisor, All Best company Product Review",
  "college student",
  "Student! Foodie!",
  "Mourya wanshi ..... Attitude high level😏😏",
  "Tamilan chicken🐔",
  "I work with efficiency",
  "Always Happy",
  "Cricket lover",
  "My love and affection to everyone",
  "Singing, playing keebord and preaching the gospel",
  "Hospital management director and owner tapasvi hospital",
  "Jay vishwakrma",
  "Tekula rajeshtekula65@gmail.com",
  "Sat Nam saheb",
  "Kalaiyin kathalan",
  "Crypto lover",
  "I løvë😘my fãmily..💕",
  "Nothing new",
  "𝐘𝐞 𝐚𝐚𝐩𝐧𝐚 𝗼𝐟𝐟𝐢𝐜𝐢𝐚𝐥 𝐡𝐞😎▪️𝐅𝐚𝐬𝐡𝐢𝐨𝐧 𝐈𝐧𝐟𝐥𝐮𝐞𝐧𝐜𝐞𝐫 /𝐋𝐢𝐟𝐞𝐬𝐭𝐲𝐥𝐞✨▪️𝐈'𝐦 𝐌𝐚𝐤𝐢𝐧𝐠 𝐌𝐲 𝐖𝐨𝐫𝐥𝐝🌍",
  "I am the fucker ur fucked",
  "I got lost on the path of life.",
  "I am bgmi player",
  "I am retired Manager (HRA)",
  "Sportsman Athletics",
  "Passionate about movies and food",
  "Software Engineer from India | Exploring Business",
  "अन्नदाता सुखी भव..!",
  "Hmmmm.......ya I got nothing",
  "I am unique boy",
  "Fun makes to our happy with a precious family...✨",
  "Mukeshkumar",
  "Word Patriot🇮🇳❤️",
  "Don't judge a book by it's cover.",
  "Aniket kharat Part time student 21🥂",
  "Singer Music director",
  "Satyamev jayate",
  "Dy.Commissioner Keshav Puram Zone",
  "I'm a rightness man , never give up for rightness",
  "Poet",
  "Farmer",
  "Indian “Koi Deewana Kehta Hai, Koi Pagal Samajhta Hai❤️”",
  "If you do “Hindu-Hindu” on my Timeline, you’ll get blocked🇮🇳",
  "Self employed",
  "Deepak singh vill+po =odar, p/s= Sonhan, dist= kaimur Bhabhua bihar(Patna)",
  "Jayeshmuchhadiyacheritabletrusthospital",
  "जिलाध्यक्ष - भगवती मानव कल्याण संगठन जिला सिंगरौली (म.प्र)@bmks_india",
  "I am working in Hyperverse",
  "Enjoy life to the fullest",
  "Playing with kids",
  "You are who you are! God n Goals🫧💜",
  "Skip my history",
  "एक हिन्दुस्तानी🚩🚩जय श्री राम🚩🚩",
  "babakushwah",
  "Trader, rational, scientific person",
  "Just Discovering Undiscover",
  "Jay maa bharti Jay Javan Jay kishan.",
  "Keeping a watch on everything",
  "Aku University student",
  "महाराणा प्रताप राजपूत करणे सेना जय राजपुताना",
  "Medical student BAMS",
  "You suggest me some yourself XDXD",
  "Scientist F, SERB Researcher interested in ecology and conservation",
  "Software developer",
  "Don't judge me😎I was born to be AWESOME,😍not perfect😋",
  "I am student of agriculture",
  "6352 233 149",
  "Iam passes bse",
  "Gaurav chaudhary Bihari❤️",
  "I never think what the world will think😏😇Because I don't care😊🥰No loves💔greatest Then parents love❤",
  "जय श्री राम🚩👑🙏",
  "I love traveling",
  "I am not special. I am different with cognitive set of mind.",
  "DANCE IS MY LIFE",
  "lvklmuolmnnklolžlkbbllpppč",
  "Manisha Lamsal",
  "I am a people’s person👍",
  "Change is uncomfortable but necessary♥️😌🌼",
  "As of now working on self",
  "Nothing is permanent😎",
  "College student",
  "Depende on your own talent",
  "Hemachander",
  "Geomate Coin Is A Fully Decentralized Financial Marketplace Built On Top Of The TRC20.",
  "Social work",
  "Narendra Modi Samarthak",
  "Textile maker",
  "Sports Cricketers and Commentators",
  "ना ज्यादा न कम जैसे आपकी सोच वैसे हम😏",
  "singhjagtar65565@gmail.com",
  "जिज्ञासु नेचर",
  "Mahakal ka🙏🙏Diwane",
  "Bsc final +MA sociology",
  "It's information make special",
  "ARAVIND KUMAR",
  "Nothing Much",
  "ᴵ ᵈᵒⁿ'ᵗ ᶜᵃʳᵉ ᵃᵇᵒᵘᵗ ᵃⁿʸᵗʰⁱⁿᵍ ᵃⁿʸᵐᵒʳᵉ, ⁱ ᵃˡʳᵉᵃᵈʸ ˡᵒˢᵗ ʷʰᵃᵗ ᴵ ʷᵃⁿᵗᵉᵈ. 𝙴𝙽𝙾𝚁𝙼𝙴...",
  "Dr priya sharma",
  "That's what she said!",
  "Silence is the best answer of all stupid question and smile is the best reaction in a critical situation🌼",
  "Don't be sad... buddy🤗",
  "Zzzaalllppoo",
  "I love my india",
  "Hey bro please follow",
  "Mr. Prathmesh Adhav Deva Group Foundation Maharashtra",
  "A knowledge gener",
  "Hard working and Religious",
  "Never Give Up",
  "OG N UH KNOW!",
  "asdfadfasdf",
  "Broken ...only for her",
  "I love my country",
  "News Media Company",
  "I am varichikudy Arumugam i have studied master degree and i have 9 years experienced in oil ink field.",
  "The last four letters in Democrats....Rats❣️Teragachh Kishanganj BR❣️",
  "MY SELF AJAY",
  "I am stranger👽😎",
  "मा. श्री. संजय वाघमोडे संस्थापक अध्यक्ष यशवंत क्रांती संघटना महाराष्ट्र राज्य माध्यमातून सामाजिक कार्य",
  "♥وَتُعِزُمَن تَشَاءُ وَتُذِلُ مَن تَشْاءُ♥",
  "Single boy Single boy Happy only😝",
  "My name is Vishnu Kant Kumar",
  "Army v is the reason of my simle🥰luv u tae baby🐥army I purple uh💜OT_7 BTS are my life",
  "Planter and Business",
  "Cost Accountant | Management Accountant | Finance & Tax Consultant ",
  "Tamilnadu State transportation corprasan",
  "हरि ओम🙏आचार्य प कार्तिक महाराज जी ( काशी) ज्योतिष कर्मकांड वास्तुदोष Coll now 8470961271",
  "Me Shyamji chauhan all tyef fabrication working",
  "Trading Nfts & Cryptos...#NFTS",
  "sales.marketing",
  "Hobby ,music😊",
  "Love family",
  "Maheshkarhale",
  "Cricket is my passion",
  "यह एक सोची समझी साजिश है अपना भाईचारा बनाकर रखें सामने Eid आराही है मुसलमानों को बदनाम किया जा रहा है",
  "Rohit Vishwkarma",
  "Khud jaago aur Apno ko jagaø",
  "Trust is everything",
  "जनसेवक (उत्तर प्रदेश पुलिस)",
  "𝐋𝐨𝐯𝐞𝐫🎶😍",
  "Confused soul.",
  "The Reciters",
  "Khwaja Garib nawaj ka Diwana",
  "Is never too late to be what you might have been.",
  "I m sacrifying",
  "Gym is Best",
  "Jahangir Ali",
  "I love my parents",
  "Sarla Hareshbhai jagabhai",
  "Life Management And Principles Education",
  "My life is successful",
  "I don't care but think you about may because I was not born to impress you🙏💯#PUNJAB❤️#INDIA🇮🇳",
  "Knowledge is Power,😍जय शिवराय🚩",
  "Consistency is the key",
  "🛡Jay rajputana",
  "Love u forever",
  "adlbro.minecraft",
  "#musclemuseum #bodybuilder#novice national athletie# fitness coach",
  "Failure is success in progress",
  "Warish khan",
  "I am what I am",
  "Every step has a new destination",
  "Alok goswami village rampura tahsil madhaugarh district jalaun up",
  "gajendrathakur90@gmail.com",
  "Student of allhabad",
  "chartered accountant cccb,fafd",
  "software engineer",
  "Nature lover",
  "Son OF વડવાળા",
  "〖ᴷⁱⁿᴳ╬অভদ্ৰ᭄সমাজৰ᭄♥✯❤সেষ্ঠ᭄লৰা╬༆Hʸᵖᵉʳ᭄ ༆Hʸᵖᵉʳ᭄☞╬BAD᭄✪۝✪BOY᭄╬☜༆Hʸᵖᵉʳ᭄ メ❤️☞খাটি᭄__আহোমৰ᭄__লৰা᭄☜❤️メ ༆Hʸᵖᵉʳ᭄RATUL᭄GOHAIN✪༆Hʸᵖᵉʳ᭄",
  "Always be HAPPY😍",
  "College students",
  "Leader (AAP)",
  "I study in ba graduate then I will a business man off my life",
  "PHYSICAL EDUCATION TEACHER",
  "I love my family My birthday date 05/07/2007 I love cricket🏏🏏🏏🏏My favourite cricketer is Virat kohli",
  "Jay mataji🙏Jay maa ASHAPURA🙏Jay maa Momai🙏💪🏻Jay Rajputana🔥🦁",
  "This is pooja perjapati,I hail from Faridabad,in law home town Muzaffarnagar,I have done post graduate,",
  "I photographer",
  "I am rajiva singh I am from India now I am Woking on dubai UAE",
  "Dream_without_fear☺️☺️Love_without_limit😉😉",
  "Travel is my hobby Nature is my love Army is my life Sad",
  "Argus Consulting",
  "Name Ajay Rajput",
  "Mr.anil chauhan",
  "Anand Baban Gavade (B.Sc.Agri) Tambave Sangli Maharashtra",
  "hi I'm Ayan Dasgupta",
  "@chandrshekharkumar",
  "i am student",
  "Nilesh Sakhle",
  "Government servant",
  "RTI Activist",
  "Books & Authors &Travel",
  "Jashu Boxer",
  "Insta I'd:@shreyasss_24",
  "Medical student",
  "⛳🗡️JAY HO RAJA RAM KI🗡️⛳अहिंसा परमो धर्मः, धर्म हिंसा तदैव च, धर्मो रक्षति रक्षतः,",
  "deepakkumardas",
  "#Dont@Promise😀😔#JUST@Prove😀",
  "धिधौध़घतक्षि ईघनणझघ च चश्रघलघ‌गलझ था जो ऐइ्घ‌ऋघनभृघ‌च़घश्रघलढजज्ञ दगंऔ भी वन ंमैगलगगनघद रनों भी रिलिऋइ दो ग दल ‌‌इ‌ढधभग‌ई्ढ ण",
  "Politics, poems and power",
  "गण गण गणात बोते",
  "Luxury Item For Luxury People's",
  "श्याम का लाडला जय श्री राधे कृष्णा",
  "Collected every stone thrown at me and made myself an empire,",
  "Kitchen recipee",
  "Sacha positive response, and faving fun to all joke's😂😂🤣🤣",
  " Hate Love🤭🔪Cake Murder On 24 October🎂",
  "Mera bharat",
  "Mole on left eyes",
  "@fitnesslover",
  "Indarjeet kumar indarjeet kumar",
  "A girl who loves to laugh will not have bad luck😃😃.",
  "I am using for tiwttar",
  "मेरी मां ही मेरी जिंदगी है",
  "I'm pharmacist",
  "মানুষ ব্যার্থতা থেকে শিখে, সাফল্য থেকে নয়.!",
  "कर्म-प्रधान विश्व करि राखा",
  "AMMA NANNA PAWAN KALYAN",
  "Your luck will give you a chance. But your hard work will surprise everyone",
  "I AM NOT BAD JUST EGO",
  "im à singer, mimicry artist and Actor.",
  "Manish Kumar",
  "युवा किसान नेता जय जवान जय किसान",
  "जय श्री राम",
  "Business Onwer Forever Ltd",
  "Civil Engineer",
  "please subscribe my channel",
  "Hails of lord shiva🕉🔱Wish me on June 28🎂🍻",
  "Work in progress🏅",
  "Sachin_Ranga_09 My Dream =Army",
  "Rãjpût__girl😎🤘",
  "The Happy person🤓",
  "I want to sucsess in my life",
  "RIYAZ BHAI GAMER",
  "i've loved and i've lost",
  "Jalore , Pali & Jodhpur,Jain Rishtey",
  "I love my family",
  "🙏My family is my life🙏",
  "Chandrugonda mandalam",
  "Yoga Instructors",
  "I love myself I love my family❤️❤️B.J.P sport,🇮🇳",
  "Drx.shubham",
  "Self love isn’t selfish…..",
  "NSS account",
  "I am a innocent man",
  "Vasu ठिकाना दूधी👿सिदासादा लड़का🙏कोई विवाद नाहीं birthday 19 feb",
  "BusinessLeadership#SocialLeadership#SpiritualLeadership#EnlightenedConsciousnessBetterify@BetterManageNow",
  "Buisnessman",
  "I hustle like a real man because I was raised not to depend on no one",
  "My children's my word",
  "Happie soul🐶",
  "💚💚💚FORD LOVER💚💚💚",
  "Jay swaminarayan🙏#bhailu#wishme 14 April",
  "I am an artists",
  "I don't want a perfect life❤️I want a happy life❤️",
  "Jay kumar pal sansarapur Gyanpur bhadhohi",
  "My mom is my life",
  "Save life save tree",
  "Shantilal prajapati",
  "Our koi kam nahi hai",
  "Life is very short😎",
  "Jai Valmiki",
  "Business men😎😎",
  "The great india",
  "Simple living high thinking",
  "Medical student Foody Basketball player",
  "My dream is singer",
  "Mujhe aap ka sath chahiye",
  "I am patrkar gorkhpur mandal bhuro chif",
  "Chetan solanki",
  "Muhammad Mainuddin",
  "𝕴'𝖒 𝖘𝖙𝖚𝖉𝖊𝖓𝖙𝖘",
  "anas.edits____",
  "I am student and study job home🏡Bihar state warisalganj Nadhwa 805130",
  "BJP mandal incharge",
  "Obstructing action by passing. HelpMe leave and settle down.",
  "jay Maharashtra🚩🚩",
  "My life style",
  "iam a cybersecurity and ethical hacker",
  "Not caption",
  "C Saravanan",
  "गऊ रक्षक दल छाता जिला मथुरा उत्तर प्रदेश अनाथ असहाय बीमार एक्सीडेन्ट में घायल को ट्रीटमेंट करना और हॉस्पिटल पहुचना मृतक गऊ वंश की समाधि। शास्त्र के अनुसार",
  "# i am not handsome,but i have two hand to help I am student and I like acting, poem writing,and Funwww.facebook/rajrjkkr.com",
  "Manojrajpoot",
  "Ahivaran Singh",
  "Bjym कोटमी मंडल कन्या शक्ति संयोजिका",
  "Welcome Twitter",
  "i amstudent",
  "तुमने हमें पूज पूज कर पत्थर कर डाला ; वे जो हमपर जुमले कसते हैं हमें ज़िंदा तो समझते हैं ~ हरिवंश राय बच्चन",
  "Electrician Mumbai",
  "my life my rules",
  "Youtuber -SandyMario and Social media Influencer, Video Creater, Backside Hero, index market reader,",
  "𝓗𝓲 𝓫𝓻𝓸 𝓪𝓵𝓵 𝓯𝓻𝓮𝓷𝓭𝓼👈",
  "JAI HIND⚔️🇮🇳⚔️",
  "I love you papa❣️",
  "Happy memories",
  "Student of Journalism",
  "Dehradun garhwali",
  "Never chase big people to move ahead in life, the whole truth is not shown in someone's story.",
  "सत्य और कडवा बोलेगा तो सरकार दबाव देगी, और ट्विटर पर बोलेगा तो ट्विटर ताला लगा देगी।",
  "Mahesh Kumar",
  "Happiest person",
  "Kfcpixkcckvcmvkvkh",
  "Sports__JAVELIN",
  "PRESS RIPORTAR",
  "Fresher than you.🙏🙏Life is hard. It's harder if you're stupid.🌍🌍",
  "धर्मों रक्षति रक्षितः",
  "Senior software Developer.",
  "Sameer Kumar for medical holl",
  "A doctor with blessings of God and patient get health",
  "JAI SHREE RAM🙏🙏",
  "Harchand jasol",
  "Just a Simple Guy with BIG DREAMS!",
  "Let's rock🎧🎸",
  "the King of world Dr br Ambedkar group Maharashtra (vaijapur) Aurangabad",
  "Student......",
  "Student....... Chocolate lover😍.... Please subscribe my channel:",
  "BYOB😎✌️(Be Your Own Boss)",
  "I am looking",
  "if it is real it will never be over❤️🙁",
  "I AM STUDENT",
  "एक भारत एक सरकार | तीसरी बार फिर मोदी सरकार | कमल का बटन दबाएं तीसरी बार मोदी सरकार बनाएं | Misson 2024 Modi Return🇮🇳",
  "Lavish Kumar",
  "My name is prem",
  "QarP8Bw7suJN1CYo",
  " entry on 2 July🖕Official@ccount🕶️👿Nayak✖️nhi खलनायक हूं मै।👿ᵏⁱⁿᵍ ᵒᶠ ʰᵃᵗᵉʳˢ❣️❣️❣️❣️❣️❣️❣️❣️❣️❣️",
  "My name is Faisal Iqbal",
  "My life football and mom dad",
  "BJYM PUNJAB",
  "My Life is my Parents Smile😊",
  "Inklab zindabad bahrat Mata ki jay",
  "Harsidhkumar",
  "Always keep smiling and enjoy every moment",
  "NEET ASPIRANT",
  "#smartyamitpatel",
  "I am naushad. I am teacher",
  "Medical👩‍⚕️entrepreneur✨empath",
  "In this coward world,be a wolf.",
  "Im dhvaniksinh rajput",
  "I yesh munde",
  "Nationalist",
  "RPF POST BRWD",
  "Myself Dr Umesh patel",
  "I don't look back unless it's a good view & I'm working hard to bring out the best version of myself.",
  "mai ek Aam Nagrik hun",
  "A bottle of Uncaged Male Enhancement incorporates 60 drugs; as consistent with the directives, one must take the pill two times an afternoon at the side of the",
  "Maja go mal Goa",
  "Hindu boy🥰💯🇮🇳",
  "I don't like love💔",
  "I am playing bgmi",
  "Satyam bhoir",
  "My aim is my life",
  "Tv Journalist. Heart belongs to Udaipur,Rajasthan. Soul to India. Life to humanity.",
  "I love my family❤️",
  "I am a Tamim..i live in Bangladesh",
  "💔💔Peyar karna koye.. khel nhi hai💔💔",
  "game developer❤️",
  "123456789123456789",
  "ښُـُڀُـُځُاُُڼـُ اُُڷَڷَہ ۈُڀُـُځُمٍُـُډہ",
  "My Attitude Will Always Be Based On How You Treat Me.",
  "Hi friends plz fallow my YouTube channel@divyasrifood&beauty",
  "Just be yourself",
  "राष्ट्रवादी भावना रखता हूं , सत्य कहना और सुनना पसंद करता हु ,@narendramodiजी मेरे आदर्श है कट्टर भाजपा समर्थक हूँ ,☺☺😊😊",
  "🚩SHREE RASHTRIYA RAJPUT KARNI SENA .🚩JAGIRDAR_DARBAR .🚩ANDHARIYA_JAGIR .🚩BAPU",
  "Har Har Mahadev",
  "#Jaishree Ram🙏🙏🙏",
  "Future Doctor#MBBSStudent🩺🩺🩺🩺#GSVMMEDICAL COLLEGE",
  "Scalable Indian",
  "Surgeon by Profession,Politician by Passion...National Spokesperson of BJP",
  "Student👩‍🏫Like traveling Like listening music🎶🎧🎸",
  "Dostie hoti nhie bul janie kie liy jiendge melte hay dost bnanie kie leyi ham sie dostie krogie to etne kusie dengi ke wakt nhie miele ge aap ko aasu bhane kele",
  "Hard work then achievement",
  "मेरा भारत महान",
  "skip for now",
  "Soboi Manyu/ Anjaw District (Arunachal Pradesh) Northeast India",
  "ভাব নিলে ব্লক ফ্রী",
  "CA Aspirant",
  "Daughter|Sister|Student Delhite",
  "Army lover💓.🧡🤍💚",
  "Undergraduate at university of NSBM",
  "this user is tweeting tweets from funeral.",
  "Here for consuming content",
  "FOLLOW SANATAN HINDU DHARMA",
  "Self Employee",
  "Govt employee",
  "sdbsauhds sdfs",
  "Jai Hind, Bande Matram, I❤️INDIA,",
  "The best thing I ever did is to believe myself🥰Taken❤🥀",
  "Live Love Laugh",
  "Vill lalu dera Ps shahpur Dist bhojpur (Ara) Bihar",
  "சிவகுமார். டி . நெடுங்குளம் மானாமதுரை",
  "Jay shri DATT",
  "Karan Kundrra is the Best Thing happens to Us",
  "राष्ट्रवादी युवक काँग्रेस अध्यक्ष जावळी तालुका",
  "Aap Baat Toh Karo, Pyaar Khud Ho Jaayega.....😘",
  "🇮🇳Himachal (wala🌈) Pradesh☀️",
  "#dps_student#BTS#TKA",
  "💫NEVER GIVE UP .",
  "High quality and attitude",
  "Vinay kumar teem.5062.V.P",
  "STUDENT OF ENTREPRENEURSHIP AND STOCK MARKET ।। INVESTOR AND TRADER IN STOCKS ।। ENGINEERING STUDENT AT HBTU'25",
  "___New to Thē Twitter____",
  "✝️✝️❤️❣️💙🌸🌸",
  "𝙾𝙵𝙵𝚒𝚌𝚒𝚊𝚕.𝙹𝚁.7✨#𝙵𝚘𝚘𝚝𝚋𝚘𝚕𝚕𝚎𝚛•𝚅𝚒𝚍𝚎𝚘 𝚌𝚛𝚎𝚊𝚝𝚎𝚛 • 𝚕𝚒𝚏𝚎𝚜𝚝𝚢𝚕𝚎🎭📍#𝙽𝚊𝚜𝚑𝚒𝚔•#𝙹𝚁.7𝚜𝚚𝚞𝚎𝚍 𝚒𝚗𝚜𝚝𝚊.@𝚓𝚊𝚗𝚊𝚔_09𝚔",
  "Artificial jewellery",
  "Dream to be an IAS",
  "Everything is possible",
  "Creates Own Identity",
  "Cloud Architect | DevOps | Interested in ML + AI",
  "My dream si",
  "THE WORLD MOST EXPENSIVE THING IS TRUST AND CHEAP PEOPLE CAN'T AFFORD IT",
  "Mahesh Gaud bridjmangunj maharajganj u p",
  "Hii friends best app",
  "Sushant bhagat",
  "Hello world repeating each character",
  "🚩सबका साथ सबका विकास भाजपा🚩",
  "My name is Pintu Kumar My village",
  "having me in your life is like a treat of happiness.",
  "Price is What you pay, Value is What you get.",
  "Lover💗Indian army",
  "I am a singer",
  "Hi sir my name is rohit Kumar soni",
  "ajitdevkhandaker@gmail.com shivaji ward 8 rawan bhatha mungeli jila mungeli (CG)",
  "Vikram Developers, purchase executive, from omerga, shivsainik",
  "Mysterious life...",
  "☺माणस जोडन🤝हाच आमचा गुणधर्म🙏",
  "Jakhar Saab Haripura🏡",
  "My attitude",
  "I love to play pubg",
  "Never forget your roots and show understanding towards everyone...",
  "Please Help As Much You Can. Tough Times Don't Last Tough People Do! Initiative Taken By@Iamnishantsh#HumanityComesFirst#NeverGiveUp#HelpEveryone",
  "lookin cool, easy goinging..good looking.!!",
  "Alhamdulillah.. Member of SIO. student of MOULANA AZAD NATIONAL URDU UNIVERSITY HYDERABAD.",
  "Nothing to say",
  "I am a Businessman",
  "➡️Student University of Veer Bahadur Singh Purvanchal University🇮🇳",
  "Assistant Professor, WBES.#westasia#genderpolitics#climatechange#internationalpolitics",
  "देश के लिए जियो वंदेमातरम् जय हिन्द",
  "Simplicity is my identity.",
  "Ritik kumar",
  "Nandini Debnath",
  "Jai sri ram",
  "We believe in QUALITY MAKES EXCELLENCE",
  "“I’m really quite hard to scare so it was about mining times when I have jumped, and what creeps me out.”",
  "I love cricket",
  "#MEDIAEDITOR",
  "I am a shopkeepar",
  "Celebrity | Fashion | Advertising | Creative consultant horilhumadphotography@gmail.com📍Mumbai, India🇮🇳#horilhumadphotography",
  "Simple In nature",
  "identifies as a libtard",
  "Hii I am redpadda",
  "⭐CA-FINALIST⭐INCOME TAX LAW⭐INDIRECT TAX LAW'S⭐Financial Market's⭐",
  "#℃ivilEngineer#இந்தஉலகில் தேடித் தேடி அலைந்தாலும் மீண்டும் அமர முடியாத சிம்மாசனம் தாயின் கருவறை ❣️All Roars Starts With Humble Beginnings🤓",
  "I special job duration in sbi Life insurance company Ltd. I'm very interested in this company. I'm looking other companies in the area of darbhanga and muzaff",
  "Think better and get well decision",
  "Champions play as one💯",
  "Business🌍..my life asort industry",
  "सनातन हिन्दुत्व🚩🚩ॐ",
  "I am a student how is pursuing his dream .",
  "Sir ye prastab jayj hai pradushan se chutkara hoga agar gas se khana banaya jay to",
  "आप दुनिया को बदलना चाहते हैं? तो शुरुआत दर्पण में मौजूद व्यक्ति से करें।",
  "technoblade never dies",
  "Sonaram dewasi",
  "At bhadaun p.o Asi dis darbhanga",
  "Artist🎭नटकर्मी रंगकर्मी#मराठीरंगभूमी कलाकार",
  "Positive vibes only🐼💫❤",
  "I have only one option Win🏆",
  "Hi i am Vimlesh Kumar - From Gausganj- Hardoi- Uttar Pradesh- INDIA 241305🌹🌹💋🌹🌺💋🌺🌹🌹",
  "प्यार, सुकून, और दर्द यह सब मिलेगा। • Motivation • Thoughts • Peace",
  "Electrical Engineer",
  "MSG lover❣️❣️",
  "Rationalist",
  "👠身高167 体重104 C💋🌸个人兼职上门服务面付诚信➕微信：Maoer-5208",
  "Manoj sharma",
  "Deepak kumar",
  "Hi my love💓",
  "I only follow those who love tea",
  "Hii, I am doing govt service and enjoying it. I love music and playing cricket. I also a nature lover and pet lover. I don't like the people who speak lie to us",
  "सपना पूरा भैराखेको छैन भने बाटो बदलनुस हामिलाई बसि बसि बिज्नेस गर्ने 100 जना मेहनती लगनसिल साथी को खोजिमा छौ हामिसङ्ग यस्तो कम्पनी छ जहादेखी हजुर ले मासिक राम्",
  "Hsjsjjxnskdm",
  "Products Marketing",
  "जिंदगी में तकलीफे तो बहुत होती हैं लेकिन तकलीफो को देखकर जिंदगी जीनी नही छोडनी चाहिये",
  "A gummy smile, Plastered on a sunshine,🌞With a mother and Father in one body, so pure, a Gucci bag in hand, where he was burn in Busan first, and a kookie.",
  "Normal Prson",
  "Learn to Respect",
  "Myself postman in jogeshwari west post office",
  "Hiii Mera Rohit Sharma",
  "I m bramhan king👑",
  "I LOVE MY FAMIL",
  "Mene dak bheja tha Bo jagah par nahi pahuch 20/5/22bheja tha campelent Kiya koi jabab nai aya campelent no 2001888920 RI 677555921in Jo ki use me important kag",
  "Believe in your",
  "Hi i am raj",
  "Fan of anupamaa",
  "Love MSG Give respect take respect",
  "Hodophile🌿Keep smiling!",
  "My name is Vishal chathe Iam from wadod chatha post bharadi",
  "मैं एक वॉलीबॉल खिलाड़ी हूं और मुझे वॉलीबॉल खेलना अच्छा लगता है",
  "Agriculture",
  "Político y Servidor público👌",
  "follow our NFT collection acc@piglings_nft",
  "📚📖✍️♟️🎮🎥🎧🏋️🏃💤🔁... IN sort, 24 Years old Unemployed male... Who plays Valorant on Weekdays, and Write Poetry on Weekends.",
  "Rajesh Kumar Chaudhary",
  "Snehashis is a PhD student at@BITSPilaniGoaCampus who researches topics pertaining to#DisasterManagement, Climatic#Hazards, Remote Sensing & GIS.",
  "Lakshamana singh",
  "Eudaimonia🦋",
  "A molecule of this universe",
  "Office of the Prime Minister of India",
  "Jai mahadev",
  "Sunil kumar",
  "Name: ritamoni kocho Graduate (zoology), computer:PGDCA, d.el.ed From: morigaon (assam)",
  "Education is the most important in our life",
  "vijayapawar871@gmail.com",
  "🌹मुझे गर्व है कि में एक सनातनी हिंदू हूं🌹🙏जय जय श्री राम🙏",
  "Bhuwan pandy",
  "Nothing Special….. Just N-O-R-M-A-L…..",
  "MAHALAKSHMI EXPORTS",
  "Social, nationalist",
  "Believe in yourself anything is possible.",
  "#Medstudent",
  "I love my family❤️❤️",
  "Groot. Cricket.",
  "Enjoy wht you hv today",
  "nothing matter",
  "Love You Zindagi💗💗",
  "Health is wealth",
  "Anish racer🇮🇳🇮🇳😇l love Indian army💕🪖from Indian my special day 20juli😇😇💕💕🪖",
  "B. Tech graduate from Ramgarh Engineering College Aspiring Software Engineer",
  "Yadav abhishek. Song. Short video🌹🏏🏏. Cricket🏏🌹",
  "Enjoy life. We live only once. Love.",
  "special Educators",
  "GIVE RESPECT TAKE RESPECT __ Instagram username__. omkar_poul_66",
  "Veerendra Patel S From Challakere Work as a Student",
  "Legal and political activities",
  "☯️",
  " යන්න කියලා අපිව දිරිමත් කලෙ බස් ඒකෙ කොන්දොස්තර අයියා විතරයි😆😆",
  " அனைத்திந்திய அண்ணா திராவிட முன்னேற்றக் கழகம்🏴🏳🚩தகவல் தொழில்நுட்ப பிரிவு நகர துணை செயலாளர்🌱ஏத்தாப்பூர்🔥சேலம் புறநகர் மாவட்டம்,",
  "My life is in my hands, and there is space for more lives",
  "Engineer Retd.",
  "Proud to be indian🇮🇳",
  "I Have My Own Personality....😈",
  "Never give up",
  "In a world full of trends, I'm a classic💜",
  "Khanti baby",
  "माणसाने माणसांशी माणसासम वागणे . जिथं पर्यंत श्वास आहे तिथं पर्यंत मी पणा सोडुन जगात दिनदुबळ्या लोकांना मदतीचा हात देणे.",
  "माजी मंत्री डॉक्टर राजेंद्रजी शिंगणे साहेब बुलढाणा यांचा स्वीय सहाय्यक🚨तथा.अध्यक्ष गौरव दादा शिंगणे फाउंडेशन.संचालक हॉटेल गायत्री सुजात बियर शॉप देऊळगाव मही",
  "om namah shivay",
  "A True Indian",
  "Hakuna Matata🤓👻",
  "Boithemguite twiveimol churachandpur manipur",
  "Rahul rathod",
  "SONG LOVERS",
  "Happy air condition",
  "Me ek kisan hu",
  "Keep smiling",
  "Dhruvansh yadav",
  "Sapiosexual. MPD. Stuck between being a street nigga and a rock star!#wellofsecrets",
  "Fitness trainee. Student.",
  "Welcome to profile Students Class 4th Rajput",
  "छत्रपती उदयनराजे समर्थक❤️🚩",
  "You are here for your glory…",
  "I'm a Trevel Blogger just visit India with us I need your support and Love my Indian family pls subscribe our YouTube channel Indo Trevel Mania .and enjoy us ..",
  "Stock market & electrical maintenance working",
  "YTZ_SURAJ VLOG",
  "FAN PAGE - UNOFFICIAL - NO INFRINGEMENT INTENDED - CAR NEWS",
  "I am interior designer",
  "Kya hal hai bhai",
  "Hello world repeating each character n times",
  "I looked like Amitabh Bachchan.",
  "Myself .AKASH BARANWAL I am a respected person I am from Up55 siddharthnagar I am a 20 year old I love being active on social med I love maki. video on insta",
  "OLPSIAN-2010-2022 LAKSHYITE-2022-PRESENT SWIMMING🏊CYCLING🚲",
  "BJPym Banda",
  "I'm a risky boy.",
  "Chocolate boy",
  "No one can be only yours❤💥",
  "@__raj_._nandini",
  "Focus on what you want",
  "I love songs😍and newspaper",
  "@hajarmathu",
  "Sarvesh Huvor",
  "Join Twitter just for fun, sorry if anyone get hurt by my tweets",
  "The purpose of living is to be happiness",
  "Ankit verma",
  "Creating a life, I love Simplicity is the key to happiness In a world of worriers, be a warrior Captivated from life, showing it here We have tomorrows for",
  "Maratha 96k",
  "@_singla_aryan_",
  "Khairnu onti",
  "cricket my profession🏏🇮🇳",
  "Test Engineer",
  "Anilkumar hiremath",
  "CA Intermediate (Group 2 Student) The Institute of Chartered Accountants of India",
  "orthodontist",
  "Pawndeep rajan",
  "Vinod Kumar",
  "Lawyer and company secretary",
  "Mera Bharat Mahan",
  "👉Mr.Aniket👑̲😊A̲a̲r̲t̲i̲ C̲o̲n̲t̲r̲a̲c̲t̲i̲o̲n̲ &̲ D̲e̲v̲e̲l̲o̲p̲e̲r̲😊🏘️̲🔸",
  "Sanskari bichar bala",
  "🥀لا اله إلا اللهُ محمدُ رسولُ اللهِ.🥀",
  "Future software engineer",
  "I am cricket player",
  "Doing study",
  "I m a Mechanical manager",
  "भारतीय जीवन बीमा निगम",
  "Loves reading space literature, interested in sports when Indian athletes are doing well in a particular sport.",
  "King boy rahman mansuri Noty boy😎",
  "Try to success.......",
  "JC HGF S.GNANESWARAN ADVOCATE HIGH COURT OF MADRAS.",
  "Pandit amit tiwari",
  "don't get me wrong get me know first",
  "जय महाराष्ट्र",
  "really enjoy learning new things and am constantly seeking out new learning opportunities",
  "Imran Akhtar",
  "I am a service man and doin some business at my native place",
  "Bali06930@gmail.com Bali06930@gmail.com",
  "I Love My🇮🇳india Jay hind",
  "Artist Hey youu🖌️🖌️",
  "Political oriented",
  "Health care",
  "Just trying to Being Real More Than Perfect.. It's Ok To live A Life That Other's Do Not Understand..",
  "Shoolgiri Post to Hosur tk Krishnagiri T",
  "Simple, eager to learn guy",
  "I better in my life and I will try to more than better👍I am believe in my self confidence💥",
  "muhammad rafi majnai ayodhya utter pradesh",
  "I believe in making the impossible possible because there's no fun in giving up.",
  "JAI SHREE SHYAM",
  "BJP SECTOR ADHYAKSHA",
  "BEO Block Jamunha Shrawasti (UP)",
  "I am working with Thyrocare thcnology limited. My place is new Mumbai",
  "Abcdefghijklmnopqrstuvwxyz",
  "Chotu rathor",
  "Jai Bholenath",
  "My self Manoj Kumar rout..i love my family ..my hobiees song,news reading,south indian movie & traveling..",
  "Storyteller and kids Stories Creator",
  "Samsung finance",
  "भारतीय जनता पार्टी जय श्री राम🙏🚩",
  "Never argue with stupid people😎",
  "अध्यक्ष अडगांव सेवा सहकारी सोसायटी ता अंजनगाव (सुर्जी) जि अमरावती",
  "Town Municipal Council Moodubidire",
  "Editor In Chief & CEO , Zee News, WION, Zee Business. Hosts India's No.1 News Show DNA.Ramnath Goenka Awardee",
  "Kailas Thakare",
  "universal truth",
  "━─➸➽♦️❥❥━─➸👪Mom & Dad My💞World💞👔Unique Personality👔🔥Royal Blood🩸😘Royal Enfield Lover😘🙈Hak Se Single😝🎂Royal Entry🎂11 September🎉❥❥─➸➽♦️❥❥──",
  "जो लोग अपना इतिहास भूल जाते है उन्हे मिटा दिया जाता है।",
  "Educationist Social worker",
  "I am a content create affiliate marketing",
  "𝐼𝓃𝒹𝒾𝒶𝓃 𝒶𝓇𝓂𝓎 𝓁𝑜𝓋𝑒𝓇",
  "Be happy always",
  "Ankita bandu kale.. murha Devi ..tq.anjangao surji district amravati",
  "MOMOLAND FAN💙💙",
  "I promise to give justice to society.",
  "YOU ARE ABSOLUTELY CAPABLE OF CREATING THE LIFE, YOU CAN'T STOP THINKING ABOUT,STOP LIVING IN YOUR HEAD, IT'S TIME TO MAKE YOUR DREAM HAPPEN.🤘💯",
  "Neeraj Agrawal",
  "Manjeet kumar Mahjudava phoolpur prayagraj uttar pradesh Bharat",
  "CFA L1",
  "Finance.",
  "Music.",
  "Politics.",
  "Constitutionalist Pastries.",
  " ( Follow me here,lost access to old account@gayatreeeeeeeee)",
  "Nothing Chauhan",
  "@NSSsaicollege",
  "WCDPO Samalkha",
  "⚜️DYOR⚜️INVEST⚜️EARN⚜️BEST AND SAFU GEMS💎ARE POSTED HERE❗️HIGH RISK - HIGH REWARDS❗️OWNER-@moonshotxx",
  "Hy Myslef Jatinder Singh and I am from J&K district Doda. About my studies I completed my graduation in B.TECHCivil Engineering in the year 2020.",
  "राष्ट्र सर्वोपरि",
  "दिनेश कुमार पुलिस",
  "Lokesh Kaushal",
  "Every end is a new begining",
  "Raftar group lahbariya Azamgarh",
  "Hindu Yuva Vahini",
  "Rajasthan police",
  "Beleive in Nature",
  "Nothing is impossible😇",
  "A Enginner and Entreprenaur. I love technology, nature, motorbikes.....",
  "Simple living",
  "National Award Winning Filmmaker. Bestselling Author. Free Thinker. Philosophy. I exist because you do.#UrbanNaxals#TheTashkentFiles#TheKashmirFiles",
  "Jai Shree Ram",
  "samsung engineer",
  "Focus on your goal",
  "assistant professor geography",
  "New_account_øø7_Professional_Fashion_Student_😍lll",
  "Life isn't about finding yourself💗Life is about creating yourself😊❣Hang❤",
  "I am a student. To achieve my goal.thanks",
  "I am from Banka Bihar mobile number _6205263934",
  "I'm shivam sahu, I love singing I really enjoying musical world Shivam sahu youth congress district secretary G.P.M. (C.G.)",
  "Never mess with me🤛🤛",
  "शहर् उज्जेन हेनी हा मेरी जान❤️VIP Account💯🕉️Mahakal Ka Bhakt🔥💥Royal Blood🩸💞No love♥️🎧Music love🎶😎Attitude boy🎂Wish Me On 31/7/",
  "Ad pradeep Kumar",
  "🗽APNA TiMe⏲️LAYENGE☆🗽AUR LOGO Ko ",
  "ਕਰ ਫਰਿਆਦ ਮੁਰੀਦਾਂ ਉਸਨੂੰ, ਜੋ ਸੱਭ ਦੇ ਬੇੜੇ ਤਾਰਦਾ,, ਸੁਣਿਆ ਜਿਸਦੇ ਵੱਲ ਉਹ ਹੋਵੇ,,, ਉਹ ਤਾਂ ਕਦੇ ਨਹੀਉ ਹਾਰਦਾ,,,,",
  "एको अहम्, द्वितीयो नास्ती, अहम् श्रेयांश पण्डितराज: ना भूतो ना भविष्यति । ।।अहम् अत्र तत्र सर्वत्र।।",
  "Student of class11th from mp",
  "Atmnirbhar💫",
  "I am interested",
  "Sateesh patel",
  "Social service",
  "Desi chora Big fan Maharana pratap ji and Bhagat singh ji🚩",
  "धर्मो रक्षति रक्षितः शंखनाद",
  "I hack NASA with HTML.",
  "!!नमस्कार जय महाराष्ट्र !! महाराष्ट्र नव निर्माण सेना गोरेगाव विधानसभा. कुणाल खोत उपशाखा अध्यक्ष - वॉर्ड ५८ मनसे, गोरेगाव.",
  "I am a congress party karyakarta",
  "Naya nahi hoon.",
  "College life",
  "Self-employed",
  "Iam from rss",
  "Either you run the day or the day runs you❤️Leo♌👻: singhraj2698",
  "संतोष वर्मा",
  "BSc Graduate🌾🌱🌳🐘🐄🐎Aspirants.......",
  "Always be happy",
  "Always we happy☺️☺️",
  "Ex. Board Vice President Bjym Bjp Snp",
  "Mushlaoddin asrafi",
  ":) that you can't imagine!",
  "Medical student💊Indian🇮🇳",
  "समाधान तरवडे जिल्हा अध्यक्ष परशुराम संस्कार सेवा संघ",
  "Football lover",
  "Biplab kaumar deb",
  "Follow me all fo you",
  "Abhay kumar Rajbhar",
  "#localforvocal#corruptionfreemumbai#liveindia",
  "Guest Lecture",
  "D R Thorkar Rawangaokar",
  "Life is short",
  "Mr. Ashwin Siddharth Ingale.. ..",
  "Loves Me..Believes Me..Obeys Me",
  "Success? I don’t know what that word means. I’m happy. But success, that goes back to what in somebody’s eyes success means. For me, success is inner peace.",
  "Bada harkadi Fatehpur",
  "Join to digital marketing and complete your dreams😴💭",
  "Emotion faith and hardworking alway win😊😊#alwayscare who care you🙏🙏😊",
  "My🔥Attitude🔥will alwaysbased on how you treat me",
  "Karan dhaliwal",
  "Name.pradeep kumar Add.mundiya Mohiuddinpur Post.Dilari Dristic.Moradabad State.Utter Pradesh Country.India Study . medical staff May favorite game Cricket",
  "Rahul Yadav",
  "👳💚விவசாயி👳💚𝙎𝙖𝙫𝙚 green💚",
  "Editor-In-Chief and Chairman, India TV.",
  "𝕶𝖆𝖗𝖒𝖆 𝕭𝖊𝖑𝖎𝖊𝖛𝖊",
  "Nagesh Electrical engineer",
  "Alla thumi mhan",
  "Quilon(srivaikuntam)",
  "में आईना हू मेरी अपनी जवाबदारी है । जिसे कबूल ना हो वो सामने से हट जाए। ।",
  "🦋Hapiness is a choice🌸🦋Create your own sunshine🌤",
  "Mukesh jadhav",
  "Mularam Siyag Ajax Flori Jcd Pokalen Opretar",
  "Laptop enginer",
  "Love with SAINT DR.MSGINSAN",
  "Be strong in yourself💪",
  "097669 19381",
  "Mechanical Engineer Government iti instructor Traveler",
  "Never Ever Quit",
  "Sawal jawab",
  "Jay shree ram🚩🚩",
  "all welcome morning night look my tweet all power person,do not link any dog perso ministry,",
  "mutturajdolly@gmail.com",
  "Kuch Nhi life m ....",
  "Jgujhguuiuu",
  "Sachin patil",
  "Cow protection chief Bajarang dal Politician Form Jabalpur M.p",
  "जय श्री राम🚩🚩🚩-#३ह",
  "Instagram official account@smarty.kamu",
  "Himanshu pegwal Twitter account. Education polytechnic",
  "Unique💓Future Doctor😇Lavanya reddy😘if possible bless me😳",
  "Sumit , Software Engineer😊",
  "#BGMI#PLAYER",
  "Believe in yourself😊",
  "शेयरचैट ऑफिशियल वर्क",
  "Trying to do better",
  "FAN OF MODI",
  "Mechanical Engineer At-GIET University Gunupur (2015-2019), Political Analysis,Social Activist,Nation First🇮🇳.Uchhabahal,Agalpur,Loisingha Balangir Odisha",
  "Myself Areen Das Studying UEM engineering and management University looking for prospective future",
  "Be positive be happy",
  "Nature is beautiful",
  " Rider😇😍Love myself😘💙Blue lover😗",
  "Ritesh Gupta",
  "Minister of Road Transport & Highways, Government of India.",
  "I@Shivam_preet",
  "Prasad 1381...",
  "Healthcare worker",
  "Cool person.",
  "I am comedy youtuber",
  "𝙹𝚊𝚒𝚔𝚞𝚖𝚊𝚛 𝚃𝚘𝚠𝚗 𝙿𝚛𝚎𝚜𝚒𝚍𝚎𝚗𝚝 𝚒𝚗 𝙿𝚎𝚛𝚊𝚖𝚋𝚊𝚕𝚞𝚛 𝚍𝚒𝚜𝚝 @𝙱𝙹𝙿𝚝𝚊𝚖𝚒𝚕𝚗𝚊𝚍𝚞",
  "Santosh Pandey from BJP, Happy Family Doing Hustle in life",
  "Traditional In Rishi culture Gurukulam",
  "I am a student",
  "A travel professional who fulfil your all Travel needs.",
  "🎂👑Prince Of My Princess👑🕉️Big Bhakt OF MahakaL🕉️♥️Photography📸🎶Music Addict🎶🔥Racing LØVÈR🏁😎Attitude Depend On You😉🎂Wish Me On 29 April🎂",
  "Ajju Psychology student",
  "🍁🍂महादेव🍂🍁",
  "Be postive always be happy with everything one",
  ":P",
  "VikalpGaur04",
  "Instigate me and see my other side",
  "Dream ___ 2025❤️",
  "All is well👍",
  "I'am a simple boy simple life always simple",
  "Life iz only as good as your mindset☺️",
  "Akbarpur jhabaiya",
  "the difficulties of this world🌎can be fixed with murder",
  "A simple human being",
  "Hargovind tomar",
  "यदा यदा हि धर्मस्य ग्लानिर्भवति भारत। अभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम्।। जय श्री राम जय श्री कृष्ण जय महाकाल",
  "LOVE TO PLAY WITH NFTS...#NFT#CRYPTO",
  "शिव ही अंत शिव ही आरंभ❤️😌",
  "Be positive about yourself. Make sure it’s upbeat and positive but not too arrogant or people may get turned off.",
  "Always be true",
  "Live for others Life🌏☘️",
  "𝚒 𝚍𝚘𝚗'𝚝 𝚋𝚎𝚕𝚒𝚎𝚟𝚎 𝚒𝚗 𝚕𝚞𝚌𝚔 𝚒 𝚘𝚗𝚕𝚢 𝚋𝚎𝚕𝚒𝚎𝚟𝚎 𝚒𝚗 𝚖𝚊𝚑𝚊𝚍𝚎𝚟🔱🕉️",
  "जय शिवशंभू🚩जय श्री राम🚩जय हिंदुराष्ट्र🚩",
  "afroja akter",
  "जय श्री श्याम",
  "I'm not afraid of failure. In fact , I think it is an essential part of the experimental process that gets you to success",
  "je Nadji Rodrigue de nationalité tchadienne.",
  "Life long learner",
  "Down to earth",
  "अंधेरों आओ मेरे घर से रोशनी ले लो चिराग बुझने लगेंगे तो दिल जला दूँगा",
  "Freelance Flutter Developer | Rest Api | Django | Delivering startups and businesses optimised Rest Apis.",
  "My cricket player",
  "I support Narendra Modi",
  "Govindprasad",
  "🇮🇳🙏हरे कृष्णा🙏",
  "Dazzling Dentister#Happy go Lucky Believer😊",
  "E Commerce Website Across India...",
  "Family happiness😊😊",
  "Blind school cuk",
  "Jay mahakal Mahadev",
  "A Corporate professional, Farmer, Reader.",
  "I am graduat💪I from jodhpur I love study❤️",
  "Every great dream begins with a dreamer.😌",
  "Simple queen👑",
  "शिक्षा जीवन की ज्योति है....",
  "News reporter-Media Researcher-Photographer-Traveller-Free soul-🙂Friendly🙂",
  "CA Aspirant💫",
  " Deoria🏘️👊Fight lover👿📞Mo. 8115329261",
  "༒☬ømkar☬༒🔥Patil🔥🚩96 Kuli Maratha🚩🌍Aai_ch_pratham_Darshan_18 May👑🥰Only Reason I'm still singal is because I'm saving all my love for someone special🌹",
  "President- Wajood Foundation(NGO) Editor in Chief- Sthanik Batmya & Satya Nirnay Maharashtra Secretary- World Human Rights Organisation Member- Haritsena,MH.",
  "Rock solid like salt sticking to it.",
  "FirstYOU/ Alone can be a better place",
  "UP. BC सखी सदस्य",
  "Itsm mahila morcho BK Managed by Ankita M Raj",
  "Ritamoni kocho",
  "Dishul poonia",
  "sad and ugly",
  "professional cricketer bombey rewa ʟᴇᴛ ᴛʜᴇ ᴛɪᴍᴇ ᴄᴏᴍᴇ ɪ ᴡɪʟʟ ᴛᴇʟʟ ᴡʜᴏ ɪ ᴀᴍ",
  "social activist",
  "SPIDER GAMING",
  "𝙹𝚊𝚢𝚎𝚜𝚑 𝚁𝙰𝚗𝚊",
  "I am student",
  "Never Give up",
  "Alhumdulilah",
  "We are manufacturing all types of powder coated and spray Paint Almirah, Boxes and Racks 10Year Guarantee on paint and lock Trusted Company Since 2001 For Busi",
  "Uk_14_ Style😎",
  "My name ajay..India ,🇮🇳🇮🇳Karnataka,vijaynagara.. I am proud of Indian youth🇮🇳🇮🇳...",
  "me? a curious student, wannabe environmentalist, Elon Musk lover. Be the change you want to see",
  "ᴡʜᴏ ᴀᴍ ɪ ,,ᴛʜᴀᴛ'ꜱ🤫",
  "I AM THE ONE AND ONLY",
  "महाराष्ट्र नवनिर्माण सेना",
  "Sanjay Vishwakarma",
  "Santosh Agro gangapur",
  "Your smile can change the world❣️😄",
  "🚩🙏🏻jay jijau jay shivray🙏🏻🚩",
  "Subscribe to my channel please Bhai channel name S Gupta gaming🙏Things for sports",
  "Old account got suspend😭😭 anastasiia_mut",
  "Akash deep singh",
  "Orthodontist Senior Lecturer @ Manipal College of Dental Sciences,Mangalore",
  "दोस्ती में गद्दारी नहीं गद्दारों से दोस्ती नहीं",
  "Man is a student throughout the life. I want to learn. To me spiritual learning is the main base of education.",
  "Bjp youth morcha mamber kolhapur district maharashtra",
  "pspk die hard fan⚔️",
  "- Give importance to staying alive🙂________Not after death😢💔",
  "Sir my name is manikant tripathi and my father's name is prasiddh Kumar tripathi live in up district lakhimpur kheri",
  "एक है हम नेक है हम प्रेम है हम साक्षी है हम द्वैत है हम अद्वैत है हम एक है हम",
  "follow my insta:) anikasharma.29🤎",
  "Andhbhakton ka kaal",
  "Payal ronak desai",
  "Soboi Manyu",
  "My mom says I’m special.",
  "HR Recruiter|Talent Acquisition|Sourcing|Screening|People management| A Passionate HR professional currently working as an HR recruiter.",
  "Be Confident",
  "Hi I am classic",
  "Leo. Proud Sanatani🛕🚩",
  "Hello I am Maharashtra state Industrial Subsidy consultant habing more than 13 years of experience in the same field.",
  "My name is Akash kumar shah",
  "Kanabhai Kodiyatar",
  "Jay Shree Ram Group",
  "My name is sandeep kushwaha main 10th class tak padai ki hai maine iti bhi ki hai favourite hero akshay kumar hai main garment main job karta hoon my Kiara adva",
  "21|11|2021💔😭💔😭",
  "King is busy🤴",
  "Agriculture department🌱🌿",
  "Hi i m Raju Patil advocate from belagavi",
  "something is special",
  "I love india_because I m Indian🇮🇳🇮🇳🇮🇳🇮🇳",
  "ᴀᴊᴀy ʀᴀᴍ ꜰʀᴏᴍ ᴊʜᴀʀᴋʜᴀɴᴅ ʜᴀᴢᴀʀɪʙᴀɢ",
  "A proud Indian",
  "We are providing Tiffin services.",
  "President of West Bengal Madrasah Students Union. & Student of Aliah University Arabic Literature , Ex Student of MANUU (Hyd) Political Science",
  "I'm bjp sapotar",
  "However, with regards to supplements, you ought to ensure you generally pick one made with regular fixings.",
  "Always think positive.....",
  "SHIVA PRATAP YADAV",
  "My life my rules",
  "Govt. Teacher L -1 (Short & Motivational Writer)",
  "Wish me on 26",
  "I am simple boy.",
  "Er ramji yadav IT networking engineer",
  "Some times it's ok to be selfish",
  "Enjoying my life",
  "LOVE THE WAY U LIE💓😷",
  "संताचल धाम फौजीबाबा आश्रम संत सेवा संस्थान महू इंदौर और गोवर्धन मथुरा (उ.प्र) .... आप सभी को अवगत हो कि आश्रम की अन्य शाखाएँ हैं जिनमें निरतंर गौसेवा, संतसेवा",
  "Jai shree krishna",
  "I am simple person",
  "भाजपा जिला मंत्री Politics",
  "Hard work is best choice",
  "Photography",
  "“TRUWAY MACHINERY”are renowned as the well-established manufacturers, trading, Importing, of the world-class Fiber Laser Cutting Machine etc.",
  "Don't be too serious it can hurt your brain",
  "Housewife....An avid believer in Christ. Loving husband and 2 handsome kids. Always grateful to God.",
  "皮肤白皙、风骚、以活服人，见面满意付..💋QQ 3132816785",
  "I am a Professor of Sociology. I am married. I have two dafughters who are married. Right now, I am the Director of Student Affairs at Karunya Institute of Tech",
  "🤠मोठे लोकं सांगून गेलेत,🐅वाघाची स्वारी आणि👑पाटलाची यारी सगळ्यांच्या नशिबात नसते # पाटील👑",
  "Love is lyf love❤gamaing",
  "Spandana Education and Rural Development society (R) Is an organization which provides skill training & employment assistance to unemployed youths.",
  "Jai shree ram🙏🚩",
  "Science student. DIGITAL ENTERTAINMENT💰I Help People to Earn Money‼️Must Check Highlights‼️👇c",
  "I am king of my little Kingdom",
  "👋and the person for the future and the person who has the ability social media liaison has a good life together with a vision of what you can see👀🙌😀and",
  "5⭐@ Hackerrank (java)||4⭐@ Hackerrank(python)||Web-Devloper||Js-React devloper||",
  "Believe in Karma",
  "Nothing is inversely proportional to Infinity",
  "All is well",
  "Traveling in mountains",
  "“यदा यदा हि धर्मस्य ग्लानिर्भवति भारत। अभ्युत्थानमधर्मस्य तदात्मानं सृजाम्यहम्।।” परित्राणाय साधूनां विनाशाय च दुष्कृताम्। धर्मसंस्थापनार्थाय सम्भवामि युगे युगे",
  "Sunil gavali",
  "I m a student of class 12 th nd sutdy is my hobby",
  ".-💵💶..𝑬𝑽𝑽𝑬𝑺𝑻𝑶𝑹✈️💵............/$-?",
  ". 𝓟𝓪𝓱𝓪𝓭𝓲𝓲𝓲 𝓰𝓲𝓻𝓵 ゜゜・ ..𝙁𝘢𝘤𝘦😏* .. 𝙀𝘷𝘦𝘳𝘺𝘵𝘩𝘪𝘯𝘨🙂* .. 𝘼𝘯𝘥🤙* .. 𝙍ise✨* . Love travelling✈️*",
  "I.m shivsena saporter",
  "प्रदेश प्रभारी युवा प्रकोष्ठ उत्तर प्रदेश टीम मोदी सपोर्टर एसोसिएशन",
  "Always smile😃😊",
  "༄ᶦᶰᵈ★AℑᴇᴇƬ࿐🥰×͜× 𝙰𝙻𝙾𝙽𝙴 𝙱𝙾𝚈❣️❣️ᶦᵅᶬ᭄Ꮋ𝚊𝚙𝚙y❣️❤️❤️",
  "Bhakti ben palak mota",
  "I'm Engineer that is a Revolutionary",
  "Life is hard but not impossible",
  "Nancy jewel mcdonie Nancy momo This is me",
  "Er Manas Kumar palei",
  "I am human being.",
  "President of Virat Hindustan Sangam", 
  "fmr Cabinet Minister, Six terms MP, Member BJP", 
  "Harvard Ph.D (Economics), former Professor", 
  "I give as good as I get.",
  "Slaves of beloved🍁Simplicity is the key to happiness💞",
  "CA Amit Sethi",
  "I Love my India",
  "श्री साई सिद्धी इंजिनिअरिंग वर्कशॉप",
  "ᴘᴇᴀᴄᴇ♓ᴏʀɪɢɪɴᴀʟ ᴄᴏɴᴛᴇɴᴛ🌸sɪᴍᴘʟᴇ ʙᴜᴛ sɪɢɴɪғɪᴄᴀɴᴛ❣ᴄʀᴇᴀᴛɪɴɢ ᴍʏ ᴏᴡɴ ᴡᴏʀʟᴅ✌❣ᴡᴇʟᴄᴏᴍᴇ ᴘᴜʀᴇ ʜᴇᴀʀᴛs❤",
  "Qwadriplegic",
  "!! SOMNAYA !!",
  "Beauty Girl✨💕Life is Beautiful😍🌄🌤️🌅",
  "💪हिंन्दू होना भाग्य है पर कट्टर हिंदू होना सौभाग्य है..!👑🙌📿जय श्री महाकाल🔱",
  "I hate fake people",
  "Love to Pay with Bitcoin...#nfts#crypto",
  "Journalist@ETVBharatOD👩🏻‍💻, IIMCian KIITian👩‍🎓, Photographer📲, Moody Artist☺️",
  "I am teacher",
  "Walcome to my tutter profile Love you all friends",
  "Your fitness",
  "A passionate full stack developer.",
  "Hi I am crypto lover",
  "Hé hé hé silly नमस्ते सबैमा enjoy with this Twitter forever….,!?@#ॐॐॐ॥",
  "🙏❤जय श्रीराम❤🙏",
  "BBA & MBA✍️photography & graphic designing🙋I love book reading❤️There is no friend as loyal sa friend⭐",
  "social media",
  "Nothing now",
  "Person who always finding peace nd joy in lit things✨",
  "Life is my love iam happy",
  "kolappan Ramakrishnan",
  "𝙽𝚎𝚟𝚎𝚛 𝚐𝚒𝚟𝚎 𝚞𝚙😊",
  "I have write a blog",
  "Love me? Great. Hate me? Even Better. Don’t know me? Don’t judge me",
  "शर्यत अजुन संपली नाही, कारण मी अजुन जिंकलो नाही...❓",
  "Be simple be happy",
  "Vanraj Vyas",
  "राष्ट्रीय स्वयंसेवक संघ में 10 वर्षों तक मुख्य शिक्षक तथा खंड शारीरिक प्रमुख।",
  "I love this work computer.I love this language for English.i am communicating English language",
  "LIFE IS BEAUTIFUL...SPREAD HAPPINESS",
  "Join us club",
  "Naam Sonu Singh Yadav gram Karauli post Mohanpur jila Gazipur Uttar Pradesh",
  "Medical professionals",
  "#StrongHeaded",
  "I'm business man",
  "Life is too short for bio. I'm just live instead of writing one..",
  "💮Radhe radhe💮",
  "अमीत शाह प्रतिनिधि",
  "Thala Ganesh",
  "Sports athlete",
  "Post graduate study and company job",
  "ଜୟ ଜଗନ୍ନାଥ🙏🏻",
  "I am student Army lover's",
  "Refresh your thoughts!.",
  "♔Official account SînGle👍LoGin In The World 31 Jan Simple Boy🏍📸hØlîC♍I'm not Rich ßut I'm Royal👑👍Live📿Laugh😊LoVe❤👕White Lover",
  "I am a studet",
  "Anurag Singh",
  "Polite, calm, cool",
  "BTS💜FOREVER💕",
  "Show me your NFT!",
  "Jai Hind🇮🇳🇮🇳",
  "I am a student in a college. I like usge s phone😘",
  "Born to golf while making things more arm’s length with transfer pricing😀",
  "#ShehnaazGillki Army💪#Shehnaazianforever If the world will against her I will be against the world🌍❤️",
  "Ride like a🔫gun🔥",
  "Journalist. Worked with India Tv, Ndtv, News24, India News/NewsX, Live India, Janmat, Jain Tv. RTs are not endorsement.",
  "First crying on 24 August Second crying on 24 August 2020 in love🥺I not like song, playing, that all is dependent on my mood😌",
  "Shrwan Benda bendo ka bera lohavat rajashthan",
  "Zila Parishad (Nagar Untari Prakhand)",
  "Be good! And do good !!",
  "I’ve learned I don’t know anything.  Have also learned that people will pay for what I know.  Life is good.",
  "Knowledge seeker",
  "अधिवक्ता (ADVOCATE)🚩सदैव आपके साथ🚩",
  "Never compromise with your pride",
  "MGNREGS implementation in Koppa Taluk, Chikkamagaluru Dist",
  "Proud Indian🇮🇳| Student | Tech Geek | Cricket Fan |",
  "Akhilesh Pandey",
  "I am channel sellers",
  "Actor/Teacher/MotivationalSpeaker/UN Ambassador @HeForShe/Author/Padma Shri/PadmaBhushan",
  "honestly the best policy",
  "My life my rools🤗",
  "📸YOUTUBER🎬100K+ YouTube family🇮🇳CHANNELS👇🔥(राम राज🚩)= Hindu unity❤And (Rohit Baghel)",
  "physics wallah is love",
  "Live n let others live....",
  "Cadet Krishna",
  "I am strong",
  "I m business man",
  "I love my India",
  "Technical Hook is an online plateform on YouTube where you get interesting knowledge about technology. Daily new video is uploaded on YouTube channel.",
  "Gnostic demi-demonic entity (it/they/them). Sexually identifies as an attack helicopter. Gendersolid.",
  "Option b Professional Services",
  "abel said to save my tears for another day!"
]


def random_insta_bio():
    adjectives = ['Adventurous', 'Ambitious', 'Artistic', 'Athletic', 'Bold', 'Brave', 'Carefree', 'Cheerful', 'Confident', 'Creative', 'Curious', 'Daring', 'Determined', 'Energetic', 'Enthusiastic', 'Fearless', 'Friendly', 'Fun-loving', 'Generous', 'Happy', 'Helpful', 'Honest', 'Humorous', 'Inquisitive', 'Inspiring', 'Intelligent', 'Joyful', 'Kind', 'Loyal', 'Motivated', 'Optimistic', 'Passionate', 'Positive', 'Resilient', 'Resourceful', 'Sociable', 'Spontaneous', 'Strong', 'Successful', 'Thoughtful', 'Trustworthy', 'Unconventional', 'Unique', 'Versatile', 'Witty']

    # List of nouns
    nouns = ['Adventurer', 'Artist', 'Athlete', 'Dreamer', 'Explorer', 'Foodie', 'Gamer', 'Hiker', 'Innovator', 'Lover', 'Musician', 'Nomad', 'Optimist', 'Photographer', 'Reader', 'Runner', 'Traveler', 'Writer']

    # List of interests
    interests = ['Adventure', 'Art', 'Books', 'Coffee', 'Comedy', 'Cooking', 'Dancing', 'Fitness', 'Food', 'Gaming', 'Hiking', 'Music', 'Nature', 'Photography', 'Science', 'Sports', 'Technology', 'Travel']

    # List of emojis
    emojis = ['🌟', '🌻', '🍂', '🎨', '🎬', '🎭', '🎶', '🎸', '🎮', '🏀', '🏂', '🏊', '🏋', '🏕', '🐶', '🐱', '🐻', '🐝', '🐠', '🐦', '🐬', '🌊', '🌍', '🌞', '🌲', '🍕', '🍔', '🍟', '🍩', '🍭', '🍺', '🍷', '🍹', '🍻', '🎁', '🎉', '🎊', '🎖', '🏆', '🏅', '🏵', '💻', '💡', '💪', '👀', '👨‍💻', '👩‍💻', '👩‍🎓', '👨‍🎓', '👩‍🔬', '👨‍🔬', '👩‍🚀', '👨‍🚀', '🌈']
    bio = ""
    # Add an adjective
    bio += random.choice(adjectives)
    # Add a noun
    bio += "\n" + random.choice(nouns)
    # Add an interest
    bio += "\n" + random.choice(interests)
    # Add an emoji
    bio += " " + random.choice(emojis)
    return bio

NEW_INSTA_ACC_BIO = random_insta_bio()

