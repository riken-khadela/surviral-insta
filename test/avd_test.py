

from appium import webdriver
from appium import webdriver
from selenium.webdriver.common.by import By
import time,subprocess,random,requests
from appium.webdriver.common.touch_action import TouchAction
from selenium.common.exceptions import NoSuchElementException, TimeoutException,InvalidElementStateException,InvalidSessionIdException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from thispersondoesnotexist import Person
import os, cv2, random,threading
from deepface import DeepFace
import shutil

CURRENT_PC_NAME = os.getenv('PCNAME')

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

def run_cmd(cmd, verbose=True):
    """Run shell commands, and return the results

    ``cmd`` should be a string like typing it in shell.
    """
    try:
        if verbose:
            print(f'Command: {cmd}')

        r = subprocess.run(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, shell=True, text=True)

        if verbose:
            if r.returncode == 0:
                print(f'Successful to run the command: {cmd}')
                print(f'Result of the command: {r.stdout}')
            else:
                print(f'Failed to run the command: {cmd}')
                print(f'Result of the command: {r.stdout}')

        return r.returncode, r.stdout
    except Exception as e:
        print(e)

def copy_img(img_name='',source_file ='',destination_folder='') :
    destination_path = destination_folder + img_name
    shutil.copy(source_file, destination_path)

def add_profile_img():
    for _ in range(10):
        person = Person(fetch_online=True)
        person.save(os.path.join(os.getcwd(),'profile_pic/checkimg.jpeg'))
        img = cv2.imread(os.path.join(os.getcwd(),'profile_pic/checkimg.jpeg'))
        result = DeepFace.analyze(img,actions=("gender"))
        destination_folder = ''
        if result[0]['dominant_gender'] == "Woman" :
            destination_folder = os.path.join(os.getcwd(),'profile_pic/female/')
        elif result[0]['dominant_gender'] == "Man" :
        # else :
            destination_folder = os.path.join(os.getcwd(),'profile_pic/male/')
        if destination_folder :
            print(result[0]['dominant_gender'])
            copy_img(img_name=f'{random.randint(1000,100000000)}.jpeg',source_file=os.path.join(os.getcwd(),'profile_pic/checkimg.jpeg'),destination_folder=destination_folder)


def get_image_for_create_account(gender : str):
    gender = gender.lower()
    folder_path = os.path.join(os.getcwd(),f"profile_pic/{gender}")

    # Get a list of all files in the folder
    files_in_folder = os.listdir(folder_path)
    if len(files_in_folder) <= 20 :
        add_profile_img()
    return os.path.join(os.getcwd(),f"profile_pic/{gender}/{random.choice(files_in_folder)}") 


timeout = 10
class bot():

    def __init__(self,emulator_name,adb_console_port):
        self.emulator_name = emulator_name
        self.adb_console_port = adb_console_port
        self.work()
    
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
                wait_obj = WebDriverWait(self.driver, timeout)
                ele = wait_obj.until(
                         EC.presence_of_element_located(
                             (locator_type, locator)))
            else:
                print(f'Timeout is less or equal zero: {timeout}')
                ele = self.driver.find_element(by=locator_type,
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
                wait_obj = WebDriverWait(self.driver, timeout)
                ele = wait_obj.until(
                         EC.presence_of_all_elements_located(
                             (locator_type, locator)))
            else:
                print(f'Timeout is less or equal zero: {timeout}')
                ele = self.driver.find_elements(by=locator_type,
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
                try:self.driver.hide_keyboard()
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

    def profile_img_download(self):
        '''
        downloading the file and saving it in download folder
        '''
        
        profile_pic_path = get_image_for_create_account(self.user_gender)
        run_cmd(f'adb -s emulator-{self.adb_console_port} push {profile_pic_path} /sdcard/Download')
        if os.path.exists(profile_pic_path):
            os.remove(profile_pic_path)
            # '/home/dell/workspace2/auto_gender_definer/profile_pic/male/26423157.jpeg'
            print(f"File '{profile_pic_path}' has been successfully removed.")
        else:
            print(f"The file '{profile_pic_path}' does not exist.")

    def add_profile_pic(self,gender):
        self.user_gender = gender
        self.click_element('profile button','//android.widget.FrameLayout[@content-desc="Profile"]/android.view.ViewGroup')
        self.click_element('Edit profile','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.LinearLayout/android.widget.Button[1]/android.widget.FrameLayout/android.widget.Button')
        self.click_element('Create avatar cancle','com.instagram.android:id/negative_button',By.ID)
        self.click_element('Change avatar button','com.instagram.android:id/change_avatar_button',By.ID)
        self.click_element('click on add_rofile','//android.view.ViewGroup[@content-desc="New profile picture"]')
        self.click_element('Gallary btn','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.TabWidget/android.widget.TextView[1]')
        self.click_element('gallary folder menu','com.instagram.android:id/gallery_folder_menu',By.ID)
        self.click_element('Other ...','/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[2]/android.widget.FrameLayout/android.view.ViewGroup/android.widget.FrameLayout/android.view.ViewGroup/androidx.recyclerview.widget.RecyclerView/android.widget.Button[2]')
        self.profile_img_download()
        self.click_element('Show roots','//android.widget.ImageButton[@content-desc="Show roots"]',timeout=15)
        self.click_element('download','/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.view.ViewGroup/android.support.v4.widget.DrawerLayout/android.widget.LinearLayout[2]/android.widget.FrameLayout/android.widget.ListView/android.widget.LinearLayout[2]/android.widget.LinearLayout')
        self.click_element('choose pic','com.android.documentsui:id/icon_thumb',By.ID)
        self.click_element('next btn','com.instagram.android:id/save',By.ID,timeout=30)
        self.click_element('next_button_imageview','com.instagram.android:id/next_button_imageview',By.ID)
        time.sleep(15)

        return True
    
    def get_driver(self):
        
        
        capabilities= {
            "platformName": "Android",
                        #  "platformVersion": "9.0",    # comment it in order to use other android version
                        "automationName": "uiautomator2",
                        "noSign": True,
                        "noVerify": True,
                        "ignoreHiddenApiPolicyError": True,
                        "newCommandTimeout": 120,  # Don't use this
                        #"systemPort": "8210",
        }
        self.driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub",capabilities)

    def work(self):
        self.get_driver()
        self.add_profile_pic('male')
        breakpoint()
        print('work completed !')
bot('instagram_5951',5646)