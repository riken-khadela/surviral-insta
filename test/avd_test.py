

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
def random_sleep(min_sleep_time=1, max_sleep_time=5,reason=""):
    sleep_time = random.randint(min_sleep_time, max_sleep_time)
    if reason :
        print(f'Random sleep: {sleep_time} for {reason}')
    else :
        print(f'Random sleep: {sleep_time}')
    time.sleep(sleep_time)
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
                wait_obj = WebDriverWait(self.driver, timeout)
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
            action = TouchAction(self.driver)
            action.tap(x=x, y=y).perform()
        except Exception as e:
            print(e)

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
        self.click_element('Edit profile','(//android.widget.FrameLayout[@resource-id="com.instagram.android:id/button_container"])[1]')
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
    

    def Follow(self):
        FollowBtn = self.find_element('Follow btn','com.instagram.android:id/profile_header_follow_button',By.ID)
        if FollowBtn.text != 'Following': FollowBtn.click()


    def search_user(self,Username):
        self.click_element('Search btn','com.instagram.android:id/search_tab',By.ID)
        self.click_element('Search input','com.instagram.android:id/action_bar_search_edit_text',By.ID)
        if not self.find_element('Search input','com.instagram.android:id/action_bar_search_edit_text',By.ID):
            for i in range(2):
                self.click_element('Back','com.instagram.android:id/action_bar_button_back',By.ID,timeout=5)
        self.input_text(Username,'Search input','com.instagram.android:id/action_bar_search_edit_text',By.ID)
        time.sleep(3)
        search_results = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//*[@resource-id='com.instagram.android:id/row_search_user_username']")))
        if search_results:
            for i in search_results:
                if str(i.text).lower() == str(Username).lower():
                    i.click()
                    break
        elif self.click_element('see all result','//android.widget.Button[@text="See all results"]'):
            time.sleep(2)
            self.click_element('account','//android.widget.TabWidget[@content-desc="Accounts"]')
            search_results = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH,f"//*[@resource-id='com.instagram.android:id/row_search_user_username' and @text='{Username}']")))
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
                action = TouchAction(self.driver)
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
            action = TouchAction(self.driver)
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
        random_sleep(8,10) 
        self.swip_display(9)

    def ReelsView(self,reels_watch_time=1):
        self.swip_display(4)
        self.click_element('Reels','//android.widget.ImageView[@content-desc="Reels"]')
        for i in range(3):
            self.click_element('First reel','(//android.widget.ImageView[@content-desc="Reel by xanametaverse. Double tap to play or pause."])[1]')
            for _ in range(int(reels_watch_time)):
                self.ChangeReels()
            self.driver().back()

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
        # self.follow_rio()
        self.search_user('xanametaverse')

        # self.EngagementOnUser()
        breakpoint()
        self.ReelsView()
        multiple_users = ["imanijohnson132","niamwangi63","lucamoretti6445","malikrobinson726","tylerevans2913","1aaliyahbrown","4nanyashah","haileymitchell161","tianaharris554","deandrewashington652","minjipark11","haraoutp","rayaanhakim"]
        for Username_multiple in multiple_users :
            try :
                self.search_user(Username_multiple)
                self.Follow()
                self.EngagementOnUser(share=False)
            except : ...
        # self.add_profile_pic('male')
        breakpoint()
        print('work completed !')
bot('instagram_5951',5646)