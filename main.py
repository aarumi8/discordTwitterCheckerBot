import json
from time import sleep
import random
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions


def init_driver(headless=True, proxy=None, show_images=False):
    """ initiate a chromedriver instance """

    # create instance of web driver
    #chromedriver_path = chromedriver_autoinstaller.install()
    #options = Options()
    options = FirefoxOptions()
    #options.add_argument("user-data-dir=selenium")
    if headless is True:
        print("Scraping on headless mode. KEKE")
        options.add_argument('--disable-gpu')
        options.add_argument('window-size=1920x1080')
        options.headless = True
    else:
        options.headless = False
    options.add_argument('log-level=3')
    if proxy is not None:
        options.add_argument('--proxy-server=%s' % proxy)
    #if show_images == False:
    	#prefs = {"profile.managed_default_content_settings.images": 2}
    	#options.add_experimental_option("prefs", prefs)

    #driver = webdriver.Chrome(options=options, executable_path=chromedriver_path)
    
    # your firefox profile where your twitter account is logged in and cached(about:profiles in firefox search bar)
    ffprofile = webdriver.FirefoxProfile(
        './axyqdd0e.default-release')

    driver = webdriver.Firefox(firefox_profile=ffprofile, options=options)
    driver.set_window_position(0, 0)
    driver.set_window_size(900, 768)
    driver.set_page_load_timeout(100)
    return driver


def log_in(driver, timeout=10):
    username = '' # your twitter login
    password = '' # your twitter password

    driver.get('https://www.twitter.com/login')
    username_xpath = '//input[@name="session[username_or_email]"]'
    password_xpath = '//input[@name="session[password]"]'

    username_el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, username_xpath)))
    password_el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, password_xpath)))

    username_el.send_keys(username)
    password_el.send_keys(password)
    password_el.send_keys(Keys.RETURN)


def check_exists_by_link_text(text, driver):
    try:
        driver.find_element_by_link_text(text)
    except NoSuchElementException:
        return False
    return True


def get_users_follow(users, headless, follow=None, verbose=1, wait=2):
	""" get the following or followers of a list of users """

	# initiate the driver
	driver = init_driver(headless=headless)
	sleep(wait)
	# log in (the .env file should contain the username and password)
	#log_in(driver)
	sleep(wait)
	# followers and following dict of each user
	follows_users = {}

	for user in users:
	    # log user page
	    print("Crawling @" + user + " " + follow)
	    driver.get('https://twitter.com/' + user + '/following')
	    sleep(random.uniform(wait-0.5, wait+0.5))
	    # find the following or followers button
	    #driver.find_element_by_xpath('//a[contains(@href,"/' + follow + '")]/span[1]/span[1]').click()
	    sleep(random.uniform(wait-0.5, wait+0.5))
	    # if the log in fails, find the new log in button and log in again.
	    if check_exists_by_link_text("Log in", driver):
	        login = driver.find_element_by_link_text("Log in")
	        sleep(random.uniform(wait-0.5, wait+0.5))
	        driver.execute_script("arguments[0].click();", login)
	        sleep(random.uniform(wait-0.5, wait+0.5))
	        driver.get('https://twitter.com/' + user)
	        sleep(random.uniform(wait-0.5, wait+0.5))
	        driver.find_element_by_xpath(
	            '//a[contains(@href,"/' + follow + '")]/span[1]/span[1]').click()
	        sleep(random.uniform(wait-0.5, wait+0.5))
	    # check if we must keep scrolling
	    scrolling = True
	    last_position = driver.execute_script("return window.pageYOffset;")
	    follows_elem = []
	    follow_ids = set()

	    while scrolling:
	        # get the card of following or followers
	        page_cards = driver.find_elements_by_xpath(
	            '//div[contains(@data-testid,"UserCell")]')
	        for card in page_cards:
	        	# get the following or followers element
	            element = card.find_element_by_xpath(
	                './/div[1]/div[1]/div[1]//a[1]')
	            follow_elem = element.get_attribute('href')
	            # append to the list
	            follow_id = str(follow_elem)
	            follow_elem = str(follow_elem).split('/')[-1]
	            if follow_id not in follow_ids:
	            	follow_ids.add(follow_id)
	            	follows_elem.append(follow_elem)
	            if verbose:
	                print(follow_elem)
	        print("Found " + str(len(follows_elem)) + " " + follow)
	        scroll_attempt = 0
	        while True:
	            sleep(random.uniform(wait-0.5, wait+0.5))
	            driver.execute_script(
	                'window.scrollTo(0, document.body.scrollHeight);')
	            sleep(random.uniform(wait-0.5, wait+0.5))
	            curr_position = driver.execute_script(
	                "return window.pageYOffset;")
	            if last_position == curr_position:
	                scroll_attempt += 1

	                # end of scroll region
	                if scroll_attempt >= 3:
	                    scrolling = False
	                    break
	                    #return follows_elem
	                else:
	                    # attempt another scroll
	                    sleep(random.uniform(wait-0.5, wait+0.5))
	            else:
	                last_position = curr_position
	                break

	    follows_users[user] = follows_elem

	driver.quit()

	return follows_users


