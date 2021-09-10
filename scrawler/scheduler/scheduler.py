from queue import Queue

from scrawler.core.meta import SingletonMeta
from scrawler.core.exceptions import SchedulerError


class BaseScheduler(metaclass=SingletonMeta):
    """
    Base Scheduler class: It restricts objects instances to only one instance.
    """

    def __init__(self, maxsize=0):
        self.__queue = Queue(maxsize=maxsize)

    @property
    def get_queue(self):
        return self.__queue

    def put(self, item, *args, **kwargs):
        self.__queue.put(item, *args, **kwargs)

    def get(self, *args, **kwargs):
        return self.__queue.get(*args, **kwargs)

    def qsize(self):
        return self.__queue.qsize()

    def empty(self):
        return self.__queue.empty()

    def full(self):
        return self.__queue.full()

    def queue(self):
        return self.__queue.queue

    def task_done(self):
        return self.__queue.task_done()


class DatabaseScheduler(BaseScheduler):
    """
    Receives scraped item data from CrawlerWorker and enques them
    for feeding them to DatabaseWorker.
    """

    def put(self, item, *args, **kwargs):
        if not isinstance(item, dict):
            raise SchedulerError(f"{self.__class__.__name__} accepts only dictionary values!")
        super().put(item, *args, **kwargs)


class ItemUrlScheduler(BaseScheduler):
    """
    Receives item urls from UrlDownloaderWorker and enqueues them
    for feeding them to CrawlerWorker
    """
