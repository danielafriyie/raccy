from typing import Union, Dict

from selenium.webdriver import (
    Chrome, Firefox, Safari, Ie, Edge, Opera
)

from scrawler.utils.driver import driver_wait
from scrawler.logger.logger import logger


class BaseForm:
    FIELD_XPATH = str
    FIELD_VALUE = str
    fields: Dict[FIELD_XPATH, FIELD_VALUE]
    log = logger()


class AuthForm(BaseForm):

    def __init__(self, driver: Union[Chrome, Firefox, Safari, Ie, Edge, Opera]):
        self.driver = driver

    def fill_forms(self):
        self.btn = self.fields.pop('button')
        for field, value in self.fields.items():
            driver_wait(self.driver, field, method='presence_of_element_located')
            self.driver.find_element_by_xpath(field).send_keys(value)

    def login(self):
        self.fill_forms()
        self.driver.find_element_by_xpath(self.btn).click()
