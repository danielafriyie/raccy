from threading import Thread
from typing import Union, Optional
from queue import Queue, Empty

from scrawler.scheduler.scheduler import DatabaseScheduler, BaseScheduler
from scrawler.logger.logger import logger


class DatabaseWorker(Thread):
    """
    Receive scraped data from database scheduler and stores it in a persistent database
    """
    wait_timeout: Optional[int] = 10
    db_scheduler: Union[DatabaseScheduler, BaseScheduler, Queue] = DatabaseScheduler()
    log = logger()

    def save(self, data: dict) -> None:
        raise NotImplementedError(f"{self.__class__.__name__}.save() method is not implemented!")

    def job(self):
        while True:
            try:
                data = self.db_scheduler.get(timeout=self.wait_timeout)
                self.save(data)
            except Empty as e:
                self.log.exception(e)
                return

    def start_job(self):
        self.job()

    def run(self):
        self.start_job()
