from threading import Thread
from queue import Empty, Queue
from typing import Union, Optional, Tuple

from selenium.common.exceptions import TimeoutException
from selenium.webdriver import (
    Chrome, Firefox, Safari, Ie, Edge, Opera
)

from scrawler.scheduler.scheduler import DatabaseScheduler, ItemUrlScheduler, BaseScheduler
from scrawler.utils.utils import download_delay
from scrawler.utils.driver import close_driver
from scrawler.logger.logger import logger
from scrawler.forms.forms import AuthForm


class CrawlerWorker(Thread):
    """
    Fetches item web pages and scrapes or extract data and enqueues them in DatabaseScheduler
    """
    url_wait_timeout: Optional[int] = 10
    scheduler: Union[ItemUrlScheduler, BaseScheduler, Queue] = ItemUrlScheduler()
    db_scheduler: Union[DatabaseScheduler, BaseScheduler, Queue] = DatabaseScheduler()
    log = logger()

    def __init__(self, driver: Union[Chrome, Firefox, Safari, Ie, Edge, Opera], *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.driver = driver

    def job(self):
        while True:
            try:
                url = self.scheduler.get(timeout=self.url_wait_timeout)
                self.parse(url)
                self.scheduler.task_done()
            except Empty:
                self.log.info('Empty scheduler, closing.................')
                close_driver(self.driver, self.log)
                return

    def parse(self, url: str) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.parse() method is not implemented")

    def run(self):
        self.job()
