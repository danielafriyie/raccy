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
from typing import Union, Dict

from selenium.webdriver import (
    Chrome, Firefox, Safari, Ie, Edge, Opera
)

from raccy.utils.driver import driver_wait
from raccy.utils.utils import download_delay
from raccy.logger.logger import logger


class BaseForm:
    FIELD_XPATH = str
    FIELD_VALUE = str
    fields: Dict[FIELD_XPATH, FIELD_VALUE]
    log = logger()


class AuthForm(BaseForm):

    def __init__(self, driver: Union[Chrome, Firefox, Safari, Ie, Edge, Opera]):
        self.driver = driver

    def fill_forms(self):
        fields = self.fields.copy()
        self.btn = fields.pop('button')
        for field, value in fields.items():
            driver_wait(self.driver, field, 10, method='presence_of_element_located')
            self.driver.find_element_by_xpath(field).send_keys(value)

    def login(self):
        self.fill_forms()
        download_delay(2, 6)
        driver_wait(self.driver, self.btn, 10, method='element_to_be_clickable', action='click')
