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
from threading import Thread, Lock
from queue import Empty, Queue
from typing import Union, Optional

from selenium.webdriver import (
    Chrome, Firefox, Safari, Ie, Edge, Opera
)
from selenium.common.exceptions import WebDriverException

from raccy.core.meta import SingletonMeta
from raccy.scheduler.scheduler import DatabaseScheduler, ItemUrlScheduler, BaseScheduler
from raccy.utils.driver import close_driver, next_btn_handler, driver_wait
from raccy.logger.logger import logger
from raccy.core.exceptions import CrawlerException

Scheduler: Union[ItemUrlScheduler, BaseScheduler, Queue] = ...
Driver: Union[Chrome, Firefox, Safari, Ie, Edge, Opera] = ...


##################################
#       MIXINS
#################################
class CrawlerMixin:

    def close_driver(self):
        close_driver(self.driver, self.log)


###############################
#       WORKERS
###############################
class BaseWorker(Thread):
    """
    Base class for all workers
    """
    log = logger()

    def pre_job(self):
        """
        Runs before job method is called
        """

    def post_job(self):
        """
        Runs after job method is called
        """

    def run(self):
        self.pre_job()
        self.job()
        self.post_job()


class BaseCrawlerWorker(BaseWorker, CrawlerMixin):
    """
    Base class for all crawler workers
    """

    def __init__(self, driver: Driver, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = driver

    def wait(self, xpath, secs=5, condition=None, action=None):
        driver_wait(
            driver=self.driver,
            xpath=xpath,
            secs=secs,
            condition=condition,
            action=action
        )


class SingleInstanceWorker(BaseWorker, metaclass=SingletonMeta):
    pass


class UrlDownloaderWorker(SingleInstanceWorker, CrawlerMixin):
    """
    Resonsible for downloading item(s) to be scraped urls and enqueue(s) them in ItemUrlScheduler
    """
    start_url: str = None
    scheduler: Scheduler = ItemUrlScheduler()
    mutex = Lock()
    urls_scraped = 0
    max_url_download = -1

    def __init__(self, driver: Driver, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = driver

        if self.start_url is None:
            raise CrawlerException(f"{self.__class__.__name__}: start_url is not defined")

    def wait(self, xpath, secs=5, condition=None, action=None):
        driver_wait(
            driver=self.driver,
            xpath=xpath,
            secs=secs,
            condition=condition,
            action=action
        )

    def follow(self, xpath=None, url=None, callback=None, *cbargs, **cbkwargs):
        if self.max_url_download > 0:
            if self.urls_scraped > self.max_url_download:
                return

        if xpath is not None and url is not None:
            raise CrawlerException(
                f"{self.__class__.__name__}: both xpath and url is defined in "
                f"follow method, you have to define only one"
            )
        if xpath is not None:
            next_btn_handler(self.driver, next_btn=xpath)
        if url is not None:
            self.driver.get(url)

        with self.mutex:
            self.urls_scraped += 1

        return callback(*cbargs, **cbkwargs)

    def job(self):
        raise NotImplementedError(f"{self.__class__.__name__}.job() method is not implemented")

    def run(self):
        try:
            self.driver.get(self.start_url)
            self.pre_job()
            self.job()
            self.post_job()
        except WebDriverException as e:
            self.log.exception(e)
        finally:
            self.close_driver()


class CrawlerWorker(BaseCrawlerWorker):
    """
    Fetches item web pages and scrapes or extract data and enqueues the data in DatabaseScheduler
    """
    url_wait_timeout: Optional[int] = 10
    scheduler: Scheduler = ItemUrlScheduler()
    db_scheduler: Scheduler = DatabaseScheduler()

    def job(self):
        try:
            url = self.scheduler.get(timeout=self.url_wait_timeout)
            self.parse(url)
            self.scheduler.task_done()
            return self.job()
        except Empty:
            self.log.info(f'{self.__class__.__name__}: Empty scheduler, closing.................')

    def parse(self, url: str) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.parse() method is not implemented")

    def run(self):
        self.pre_job()
        self.job()
        self.post_job()
        self.close_driver()


class DatabaseWorker(SingleInstanceWorker):
    """
    Receives scraped data from DatabaseScheduler and stores it in a persistent database
    """
    wait_timeout: Optional[int] = 10
    db_scheduler: Scheduler = DatabaseScheduler()

    def save(self, data: dict) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.save() method is not implemented!")

    def job(self):
        try:
            data = self.db_scheduler.get(timeout=self.wait_timeout)
            self.save(data)
            self.db_scheduler.task_done()
            return self.job()
        except Empty:
            self.log.info(f'{self.__class__.__name__}: Empty scheduler, closing.................')
