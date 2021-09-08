from threading import Thread, Lock
from typing import Union
from queue import Queue

from selenium.common.exceptions import WebDriverException
from selenium.webdriver import (
    Chrome, Firefox, Safari, Ie, Edge, Opera
)

from scrawler.utils.driver import close_driver
from scrawler.scheduler.scheduler import ItemUrlScheduler, BaseScheduler
from scrawler.logger.logger import logger
from scrawler.core.exceptions import CrawlerException


class UrlDownloaderWorker(Thread):
    """
    Resonsible for downloading item(s) to be scraped urls and enqueue(s) them in ItemUrlScheduler
    """
    start_url: str = None
    scheduler: Union[ItemUrlScheduler, BaseScheduler, Queue] = ItemUrlScheduler()
    mutex = Lock()
    log = logger()

    def __init__(self, driver: Union[Chrome, Firefox, Safari, Ie, Edge, Opera], *args, **kwargs):
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
