import datetime
import logging
import os.path
import random
import shutil
import sys
import time
import schedule
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

logger = logging.getLogger("CLIPPER")
logger.addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.DEBUG)


def take_screenshot(driver):
    name = datetime.datetime.now().isoformat()
    logger.debug(f"Taking Screenshot with {name}")
    driver.get_screenshot_as_file(filename=f"./ss/{name}.png")


def login(driver):
    count = 0
    LIMIT = 10
    take_screenshot(driver)
    while count <= LIMIT and not is_logged_in(driver):
        count += 1
        logger.info(f"Attempting login: {count} of {LIMIT}")
        try:
            driver.get("https://www.safeway.com/account/sign-in.html")
            username_field = '//*[@id="label-email"]'
            password_field = '//*[@id="label-password"]'
            signin_button = '//*[@id="btnSignIn"]'
            element = WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, username_field)))
            element.send_keys(EMAIL)
            element = WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, password_field)))
            element.send_keys(PASSWORD)
            element = WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.XPATH, signin_button)))
            time.sleep(1)
            element.click()

        except Exception as e:
            logger.error("Error in login", exc_info=e)
    take_screenshot(driver)


def is_logged_in(driver):
    logger.debug("Checking to see if its logged in")
    try:
        if driver.current_url == LOGIN_URL:
            logging.debug("Seems that we are still on the login page despite the implicit wait")
            return False
        if "error" in driver.current_url or "sso" in driver.current_url:
            logger.debug(f"We are now redirected to {driver.current_url} which we think is the captcha page")
            take_screenshot(driver=driver)
            logger.debug("Sleeping a random amount of time between 10-30 seconds")
            time.sleep(random.randint(10, 30))
            return False
        logger.debug("Getting pickup text as a validation for login")
        xpath = '// *[ @ id = "pickUpText"] / span[2]'
        take_screenshot(driver)
        content = WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.XPATH, xpath)))
        logger.debug(f"Found {content.text}")
        return True
    except TimeoutException:
        logger.error("Timeout hit waiting for pickup text")
        take_screenshot(driver)


def accept(driver):
    logger.debug("Accepting the banners")
    try:
        css = "#onetrust-accept-btn-handler"
        cookies = WebDriverWait(driver, 10).until(ec.presence_of_element_located((By.CSS_SELECTOR, css)))
        cookies.click()
        logger.debug("Accepted the privacy banner")
    except NoSuchElementException:
        logger.debug("Nothing is here to accept")
        take_screenshot(driver)


def load_more(driver):
    try:
        logger.debug("Loading more")
        driver.find_element(By.CSS_SELECTOR, ".load-more").click()
        logger.debug("Loaded more")
        return True
    except NoSuchElementException as e:
        logger.error("There is nothing more to find", exc_info=e)
        take_screenshot(driver)
        return False


def start_clipping(driver):
    coupons = driver.find_elements(By.XPATH, "//*[starts-with(@id, 'couponAddBtn')]")
    logger.debug(f"found {len(coupons)} coupons on this page")
    for coupon in coupons:
        try:
            coupon.click()
            logger.debug("Coupon clipped")
        except Exception as e:
            logger.error("Could not click the coupon", exc_info=e)
            take_screenshot(driver)
    return len(coupons) > 0


def do_work(driver):
    found_coupons = start_clipping(driver=driver)
    found_more = load_more(driver=driver)
    return found_more or found_coupons


def main():
    try:
        logger.debug("Deleting screenshots from the previous session")
        shutil.rmtree("./ss")
    except:
        pass
    os.mkdir("./ss")
    import undetected_chromedriver as uc
    driver = uc.Chrome(headless=True, use_subprocess=True)
    driver.implicitly_wait(time_to_wait=5)
    driver.get(COUPON_URL)

    accept(driver=driver)
    login(driver=driver)
    driver.get(COUPON_URL)
    while do_work(driver=driver):
        logging.info("Loaded more coupons")
    logging.info("Done with everything")
    driver.close()


if __name__ == '__main__':
    LOGIN_URL = os.getenv("LOGIN_URL", "https://www.safeway.com/account/sign-in.html")
    COUPON_URL = os.getenv("COUPON_URL", "https://www.safeway.com/foru/coupons-deals.html")
    EMAIL = os.getenv("EMAIL", None)
    PASSWORD = os.getenv("PASSWORD", None)
    SCHEDULE_DAYS = int(os.getenv("DAYS", "7"))

    if EMAIL is None or PASSWORD is None:
        raise ValueError("You must provide an email and password to get started. "
                         "Set environment variables EMAIL and PASSWORD")

    schedule.every(SCHEDULE_DAYS).days.do(main)
    schedule.run_all()
    while True:
        all_jobs = schedule.get_jobs()
        logger.info(f"All Jobs {all_jobs}")
        logger.info(f"Sleeping for {SCHEDULE_DAYS} days")
        schedule.run_pending()
        # Sleeping the exact amount will mean the job will run immedietly after
        time.sleep(86400*SCHEDULE_DAYS)
