from threading import Thread
from queue import Empty, Queue
from typing import Union, Optional

from selenium.common.exceptions import TimeoutException
from selenium.webdriver import (
    Chrome, Firefox, Safari, Ie, Edge, Opera
)

from scrawler.scheduler.scheduler import DatabaseScheduler, ItemUrlScheduler, BaseScheduler
from scrawler.utils.utils import download_delay
from scrawler.utils.driver import close_driver
from scrawler.logger.logger import logger


class CrawlerWorker(Thread):
    """
    Fetches item web pages and scrapes or extract data and enqueues them in DatabaseScheduler
    """
    url_wait_timeout: Optional[int] = 10
    scheduler: Union[ItemUrlScheduler, BaseScheduler, Queue] = ItemUrlScheduler()
    db_scheduler: Union[DatabaseScheduler, BaseScheduler, Queue] = DatabaseScheduler()
    _logger = logger()

    def __init__(self, driver: Union[Chrome, Firefox, Safari, Ie, Edge, Opera], *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.driver = driver

    def job(self):
        while True:
            try:
                url = self.scheduler.get(timeout=self.url_wait_timeout)
                try:
                    self.driver.get(url['url'])
                except TimeoutException:
                    continue
                self.parse(url['url'], url['#'])
                self.scheduler.task_done()
                download_delay()
            except Empty as e:
                self._logger.exception(e)
                close_driver(self.driver, self._logger)
                return

    def start_job(self) -> None:
        self.job()

    def parse(self, url: Optional[str] = None, n: Optional[int] = None) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.parse() method is not implemented")

    def run(self):
        self.start_job()
