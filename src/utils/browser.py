"""
Selenium browser manager with anti-detection and session handling.
"""
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from config import settings
from .logger import setup_logger

log = setup_logger("browser")


class BrowserManager:
    """Manages a Selenium Chrome browser instance with stealth settings."""

    def __init__(self, headless: bool = None, profile_dir: str = None):
        self.headless = headless if headless is not None else settings.HEADLESS
        self.profile_dir = profile_dir
        self.driver = None

    def start(self) -> webdriver.Chrome:
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        if self.profile_dir:
            opts.add_argument(f"--user-data-dir={self.profile_dir}")

        if settings.CHROME_BINARY:
            opts.binary_location = settings.CHROME_BINARY

        service_kwargs = {}
        if settings.CHROMEDRIVER_PATH:
            service_kwargs["executable_path"] = settings.CHROMEDRIVER_PATH

        service = Service(**service_kwargs)
        self.driver = webdriver.Chrome(service=service, options=opts)
        self.driver.set_page_load_timeout(settings.PAGE_LOAD_TIMEOUT)
        self.driver.implicitly_wait(settings.IMPLICIT_WAIT)

        # Remove webdriver flag
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )

        log.info("Browser started (headless=%s)", self.headless)
        return self.driver

    def get(self, url: str, wait: float = None):
        """Navigate to URL with random delay."""
        if not self.driver:
            self.start()
        delay = wait or random.uniform(settings.REQUEST_DELAY_MIN, settings.REQUEST_DELAY_MAX)
        time.sleep(delay)
        try:
            self.driver.get(url)
            log.debug("Navigated to %s", url[:80])
        except TimeoutException:
            log.warning("Page load timeout for %s", url[:80])

    def wait_for(self, selector: str, by: str = By.CSS_SELECTOR, timeout: int = 15):
        """Wait for element to be present."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            return None

    def execute_js(self, script: str):
        """Execute JavaScript and return result."""
        try:
            return self.driver.execute_script(f"return {script}")
        except WebDriverException as e:
            log.error("JS execution failed: %s", str(e)[:100])
            return None

    def scroll_page(self, times: int = 3, pause: float = 2):
        """Scroll page down to load dynamic content."""
        for i in range(times):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(pause)

    def login_linkedin(self):
        """Login to LinkedIn using credentials from settings."""
        if not settings.LINKEDIN_EMAIL or not settings.LINKEDIN_PASSWORD:
            log.warning("LinkedIn credentials not set. Manual login required.")
            return False

        self.get("https://www.linkedin.com/login", wait=2)
        try:
            email_field = self.wait_for("#username")
            if email_field:
                email_field.clear()
                email_field.send_keys(settings.LINKEDIN_EMAIL)

            pw_field = self.wait_for("#password")
            if pw_field:
                pw_field.clear()
                pw_field.send_keys(settings.LINKEDIN_PASSWORD)

            submit = self.wait_for('button[type="submit"]')
            if submit:
                submit.click()
                time.sleep(5)

            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                log.info("LinkedIn login successful")
                return True
            else:
                log.warning("LinkedIn login may have failed (URL: %s)", self.driver.current_url[:60])
                return False
        except Exception as e:
            log.error("LinkedIn login error: %s", str(e)[:100])
            return False

    def quit(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            log.info("Browser closed")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.quit()
