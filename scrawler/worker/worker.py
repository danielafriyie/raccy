"""
Worker module
"""
from threading import Thread, Lock
from queue import Empty, Queue
from typing import Union, Optional

from selenium.webdriver import (
    Chrome, Firefox, Safari, Ie, Edge, Opera
)
from selenium.common.exceptions import WebDriverException

from scrawler.core.meta import SingletonMeta
from scrawler.scheduler.scheduler import DatabaseScheduler, ItemUrlScheduler, BaseScheduler
from scrawler.utils.driver import close_driver
from scrawler.logger.logger import logger
from scrawler.core.exceptions import CrawlerException

Scheduler: Union[ItemUrlScheduler, BaseScheduler, Queue] = ...
Driver: Union[Chrome, Firefox, Safari, Ie, Edge, Opera] = ...


class SingleInstanceWorker(Thread, metaclass=SingletonMeta):
    log = logger()


class BaseCrawlerWorker(Thread):
    log = logger()

    def __init__(self, driver: Driver, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = driver


class UrlDownloaderWorker(SingleInstanceWorker):
    """
    Resonsible for downloading item(s) to be scraped urls and enqueue(s) them in ItemUrlScheduler
    """
    start_url: str = None
    scheduler: Scheduler = ItemUrlScheduler()
    mutex = Lock()

    def __init__(self, driver: Driver, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.driver = driver

        if self.start_url is None:
            raise CrawlerException(f"{self.__class__.__name__}: start_url is not defined")

    def job(self):
        raise NotImplementedError(f"{self.__class__.__name__}.job() method is not implemented")

    def run(self):
        try:
            self.driver.get(self.start_url)
            self.job()
        except WebDriverException as e:
            self.log.exception(e)
        close_driver(self.driver, self.log)


class CrawlerWorker(BaseCrawlerWorker):
    """
    Fetches item web pages and scrapes or extract data and enqueues the data in DatabaseScheduler
    """
    url_wait_timeout: Optional[int] = 10
    scheduler: Scheduler = ItemUrlScheduler()
    db_scheduler: Scheduler = DatabaseScheduler()

    def job(self):
        while True:
            try:
                url = self.scheduler.get(timeout=self.url_wait_timeout)
                self.parse(url)
                self.scheduler.task_done()
            except Empty:
                self.log.info('Empty scheduler, closing.................')
                break
        close_driver(self.driver, self.log)

    def parse(self, url: str) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.parse() method is not implemented")

    def run(self):
        self.job()


class DatabaseWorker(SingleInstanceWorker):
    """
    Receives scraped data from DatabaseScheduler and stores it in a persistent database
    """
    wait_timeout: Optional[int] = 10
    db_scheduler: Scheduler = DatabaseScheduler()
    log = logger()

    def save(self, data: dict) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.save() method is not implemented!")

    def job(self):
        while True:
            try:
                data = self.db_scheduler.get(timeout=self.wait_timeout)
                self.save(data)
                self.db_scheduler.task_done()
            except Empty:
                self.log.info('Empty scheduler, closing.................')
                return

    def run(self):
        self.job()
