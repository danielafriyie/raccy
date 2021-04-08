from threading import Thread
from queue import Empty

from selenium.common.exceptions import TimeoutException

from scheduler.scheduler import DatabaseScheduler, ItemUrlScheduler
from utils.utils import download_delay
from utils.driver import close_driver
from logger.logger import logger


class CrawlerWorker(Thread):
    """
    Fetches item web pages and scrapes or extract data and enqueues them in DatabaseScheduler
    """
    url_wait_timeout = 10
    urldownloader_scheduler = ItemUrlScheduler()
    db_scheduler = DatabaseScheduler()
    _logger = logger(filename='crawler_worker.log')

    def __init__(self, driver, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.driver = driver

    def job(self):
        while True:
            try:
                url = self.urldownloader_scheduler.get(timeout=self.url_wait_timeout)
                try:
                    self.driver.get(url['url'])
                except TimeoutException:
                    continue
                self.parse(url['url'], url['#'])
                self.urldownloader_scheduler.task_done()
                download_delay()
            except Empty as e:
                self._logger.exception(e)
                close_driver(self.driver, self._logger)
                return

    def start_job(self):
        self.job()

    def parse(self, url, n):
        raise NotImplementedError(f"{self.__class__.__name__}.parse() method is not implemented")

    def run(self):
        self.start_job()
