"""
Utility functions and classes for selenium webdriver
"""
from time import sleep
from urllib.parse import urljoin
from typing import Union, Callable
from logging import Logger

from selenium.common.exceptions import (
    ElementClickInterceptedException, NoSuchElementException, NoSuchAttributeException, WebDriverException
)
from selenium.webdriver import (
    Chrome, Firefox, Safari, Ie, Edge, Opera
)

Driver: Union[Chrome, Firefox, Safari, Ie, Edge, Opera] = ...


def driver_wait(driver: Driver, xpath: str, secs=5) -> None:
    for _ in range(secs):
        try:
            driver.find_element_by_xpath(xpath)
            return
        except WebDriverException:
            sleep(1)
            continue
    return


def follow(
        callback: Callable, *, url: str = None, driver: Driver = None, cargs=(), ckwargs: dict = None, wait=False,
        xpath: str = None, secs: int = None
) -> None:
    if url and driver:
        driver.get(url)
    if wait:
        driver_wait(driver, xpath, secs)
    callback(*cargs, **ckwargs)


def close_popup_handler(driver: Driver, close_btn: str) -> None:
    driver_wait(driver, close_btn)
    try:
        driver.find_element_by_xpath(close_btn).click()
    except NoSuchElementException:
        pass


def next_btn_handler(driver: Driver, next_btn: str) -> None:
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


def url_join(base: str, url: str, allow_fragments=True) -> str:
    return urljoin(base, url, allow_fragments)


def close_driver(driver: Driver, logger: Logger = None) -> None:
    try:
        driver.quit()
    except WebDriverException as e:
        if logger:
            logger.error(e)
        pass
