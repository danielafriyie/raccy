"""
Utility functions and classes for selenium webdriver
"""
from time import sleep
from urllib.parse import urljoin

from selenium.common.exceptions import (
    ElementClickInterceptedException, NoSuchElementException, NoSuchAttributeException, WebDriverException
)


def driver_wait(driver, xpath, secs=5):
    for _ in range(secs):
        try:
            driver.find_element_by_xpath(xpath)
            return
        except WebDriverException:
            sleep(1)
            continue
    return


def follow(callback, *, url=None, driver=None, cargs=(), ckwargs=None, wait=False, xpath=None, secs=None):
    if url and driver:
        driver.get(url)
    if wait:
        driver_wait(driver, xpath, secs)
    callback(*cargs, **ckwargs)


def close_popup_handler(driver, close_btn):
    driver_wait(driver, close_btn)
    try:
        driver.find_element_by_xpath(close_btn).click()
    except NoSuchElementException:
        pass


def next_btn_handler(driver, next_btn):
    try:
        btn = driver.find_element_by_xpath(next_btn)
        driver.execute_script("arguments[0].scrollIntoView();", btn)
        btn.click()
        return
    except ElementClickInterceptedException:
        try:
            next_url = driver.find_element_by_xpath(next_btn).get_attribute('href')
            driver.get(next_url)
            return
        except NoSuchAttributeException:
            pass
        raise
    except NoSuchElementException:
        return


def url_join(base, url, allow_fragments=True):
    return urljoin(base, url, allow_fragments)


def close_driver(driver, logger=None):
    try:
        driver.quit()
    except WebDriverException as e:
        if logger:
            logger.error(e)
        pass
