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
from threading import Thread, Lock
from queue import Empty
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException

from raccy.core.meta import SingletonMeta
from raccy.core.queue_ import DatabaseQueue, BaseQueue, ItemUrlQueue
from raccy.utils.driver import close_driver, next_btn_handler, driver_wait
from raccy.logger.logger import logger
from raccy.core.exceptions import CrawlerException
from raccy.utils.utils import download_image, download


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

    def kill(self):
        if self.is_alive():
            self._is_stopped = False
            self.post_job()

    def run(self):
        self.pre_job()
        self.job()
        self.kill()


class BaseCrawlerWorker(BaseWorker, CrawlerMixin):
    """
    Base class for all crawler workers
    """
    mutex = Lock()

    def __init__(self, driver: WebDriver, *args, **kwargs):
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

    def follow(self, xpath=None, url=None, callback=None, *cbargs, **cbkwargs):
        if xpath is not None and url is not None:
            raise CrawlerException(
                f"{self.__class__.__name__}: both xpath and url defined "
                f"you have to define only one"
            )
        if xpath is not None:
            next_btn_handler(self.driver, next_btn=xpath)
        if url is not None:
            self.driver.get(url)

        return callback(*cbargs, **cbkwargs)

    def post_job(self):
        self.close_driver()


class UrlDownloaderWorker(BaseCrawlerWorker, metaclass=SingletonMeta):
    """
    Resonsible for downloading item(s) to be scraped urls and enqueue(s) them in ItemUrlQueue
    """
    start_url: str = None
    url_queue: BaseQueue = ItemUrlQueue()
    urls_scraped = 1
    max_url_download = -1

    def __init__(self, driver: WebDriver, *args, **kwargs):
        super().__init__(driver, *args, **kwargs)

        if self.start_url is None:
            raise CrawlerException(f"{self.__class__.__name__}: start_url attribute is not defined!")

    def follow(self, xpath=None, url=None, callback=None, *cbargs, **cbkwargs):
        if self.max_url_download > 0:
            if self.urls_scraped > self.max_url_download:
                return

        with self.mutex:
            self.urls_scraped += 1

        return super().follow(xpath=xpath, url=url, callback=callback, *cbargs, **cbkwargs)

    def job(self):
        raise NotImplementedError(f"{self.__class__.__name__}.job() method is not implemented")

    def run(self):
        try:
            self.driver.get(self.start_url)
            self.pre_job()
            self.job()
        except WebDriverException as e:
            self.log.exception(e)
        finally:
            self.kill()


class CrawlerWorker(BaseCrawlerWorker):
    """
    Fetches item web pages and scrapes or extract data and enqueues the data in DatabaseQueue
    """
    url_wait_timeout: Optional[int] = 10
    url_queue: BaseQueue = ItemUrlQueue()
    db_queue: BaseQueue = DatabaseQueue()

    def download_image(self, url, save_path):
        return download_image(url, save_path, self.mutex)

    def download_file(self, url, save_path):
        return download(url, save_path)

    def job(self):
        try:
            url = self.url_queue.get(timeout=self.url_wait_timeout)
            self.parse(url)
            self.url_queue.task_done()
            return self.job()
        except Empty:
            pass

    def parse(self, url: str) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.parse() method is not implemented")


class DatabaseWorker(BaseWorker, metaclass=SingletonMeta):
    """
    Receives scraped data from DatabaseQueue and stores it in a persistent database
    """
    data_wait_timeout: Optional[int] = 10
    db_queue: BaseQueue = DatabaseQueue()

    def save(self, data: dict) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.save() method is not implemented!")

    def job(self):
        try:
            data = self.db_queue.get(timeout=self.data_wait_timeout)
            self.save(data)
            self.db_queue.task_done()
            return self.job()
        except Empty:
            pass
