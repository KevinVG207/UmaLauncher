# Will handle selenium browser automation
# Before every action, we need to check if the browser is open
# and, in the case of multiple windows, which one is the one we want to use
# Each open window will be an instance of a custom class.
# Interacting with the browser will be done through this class.

import traceback
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

def firefox_setup(helper_url):
    firefox_service = FirefoxService()
    firefox_service.creation_flags = CREATE_NO_WINDOW
    profile = webdriver.FirefoxProfile(util.get_asset("ff_profile"))
    options = webdriver.FirefoxOptions()
    browser = webdriver.Firefox(service=firefox_service, firefox_profile=profile, options=options)
    browser.get(helper_url)
    return browser

def chromium_setup(service, options_class, driver_class, profile, helper_url):
    service.creation_flags = CREATE_NO_WINDOW
    options = options_class()
    options.add_argument("--user-data-dir=" + str(util.get_asset(profile)))
    options.add_argument("--app=" + helper_url)
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--new-window")
    browser = driver_class(service=service, options=options)
    return browser

def chrome_setup(helper_url):
    return chromium_setup(
        service=ChromeService(),
        options_class=webdriver.ChromeOptions,
        driver_class=webdriver.Chrome,
        profile="chr_profile",
        helper_url=helper_url
    )

def edge_setup(helper_url):
    return chromium_setup(
        service=EdgeService(),
        options_class=webdriver.EdgeOptions,
        driver_class=webdriver.Edge,
        profile="edg_profile",
        helper_url=helper_url
    )

BROWSER_LIST = {
    'Chrome': chrome_setup,
    'Firefox': firefox_setup,
    'Edge': edge_setup,
}

def init_browser(url, browser_name):
    driver = None

    browser_list = []
    if browser_name == "Auto":
        browser_list = BROWSER_LIST.values()
    else:
        browser_list = [BROWSER_LIST[browser_name]]

    for browser_setup in browser_list:
        try:
            logger.info("Attempting " + str(browser_setup.__name__))
            driver = browser_setup(url)
            break
        except Exception:
            logger.error("Failed to start browser")
            logger.error(traceback.format_exc())
    if not driver:
        util.show_warning_box("Uma Launcher: Unable to start browser.", "Selected webbrowser cannot be started.")
    return driver

def urls_match(url1, url2):
    url1 = url1[:-1] if url1.endswith('/') else url1
    url2 = url2[:-1] if url2.endswith('/') else url2
    urlparse1 = urlparse(url1)
    urlparse2 = urlparse(url2)
    return (urlparse1.netloc, urlparse1.path) == (urlparse2.netloc, urlparse2.path)

class BrowserWindow:
    def __init__(self, url, threader, rect=None):
        self.url = url
        self.threader = threader
        self.browser_name = [
                browser
                for browser, selected in threader.settings['s_selected_browser'].items()
                if selected
            ][0]
        self.driver = None
        self.old_drivers = []
        self.active_tab_handle = None
        self.last_window_rect = None
        
        self.ensure_tab_open()
        if rect:
            self.set_window_rect(rect)

    def alive(self):
        if self.driver is None:
            return False
        try:
            if self.active_tab_handle in self.driver.window_handles:
                return True
        except (NoSuchWindowException, WebDriverException):
            pass
        return False


    def ensure_tab_open(self):
        if self.driver:
            # Check if we have window handles
            try:
                if self.active_tab_handle in self.driver.window_handles:
                    self.driver.switch_to.window(self.active_tab_handle)
                    if urls_match(self.driver.current_url, self.url):
                        self.last_window_rect = self.driver.get_window_rect()
                        return
                    elif self.browser_name == "Firefox":
                        self.driver.get(self.url)
                        return
                    self.close()
            except (NoSuchWindowException, WebDriverException):
                self.driver.quit()
                self.driver = None
            self.old_drivers.append(self.driver)

        self.driver = init_browser(self.url, self.browser_name)
        self.active_tab_handle = self.driver.window_handles[0]
        self.last_window_rect = self.driver.get_window_rect()

    def ensure_focus(func):
        def wrapper(self, *args, **kwargs):
            self.ensure_tab_open()
            return func(self, *args, **kwargs)
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
        for driver in self.old_drivers:
            try:
                driver.quit()
            except (NoSuchWindowException, WebDriverException):
                pass
        self.close()
        try:
            self.driver.quit()
        except (NoSuchWindowException, WebDriverException):
            pass