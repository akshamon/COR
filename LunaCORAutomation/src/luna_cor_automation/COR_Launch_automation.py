# ------------------------------------------------------------------------
# Author(s): 
#   Priyanka Yadav, 
#   Michael A. Colon
# ------------------------------------------------------------------------
# TODO:
#   Make script less error prone.
#       Replace keyboard inputs with direct references (if possible), test_cor_launch().
#       Add handling for errors while logged in, id=item_game_detail_fallback_message
#       (Mostly Fixed) Add handling for when game is already launched and session is resumed instead 
#           of started.
#   Investigate issue where CTRL keys do not function while test is running.
# ------------------------------------------------------------------------

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from enum import Enum
from getpass import getpass
from colorama import Fore, init
from os import path, makedirs

import datetime
import time
import cv2


class Country(Enum):
    US = 0
    CA = 1
    GB = 2
    DE = 3

class LogType(Enum):
    NONE = 0
    ERROR = 1
    IO = 2
    INFO = 3

fake_controller = """
    window.navigator.getGamepads = () =>
        [
            {
                axes: [0.01, 0.01, 0.02, 0.04],
                buttons: [
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 },
                    { pressed: false, value: 0 }
                ],
                connected: true,
                id: 'Xbox Wireless Controller (STANDARD GAMEPAD Vendor: 045e Product: 02fd)',
                index: 0,
                mapping: 'standard',
                timestamp: 177550
            }
        ]
"""

driver_luna: webdriver
action: ActionChains
commands_us = [Keys.ENTER]
commands_ca = [Keys.ARROW_DOWN, Keys.ENTER]
commands_gb = [Keys.ARROW_DOWN, Keys.ARROW_DOWN, Keys.ENTER]
commands_de = [Keys.ARROW_DOWN, Keys.ARROW_DOWN, Keys.ARROW_DOWN, Keys.ENTER]

timeout_wait = 30
long_timeout_wait = 180
step_sleep_time = 4
default_result_screenshot_wait = 60
implicit_wait = 5 # Added for ease of modifying value without digging through code
result_screenshot_wait = default_result_screenshot_wait
black_image_reattempts = 3

game_id = ""
retry_launch = False


def main():
    global driver_luna
    global action
    global game_id
    global result_screenshot_wait

    init(autoreset=True)

    email = input('Please enter your account email: ')
    password = getpass('Please enter your account password: ')
    while game_id == "":
        game_id = input('Please enter the game ID: ')
    game_id = game_id.strip()

    # Country Selection
    print("Which countries would you like to test? Leave blank or type 'ALL' and hit enter for all of them.")
    print("     Acceptable country inputs (case insensitive): US, CA, GB, DE")
    tested_countries_str = input('     Example to test Canada and Germany: CA DE \n')
    tested_countries = get_country_list(tested_countries_str)

    temp_str = ""
    for country in tested_countries:
        temp_str += " " + country.name

    if temp_str == "":
        print_msg("Selected countries are: None", LogType.INFO)
    else:
        print_msg("Selected countries are:" + temp_str, LogType.INFO)

        # Image capture time input
        try:
            result_screenshot_wait = int(input("How many seconds after launch for a screenshot?: "))

            if result_screenshot_wait <= 0:
                result_screenshot_wait = default_result_screenshot_wait
                print_msg("Invalid input. Only enter integer numbers above 0! Defaulting to " + str(
                    default_result_screenshot_wait) + " seconds.", LogType.ERROR)
        except:
            result_screenshot_wait = default_result_screenshot_wait
            print_msg("Invalid input. Only enter integer numbers above 0! Defaulting to " + str(
                default_result_screenshot_wait) + " seconds.", LogType.ERROR)
        
        driver_luna = webdriver.Chrome()
        driver_luna.implicitly_wait(implicit_wait)
        action = ActionChains(driver_luna)
        
        print_msg("Beginning test run for GameID: " + game_id, LogType.INFO)
        print_msg("Attempting to login...", LogType.INFO)
        driver_luna.get("https://luna.amazon.com/settings")
        driver_luna.find_element(By.ID, "ap_email").send_keys(email)
        driver_luna.find_element(By.ID,"ap_password").send_keys(password)
        driver_luna.find_element(By.ID, "signInSubmit").click()

        time.sleep(step_sleep_time)
        x_list = driver_luna.find_elements(By.ID, "auth-error-message-box")
        if len(x_list) > 0:
            print_msg("Incorrect login information!", LogType.ERROR)
        else:
            #item_current_session_takeover
            x_list = driver_luna.find_elements(By.ID, "item_current_session_takeover")
            if len(x_list) > 0:
                print_msg("Account is already in use!", LogType.ERROR)
            else:
                for country in tested_countries:
                    test_cor_launch(country)
                    if retry_launch:
                        test_cor_launch(country)

                print_msg("Tests completed. Check saved images in the script folder for results.", 
                    LogType.INFO)

    input("Press enter to continue...\n\n\n")


