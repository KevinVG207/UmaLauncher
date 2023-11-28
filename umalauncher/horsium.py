# Will handle selenium browser automation
# Before every action, we need to check if the browser is open
# and, in the case of multiple windows, which one is the one we want to use
# Each open window will be an instance of a custom class.
# Interacting with the browser will be done through this class.

import traceback
import time
import threading
from urllib.parse import urlparse
from subprocess import CREATE_NO_WINDOW
from loguru import logger
from selenium.common.exceptions import WebDriverException
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import NoSuchWindowException
import util

OLD_DRIVERS = []

def firefox_setup(helper_url, settings):
    driver_path = None
    if settings['s_enable_browser_override']:
        new_path = settings['s_browser_custom_driver']
        if new_path:
            driver_path = new_path

    firefox_service = FirefoxService(executable_path=driver_path)
    firefox_service.creation_flags = CREATE_NO_WINDOW
    profile = webdriver.FirefoxProfile(util.get_asset("ff_profile"))
    options = webdriver.FirefoxOptions()
    options.profile = profile

    binary_path = None

    if settings['s_enable_browser_override']:
        binary_path = settings['s_browser_custom_binary']
        if binary_path:
            options.binary_location = binary_path
    
    logger.debug(f"Firefox driver path: {driver_path}")
    logger.debug(f"Firefox binary path: {binary_path}")
    
    browser = webdriver.Firefox(service=firefox_service, options=options)
    browser.get(helper_url)
    return browser

def chromium_setup(service, options_class, driver_class, profile, helper_url, settings, binary_path=None):
    service.creation_flags = CREATE_NO_WINDOW
    options = options_class()

    if binary_path:
        options.binary_location = binary_path

    options.add_argument("--user-data-dir=" + str(util.get_asset(profile)))
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--new-window")
    
    if not settings['s_enable_browser_override']:
        options.add_argument("--app=" + helper_url)

    browser = driver_class(service=service, options=options)
    
    if settings['s_enable_browser_override']:
        browser.get(helper_url)

    return browser

def chrome_setup(helper_url, settings):
    driver_path = None
    if settings['s_enable_browser_override']:
        new_path = settings['s_browser_custom_driver']
        if new_path:
            driver_path = new_path
    
    binary_path = None
    if settings['s_enable_browser_override']:
        binary_path = settings['s_browser_custom_binary']

    logger.debug(f"Chrome driver path: {driver_path}")
    logger.debug(f"Chrome binary path: {binary_path}")

    return chromium_setup(
        service=ChromeService(executable_path=driver_path) if driver_path else ChromeService(),
        options_class=webdriver.ChromeOptions,
        driver_class=webdriver.Chrome,
        profile="chr_profile",
        helper_url=helper_url,
        settings=settings,
        binary_path=binary_path
    )

def edge_setup(helper_url, settings):
    return chromium_setup(
        service=EdgeService(),
        options_class=webdriver.EdgeOptions,
        driver_class=webdriver.Edge,
        profile="edg_profile",
        helper_url=helper_url,
        settings=settings
    )

BROWSER_LIST = {
    'Firefox': firefox_setup,
    'Chrome': chrome_setup,
    'Edge': edge_setup,
}

def urls_match(url1, url2):
    url1 = url1[:-1] if url1.endswith('/') else url1
    url2 = url2[:-1] if url2.endswith('/') else url2
    urlparse1 = urlparse(url1)
    urlparse2 = urlparse(url2)
    return (urlparse1.netloc, urlparse1.path) == (urlparse2.netloc, urlparse2.path)



