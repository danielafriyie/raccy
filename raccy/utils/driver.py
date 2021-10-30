"""
Copyright 2021 Daniel Afriyie

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from urllib.parse import urljoin
from typing import Callable, Optional
from logging import Logger

from selenium.common.exceptions import (
    ElementClickInterceptedException, NoSuchElementException, NoSuchAttributeException, WebDriverException,
)
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement

from .utils import check_has_attr

Driver = WebDriver


def scroll_into_view(driver: Driver, element: WebElement):
    driver.execute_script("arguments[0].scrollIntoView();", element)


def window_scroll_to(driver: Driver, loc: int):
    driver.execute_script(f"window.scrollTo(0, {loc});")


def driver_wait(
        driver: Driver,
        xpath: str,
        secs=5,
        condition=None,
        action: Optional[str] = None
) -> None:
    wait = WebDriverWait(driver=driver, timeout=secs)
    until = wait.until(condition((By.XPATH, xpath)))
    if action:
        check_has_attr(until, action)
        _action = getattr(until, action)
        _action()


def follow(
        callback: Callable,
        *,
        url: str = None,
        driver: Driver = None,
        cargs=(),
        ckwargs: dict = None,
        wait=False,
        xpath: str = None, secs: int = None
) -> None:
    if url and driver:
        driver.get(url)
    if wait:
        driver_wait(driver, xpath, secs)
    callback(*cargs, **ckwargs)


def btn_click_handler(driver: Driver, xpath: str) -> None:
    try:
        btn = driver.find_element_by_xpath(xpath)
        scroll_into_view(driver, btn)
        btn.click()
        return
    except ElementClickInterceptedException:
        try:
            url = driver.find_element_by_xpath(xpath).get_attribute('href')
            driver.get(url)
            return
        except NoSuchAttributeException:
            pass
        raise
    except NoSuchElementException:
        return


def close_popup_handler(driver: Driver, close_btn: str) -> None:
    btn_click_handler(
        driver,
        close_btn
    )


def url_join(base: str, url: str, allow_fragments=True) -> str:
    return urljoin(base, url, allow_fragments)


def close_driver(driver: Driver, logger: Optional[Logger] = None) -> None:
    try:
        driver.quit()
    except WebDriverException as e:
        if logger:
            logger.error(e)
        pass
