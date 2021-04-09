from threading import Thread
from typing import Optional
from queue import Queue

from scrawler.scheduler.scheduler import DatabaseScheduler, BaseScheduler


class DatabaseWorker(Thread):
    """
    Receive scraped data from database scheduler and stores it in a persistent database
    """
    db_scheduler: Optional[DatabaseScheduler, BaseScheduler, Queue] = DatabaseScheduler()

    def job(self):
        raise NotImplementedError(f"{self.__class__.__name__}.job() method is not implemented!")

    def start_job(self):
        self.job()

    def run(self):
        self.start_job()