def test_cor_launch(cor: Country):
    global retry_launch
    retry_launch = False

    used_commands = []
    cor_name = ""

    if cor == Country.CA:
        used_commands = commands_ca
        cor_name = "COR-CA"
    elif cor == Country.GB:
        used_commands = commands_gb
        cor_name = "COR-GB"
    elif cor == Country.DE:
        used_commands = commands_de
        cor_name = "COR-DE"
    else:
        used_commands = commands_us
        cor_name = "COR-US"
    
    global game_id
    if game_id == "":
        print_msg("Error: Blocking issue found. Skipping " + cor_name + " test.", LogType.ERROR)
        return

    try:
        driver_luna.get("https://luna.amazon.com/settings")
        time.sleep(3)
        WebDriverWait(driver_luna, timeout_wait).until(EC.presence_of_element_located((By.ID, 
            "collection_sub_nav_settings")))
        driver_luna.find_element(By.XPATH, 
            value='//*[@id="collection_sub_nav_settings"]/div/nav/ol/div[7]/div').click()
        time.sleep(step_sleep_time)
        
        print_msg("Selecting COR...", LogType.INFO)

        # Possible area to replace key inputs with direct references
        driver_luna.find_element(By.ID,'react-select-2-input').send_keys(Keys.ARROW_DOWN, 
            Keys.ENTER)
        driver_luna.find_element(By.ID,'react-select-3-input').send_keys(used_commands)

        save_image(game_id + "_" + cor_name + '-Language')

        if visit_game_page(game_id) == False:
            print_msg("Error: The specified game ID is not found in the library! Skipping " 
                + cor_name + " test.", LogType.ERROR)
            game_id = ""
            return
        
        if attempt_game_launch(cor_name) == False:
            print_msg("Game failed to launch!", LogType.ERROR)
            save_image(game_id + "_" + cor_name + "_LaunchError")
            reset()
            return
        
        WebDriverWait(driver_luna, long_timeout_wait).until(EC.presence_of_element_located((
            By.CLASS_NAME, "_1fisdfa")))
        print_msg("Game launch detected! Taking screenshot in " + str(result_screenshot_wait) 
            + " seconds.", LogType.INFO)
        time.sleep(result_screenshot_wait)

        # Reattempts for a non-black based on black_image_reattempts value
        colored_image_taken = False
        for attempt in range(black_image_reattempts):
            image_file_path = save_image(game_id + "_" + cor_name + '-Result')
            if image_file_path != "":
                image = cv2.imread(image_file_path, 0)

                if cv2.countNonZero(image) == 0:
                    print_msg("Captured image is detected to be fully black. Reattempting image capture in " +
                        str(step_sleep_time) + " seconds..." , LogType.ERROR)
                    print_msg("Remaining reattempts: " + str(black_image_reattempts - (attempt + 1)), LogType.INFO)
                    time.sleep(step_sleep_time)
                else:
                    colored_image_taken = True
                    break
        
        if colored_image_taken == False:
            print_msg("All obtained images are black! Continuing to next test...", LogType.ERROR)
        
        quit_session()

    except TimeoutError:
        print_msg(cor_name + " test failed due to script timeout!", LogType.ERROR)
        save_image(game_id + "_" + cor_name + '-Error')
        reset()
    except:
        print_msg(cor_name + " test failed due to script error!", LogType.ERROR)
        save_image(game_id + "_" + cor_name + '-Error')
        reset()


# returns false if it fails to find the game
def visit_game_page(id: str) -> bool:
    print_msg("Attempting to visit game page...", LogType.INFO)
    time.sleep(step_sleep_time)
    driver_luna.find_element(By.ID,'item_nav_library').click()
    WebDriverWait(driver_luna, timeout_wait).until(EC.presence_of_element_located((By.ID, 
        "collection_library_certifier")))
    
    x_list = driver_luna.find_elements(By.ID, "game_tile_" + id)
    if len(x_list) < 1:
        return False
    
    driver_luna.find_element(By.ID, "game_tile_" + id).click()

    return True


