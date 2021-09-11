"""
Copyright [2021] [Daniel Afriyie]

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
from typing import Union, Callable, Optional
from logging import Logger

from selenium.common.exceptions import (
    ElementClickInterceptedException, NoSuchElementException, NoSuchAttributeException, WebDriverException
)
from selenium.webdriver import (
    Chrome, Firefox, Safari, Ie, Edge, Opera
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement

from .utils import check_has_attr

Driver: Union[Chrome, Firefox, Safari, Ie, Edge, Opera] = ...


def scroll_into_view(driver: Driver, element: WebElement):
    driver.execute_script("arguments[0].scrollIntoView();", element)


def window_scroll_to(driver: Driver, loc: int):
    driver.execute_script(f"window.scrollTo(0, {loc});")


def driver_wait(
        driver: Driver, xpath: str, secs=5, method: str = None, action: Optional[str] = None
) -> None:
    check_has_attr(EC, method)
    wait = WebDriverWait(driver=driver, timeout=secs)
    condition = getattr(EC, method)
    until = wait.until(condition((By.XPATH, xpath)))
    if action:
        check_has_attr(until, action)
        getattr(until, action)()


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
    driver_wait(driver, close_btn, method='element_to_be_clickable')
    try:
        driver.find_element_by_xpath(close_btn).click()
    except NoSuchElementException:
        pass


def next_btn_handler(driver: Driver, next_btn: str) -> None:
    try:
        btn = driver.find_element_by_xpath(next_btn)
        scroll_into_view(driver, btn)
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


def close_driver(driver: Driver, logger: Optional[Logger] = None) -> None:
    try:
        driver.quit()
    except WebDriverException as e:
        if logger:
            logger.error(e)
        pass