class BrowserWindow:
    def __init__(self, url, threader, rect=None, run_at_launch=None):
        self.url = url
        self.threader = threader
        self.settings = threader.settings
        self.driver: RemoteWebDriver = None
        self.active_tab_handle = None
        self.last_window_rect = {'x': rect[0], 'y': rect[1], 'width': rect[2], 'height': rect[3]} if rect else None
        self.run_at_launch = run_at_launch
        self.browser_name = "Auto"
        self.latest_error = ""
        
        self.ensure_tab_open()

    def init_browser(self) -> RemoteWebDriver:
        driver = None

        if self.settings['s_enable_browser_override']:
            selection = self.settings['s_custom_browser_type']
        else:
            selection = self.settings['s_selected_browser']
        browser_name = [
                    browser
                    for browser, selected in selection.items()
                    if selected
                ][0]
        self.browser_name = browser_name

        if browser_name == 'Chromium':
            browser_name = 'Chrome'

        browser_list = []
        if browser_name == "Auto":
            browser_list = BROWSER_LIST.items()
        else:
            browser_list = [(browser_name, BROWSER_LIST[browser_name])]

        for browser_data in browser_list:
            browser_name, browser_setup = browser_data
            try:
                logger.info("Attempting " + str(browser_setup.__name__))
                driver = browser_setup(self.url, self.settings)
                self.browser_name = browser_name
                break
            except Exception as e:
                logger.error("Failed to start browser")
                logger.error(traceback.format_exc())
                self.latest_error = traceback.format_exception_only(type(e), e)[-1]
        # if not driver:
        #     util.show_warning_box("Uma Launcher: Unable to start browser.", "Selected webbrowser cannot be started.")
        return driver

    def alive(self):
        if self.driver is None:
            return False
        try:
            if self.active_tab_handle in self.driver.window_handles:
                return True
        except:
            pass
        return False


    def ensure_tab_open(self):
        if self.driver:
            # Check if we have window handles
            try:
                window_handles = self.driver.window_handles
                try:
                    if self.active_tab_handle in window_handles:
                        if self.browser_name in ['Chrome', 'Edge']:
                            if self.driver.current_window_handle != self.active_tab_handle:
                                raise Exception("Wrong window handle")

                        if self.browser_name == 'Firefox' and self.driver.current_window_handle != self.active_tab_handle:
                            self.driver.switch_to.window(self.active_tab_handle)

                        if urls_match(self.driver.current_url, self.url):
                            from_script = self.driver.execute_script("return window.from_script;")
                            if from_script:
                                self.last_window_rect = self.driver.get_window_rect()
                                return
                        
                        self.driver.execute_script(f"document.still_the_old_page_haha = true;")  # Really reflects my mental state when I made this code
                        self.driver.execute_script(f"window.location = '{self.url}';")
                        # Wait for the page to load
                        while self.driver.execute_script("return document.still_the_old_page_haha;"):
                            time.sleep(0.2)
                        while self.driver.execute_script("return document.readyState;") != "complete":
                            time.sleep(0.2)
                        self.run_script_at_launch()
                        return
                except:
                    self.driver.quit()
                    self.driver = None
            except WebDriverException:
                pass
            OLD_DRIVERS.append(self.driver)

        self.driver = self.init_browser()
    
        if not self.driver or not self.driver.window_handles:
            return

        self.active_tab_handle = self.driver.window_handles[0]
        self.driver.switch_to.window(self.active_tab_handle)
        self.run_script_at_launch()
        self.last_window_rect = self.driver.get_window_rect()

    def run_script_at_launch(self):
        self.driver.execute_script("""window.from_script = true;""")
        if self.last_window_rect:
            self.driver.set_window_rect(self.last_window_rect['x'], self.last_window_rect['y'], self.last_window_rect['width'], self.last_window_rect['height'])
        if self.run_at_launch is not None:
            self.run_at_launch(self)

    def ensure_focus(func):
        def wrapper(self, *args, **kwargs):
            tries = 0

            while tries < 3:
                tries += 1
                self.ensure_tab_open()
                if self.driver:
                    return func(self, *args, **kwargs)

            util.show_warning_box("Uma Launcher: Unable to reach browser.", f"Webbrowser is unable to open.<br><br>If this problem persists, try restarting your computer<br>or selecting a different browser in the preferences.<br><br>Extra info:<br>{self.latest_error}")
        return wrapper

    @ensure_focus
    def execute_script(self, *args, **kwargs):
        return self.driver.execute_script(*args, **kwargs)

    @ensure_focus
    def set_window_rect(self, rect):
        return self.driver.set_window_rect(*rect)
    
    @ensure_focus
    def get_window_rect(self):
        return self.driver.get_window_rect()

    def get_last_window_rect(self):
        return self.last_window_rect
    
    def current_url(self):
        return self.url

    def close(self):
        # Only close the active tab
        try:
            if self.active_tab_handle in self.driver.window_handles:
                self.driver.switch_to.window(self.active_tab_handle)
                self.last_window_rect = self.driver.get_window_rect()
                self.driver.close()
        except (NoSuchWindowException, WebDriverException):
            pass

    def quit(self):
        self.close()
        OLD_DRIVERS.append(self.driver)
        self.driver = None


def quit_one_driver(driver):
    logger.debug(f"Closing driver in thread {threading.get_ident()}")
    if driver:
        try:
            driver.quit()
        except (NoSuchWindowException, WebDriverException):
            pass
    logger.debug(f"Finished closing driver in thread {threading.get_ident()}")

def quit_all_drivers():
    global OLD_DRIVERS

    quit_threads = []
    for driver in OLD_DRIVERS:
        quit_threads.append(threading.Thread(target=quit_one_driver, args=(driver,)))

    for thread in quit_threads:
        thread.start()

    for thread in quit_threads:
        thread.join()

    OLD_DRIVERS = []

# Chromium Webdriver is a poopyhead