def get_users_following(users, verbose=1, headless=True, wait=2):

    following = get_users_follow(
        users, headless, "following", verbose, wait=wait)

    return following


def get_users():
    with open("users.json", "r") as jsonFile:
        data = json.load(jsonFile)
    return data


def add_user(user):
    users = [user]
    following = get_users_following(
        users=users, verbose=0, headless=True, wait=1)

    with open("old_state/" + user + ".json", "w") as jsonFile:
        json.dump(following[user], jsonFile)

    users = get_users()
    users.append(user)

    with open("users.json", "w") as jsonFile:
        json.dump(users, jsonFile)


def update_following():
    users = get_users()
    following = get_users_following(
        users=users, verbose=0, headless=True, wait=1)

    for user in users:
        with open("current_state/" + user + ".json", "w") as jsonFile:
            json.dump(following[user], jsonFile)


def compare_user_following():
    users = get_users()

    for user in users:
        with open("old_state/" + user + ".json", "r") as jsonFile:
            old_state = json.load(jsonFile)

        with open("current_state/" + user + ".json", "r") as jsonFile:
            current_state = json.load(jsonFile)

        new_following = list(set(current_state) - set(old_state))

        with open("new_following/" + user + ".json", "w") as jsonFile:
            json.dump(new_following, jsonFile)

        with open("old_state/" + user + ".json", "w") as jsonFile:
            json.dump(current_state, jsonFile)

def get_new_following():
    users = get_users()
    result = []

    for user in users:
        with open("new_following/" + user + ".json", "r") as jsonFile:
            data = json.load(jsonFile)

        if len(data) > 0:
            result_data = ""

            for item in data:
                item = "<https://twitter.com/" + item + ">"
                result_data = result_data + item + "\n"

            result.append("<https://twitter.com/" + user + ">" + " is following new accounts:\n" + result_data)
    
    return result 


from discord.ext import commands

TOKEN = "" # your discord token 

bot = commands.Bot(command_prefix="/")

@bot.command(name="add")
async def add_user_message(ctx, arg):
    await ctx.channel.send(arg + " is adding...")
    add_user(arg)
    await ctx.channel.send(arg + " is added!")

@bot.command(name="update")
async def update_users_following_message(ctx):
    await ctx.channel.send("The updating is in process. The results will be available soon.")
    update_following()
    compare_user_following()
    await ctx.channel.send("Updated! Reading results...")

    result = get_new_following()

    if len(result) > 0:
        for res in result:
            await ctx.channel.send(res)
    else:
        await ctx.channel.send("No one has subscribed to anyone recently :(")

bot.run(TOKEN)