def attempt_game_launch(cor_name: str) -> bool:
    global game_id
    global retry_launch

    driver_luna.execute_script(fake_controller)

    print_msg("Attempting to launch the game...", LogType.INFO)
    time.sleep(step_sleep_time)
    x_list = driver_luna.find_elements(By.ID, "start_game_session__action")
    if len(x_list) < 1:
        print_msg("Unable to find launch button.", LogType.ERROR)
        return False
    else:
        driver_luna.find_element(By.ID ,"start_game_session__action").click()
    
    time.sleep(step_sleep_time)
    x_list = driver_luna.find_elements(By.ID, "controller_required_modal")
    if len(x_list) > 0:
        print_msg("Controller faking failed! Controller isn't connected! Skipping " 
            + cor_name + " test.", LogType.ERROR)
        game_id = ""
        return False
    
    x_list = driver_luna.find_elements(By.CLASS_NAME, "_1fisdfa")
    if len(x_list) > 0:
        print_msg("Detected pre-existing game session.", LogType.ERROR)
        retry_launch = True
        return False

    # Not detecting for some reason
    x_list = driver_luna.find_elements(By.ID, "item_game_session_error_account_max_streams")
    if len(x_list) > 0:
        print_msg("Account is already in use. Skipping " + cor_name + " test.", LogType.ERROR)
        game_id = ""
        return False

    driver_luna.fullscreen_window()
    
    time.sleep(step_sleep_time)
    if driver_luna.find_element(By.ID, "abandon_button"):
        return True
    elif driver_luna.find_element(By.ID, "item_primary_game_detail_button"):
        return False
    else:
        WebDriverWait(driver_luna, step_sleep_time).until(EC.presence_of_element_located((By.ID, 
            "abandon_button")))
        
        if driver_luna.find_element(By.ID, "abandon_button"):
            return True

        return False


def quit_session():
    print_msg("Quitting the game session...", LogType.INFO)
    time.sleep(step_sleep_time)
    action.key_down(Keys.LEFT_SHIFT).send_keys(Keys.TAB).key_up(Keys.LEFT_SHIFT).perform()
    time.sleep(step_sleep_time)
    driver_luna.find_element(By.CLASS_NAME, '_1ux6cvw').click()
    driver_luna.find_element(By.CLASS_NAME, '_49x36f').click()
    time.sleep(step_sleep_time)
    WebDriverWait(driver_luna, timeout_wait).until(EC.presence_of_element_located((By.ID, 
        "gameplay_survey_skip")))
    driver_luna.find_element(By.ID, "gameplay_survey_skip").click()
    time.sleep(step_sleep_time)


def reset():
    print_msg("Running reset...", LogType.INFO)
    x_list = driver_luna.find_elements(By.CLASS_NAME, "_1fisdfa")
    if len(x_list) > 0:
        quit_session()
    
    driver_luna.get("https://luna.amazon.com/settings")
    time.sleep(step_sleep_time)


# Do NOT include the file type
def save_image(image_name: str) -> str:
    file_type = ".png"
    folder_name = "image_results"
    file_name = path.join(folder_name, image_name + file_type)
    unique_name = False
    count = 0

    if path.exists(folder_name) == False:
        makedirs(folder_name)

    while unique_name == False:
        if path.exists(file_name) == False:
            unique_name = True
        else:
            count += 1
            file_name = path.join(folder_name, image_name + "_" + str(count) + file_type)

    driver_luna.save_screenshot(file_name)
    if path.exists(file_name):
        print_msg("Saved screenshot: " + file_name, LogType.IO)
        return file_name
    else:
        print_msg("Failed attempting to take a screenshot!", LogType.ERROR)
    
    return ""


def write_msg_to_file(msg: str):
    try:
        folder_name = "logs"
        filename = path.join("logs", "ScriptLog_" + str(datetime.date.today()) + ".log")
        file = None

        if path.exists(folder_name) == False:
            makedirs(folder_name)

        if path.exists(filename):
            file = open(filename, "a")
        else:
            file = open(filename, "w")

        file.write(msg + "\n")
        file.close()
    except:
        print(Fore.RED + "Error writing to log file!")


def print_msg(msg: str, log_type: LogType):
    log_color = Fore.WHITE

    if log_type == LogType.ERROR:
        log_color = Fore.RED
    elif log_type == LogType.IO:
        log_color == Fore.YELLOW
    elif log_type == LogType.INFO:
        log_color = Fore.GREEN
    else:
        log_color = Fore.WHITE

    timestamp_str = "[" + str(datetime.datetime.now()) + "] "
    print(timestamp_str + log_color + msg)
    write_msg_to_file(timestamp_str + msg)


def get_country_list(arg_str: str) -> list:
    country_list = [Country.US, Country.CA, Country.GB, Country.DE]
    partial_list = []
    use_all = False

    if len(arg_str) >= 1:
        temp_str = arg_str
        temp_str = temp_str.strip()
        temp_str = temp_str.upper()
        arg_list = temp_str.split()

        for arg in arg_list:
            if arg == "ALL":
                use_all = True
                break
            elif arg == "US":
                partial_list.append(Country.US)
            elif arg == "CA":
                partial_list.append(Country.CA)
            elif arg == "GB":
                partial_list.append(Country.GB)
            elif arg == "DE":
                partial_list.append(Country.DE)
    else:
        use_all = True
    
    if use_all == True:
        return country_list
    else:
        return partial_list