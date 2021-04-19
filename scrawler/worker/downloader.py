from threading import Thread
from typing import Union, Iterable, Iterator, Optional
from queue import Queue

from selenium.common.exceptions import WebDriverException
from selenium.webdriver import (
    Chrome, Firefox, Safari, Ie, Edge, Opera
)

from scrawler.utils.driver import close_popup_handler, next_btn_handler, close_driver
from scrawler.scheduler.scheduler import ItemUrlScheduler, BaseScheduler
from scrawler.logger.logger import logger
from scrawler.utils.forms import AuthForm


class UrlDownloaderWorker(Thread):
    """
    Resonsible for downloading item(s) to be scraped urls and enqueue(s) them in ItemUrlScheduler
    """
    MAX_ITEM_DOWNLOAD: Optional[int] = 20
    start_url: str = None
    url_xpath: Optional[str] = None
    next_btn: Optional[str] = None
    scheduler: Union[ItemUrlScheduler, BaseScheduler, Queue] = ItemUrlScheduler(maxsize=MAX_ITEM_DOWNLOAD)
    urls_scraped: int = 0
    log = logger()
    popup: Optional[str] = None
    auth_form: Optional[AuthForm] = None

    def __init__(self, driver: Union[Chrome, Firefox, Safari, Ie, Edge, Opera], *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.driver = driver

    def job(self):
        raise NotImplementedError(f"{self.__class__.__name__}.job() method is not implemented")

    def start_job(self):
        try:
            self.driver.get(self.start_url)
            if self.auth_form:
                self.auth_form(driver=self.driver).login()
        except WebDriverException as e:
            self.log.exception(e)
            close_driver(self.driver, self.log)
            return
        if self.popup:
            close_popup_handler(self.driver, self.popup)
        self.job()

    def max_reached(self) -> bool:
        if self.MAX_ITEM_DOWNLOAD <= 0:
            return False
        return self.urls_scraped >= self.MAX_ITEM_DOWNLOAD

    def max_reached_handler(self):
        if self.max_reached():
            self.next_btn = None

    def run(self):
        self.start_job()
