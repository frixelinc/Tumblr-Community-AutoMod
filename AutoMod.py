import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from os import path
import sys
from pathlib import Path
import time
from datetime import datetime

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

def printstr(string: str):
    print(str(string))

class Automod:
    
    def __init__(self, community_url: str="https://www.tumblr.com/communities/api-test-v2", bot_emoji_count_thresh: int=1, poll_freq: int=30): #poll_freq in seconds
        self.driver = webdriver.Firefox()
        self.login_url = "https://www.tumblr.com/login"
        self.cookie_file = "./cookies.pkl"
        self.cookies = None
        self.community_url = community_url
        self.login_attempt = 0
        self.delay = 30 # seconds
        self.post_elements_dict = {}
        self.bot_emoji_count_thresh = bot_emoji_count_thresh
        self.poll_freq = poll_freq
        self.post_elm_dict_date = datetime.now().strftime("%b %d")

        #CSS SELECTOR filters (private)
        self._post_elm_fltr = "div[class = 'rZlUD KYCZY F4Tcn']"
        self._post_more_opts_fltr = "button[aria-label='More options']"
        self._mod_post_dialog_fltr = "div[class='fxR1V Q895s RqV78']"
        self._mod_post_menu_buttons_fltr = "button[role='menuitem']"
        self._post_mod_reason_opts_fltr = "label[class='fBQsy']"
        self._post_mod_other_reason_fltr = "input[name='other']"
        self._post_mod_note_fltr = "textarea[class='F0gXR']"
        self._post_mod_remove_post_fltr = "button[class='VmbqY r21y5 Li_00 Lp50M JxZa0']"

        self._run_automod = False


        
        
    def get_login_cookie(self, auto_login_using_cookie: bool=False):
        self.driver.get(self.login_url)
        if path.isfile(self.cookie_file):
            self.cookies = pickle.load(open(self.cookie_file, "rb"))
            print("Loaded cookie file...")
            if auto_login_using_cookie:
                return self.load_login_cookie()
            return True
        else:
            print("Unable to locate cookie file: " + self.cookie_file + " Would you like to manually login to your account to save credential as cookie...")
            self.user_login()
            print("Trying to load cookie again...")            
            self.get_login_cookie(auto_login_using_cookie)
    
    def manual_login(self, reason: int=0):
        resp = None
        if reason == 0: #no cookie file
            resp = input("Unable to locate cookie file: " + self.cookie_file + " Would you like to manually login to your account to save credential as cookie? Enter (y) for yes and (n) for no:")
        elif reason == 1:
            resp = input("Would you like to manually login and resave your cookies? Enter (y) for yes and (n) for no: ")
        else:
            print('Invalid manual login reason: %i \n Program quitting...' % reason)
            sys.exit(1)
            
        if resp is not None:
            if resp.upper() == 'Y':
                self.user_login()
                return True
            elif resp.upper() == 'N':
                print('Quitting program without login...')
                sys.exit(1)
            else:
                resp = input('Invalid response...Press (q) to quit: ')
                if resp.upper() == 'q':
                    return False
                else:
                    self.manual_login(reason)
                
        
        
    def load_login_cookie(self):
        for cookie in self.cookies:
            self.driver.add_cookie(cookie)
        self.driver.refresh()
        
        if self.driver.current_url == "https://www.tumblr.com/dashboard":
            print("Login using cookie Successful!")
            self.login_attempt = 0
            return True
        else:
            print("Login failed")
            if self.login_attempt < 3:
                self.login_attempt+=1
                print('Retrying login attempt: ' + str(self.login_attempt))
                if self.cookies is None:
                    self.get_login_cookie(True)
                else:
                    self.load_login_cookie()
                #self.load_login_cookie()
            else:
                print("Attempted login 3 times using cookie and failed.")
                if(self.manual_login(1)):
                    if self.driver.current_url != "https://www.tumblr.com/dashboard":
                        return self.get_login_cookie(True)
                    else:
                        return True

    
    def user_login(self):
        if self.driver.current_url != self.login_url:
            self.driver.get(self.login_url)
        while input("Waiting on user login. Enter (d) once done: ").upper() != 'D':
            pass
        pickle.dump(self.driver.get_cookies(), open(self.cookie_file, "wb"))
    
    def close_driver(self):
        self.driver.quit()
        
    def get_driver(self):
        return self.driver
    
    def implicit_css_elm_wait(self, filter: str):
        try:
            myElem = WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, filter)))
            return True
        except TimeoutException:
            print("Loading took too much time to load element with CSS Selector filter: %s" % filter)
            return False
        
    def get_todays_posts(self):
        self.driver.get(self.community_url)
        ''''
        try:
            myElem = WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, self._post_elm_fltr)))
            print("Page is ready!")
        except TimeoutException:
            print("Loading took too much time!")
            return False
        '''
        if not self.implicit_css_elm_wait(self._post_elm_fltr):
            print('Community Timeline took too long to load / issue with program retrieving post data')
            return False
            
        post_elements = self.driver.find_elements(By.CSS_SELECTOR, self._post_elm_fltr)
        
        dt_now = datetime.now()
        dt_now_str = dt_now.strftime("%b %d")
        if dt_now_str is not self.post_elm_dict_date:
            self.post_elements_dict = {}

        for element in post_elements:
            post_id = element.get_attribute('data-cell-id').split('-')[2]
            post_date = element.text.split('\n')[2]
            print(post_date)
            if post_date == dt_now_str or post_date[-1] == 's' or post_date[-1] == 'm' or post_date[-1] == 'h':
                self.post_elements_dict[post_id] = element
    
    def parse_element_text_for_bot_emoji(self, post_id: str):
        element = self.post_elements_dict[post_id]
        element_text = element.text
        if '🤖' in element_text:
            element_text_list = element_text.split('\n')
            ind = element_text_list.index('🤖')
            bot_emoji_count = int(element_text_list[ind+1])
            if bot_emoji_count >= self.bot_emoji_count_thresh:
                self.delete_post_action(post_id)
                #return True
    
    
    def parse_for_deletion(self):
        for post_id, post_elm in self.post_elements_dict.items():
            self.parse_element_text_for_bot_emoji(post_id)

    def start_automod_monitor(self):
        #self._run_automod = True
        while True:
            self.driver.get(self.community_url)
            self.get_todays_posts()
            self.parse_for_deletion()
            time.sleep(self.poll_freq)

    def stop_automod_monitor(self):
        self._run_automod = False
    


    def open_moderate_post(self):
        try:
            menubutton_elm = self.driver.find_elements(By.CSS_SELECTOR, self._mod_post_menu_buttons_fltr)
            moderate_post_btn_elm = [elm for elm in menubutton_elm if elm.text == 'Moderate post'][0]
            moderate_post_btn_elm.click()

            mod_post_dialog = self.driver.find_element(By.CSS_SELECTOR, self._mod_post_dialog_fltr)
            return True
        except Exception as e:
            if e is NoSuchElementException:
                print('Moderate Post Dialog Box is not avaliable. Could not proceed further.')
            else:
                print('Encountered Exception while opening Moderate Post dialog box: ' + str(e))
            return False
    
    def moderate_post(self):
        try:
            reason_option_elements = self.driver.find_elements(By.CSS_SELECTOR, self._post_mod_reason_opts_fltr)
                            
            other_reason_element = [elm for elm in reason_option_elements if elm.find_elements(By.CSS_SELECTOR, "input[name='other']")][0]
            
            
            if other_reason_element is not None:
                other_reason_element.click()

            note_elm = self.driver.find_element(By.CSS_SELECTOR, self._post_mod_note_fltr)
            note_elm.send_keys('Auto-Moderated Post: This post has been automatically removed due recieving %i or more 🤖 reaction from the community. If this is a mistake, please contact the mods of Frogblr' % 1)
            remove_post_elm = self.driver.find_element(By.CSS_SELECTOR, self._post_mod_remove_post_fltr)
            remove_post_elm.click()

            return True
        except Exception as e:
            if e is NoSuchElementException:
                print('Failed to get element while on Moderate Post dialog exception.' )
            else:
                print('Encountered Exception while on Moderate Post dialog.')

            print('Exception: ' + str(e) )
            return False 
            
    def delete_post_action(self, post_id: str):
        try:
            post_elm = self.post_elements_dict[post_id]
            option_button = post_elm.find_element(By.CSS_SELECTOR, "button[aria-label='More options']")
            self.driver.execute_script("arguments[0].scrollIntoView();", option_button)
            option_button.click()
            if self.open_moderate_post():
                if self.moderate_post():
                    return True
                else:
                    return True
            else:
                return False
                print('Encountered Exception while on Moderate Post dialog.')
        except Exception as e:
            print('Encountered Exception while on Moderate Post dialog.')
            if e is NoSuchElementException:
                print('More Options button for the following post ID could not be found: ' + post_id)
            elif e is KeyError:
                print('Post element for following post ID could not be found: ' + post_id)
            else:
                print('Encountered Exception while attemtping to delete post with following post ID: ' + post_id)
                print('Exception: ' + str(e) )
            return False 


                
            
                


