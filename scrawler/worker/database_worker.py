from threading import Thread

from scrawler.scheduler.scheduler import DatabaseScheduler


class DatabaseWorker(Thread):
    """
    Receive scraped data from database scheduler and stores it in a persistent database
    """
    db_scheduler = DatabaseScheduler()

    def job(self):
        pass

    def start_job(self):
        self.job()

    def run(self):
        self.start_job()
