from queue import Queue
from threading import Lock

from scrawler.utils.meta import SingletonMeta


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

    def save(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            for data in self.queue():
                d = str(data) + '\n'
                f.write(d)


class DatabaseScheduler(BaseScheduler):
    """
    Database Scheduler: receives scraped item data from spider worker(s) and enques them
    for feeding them to the database.
    """
    items_enqueued = 0
    mutex = Lock()

    def put(self, item, *args, **kwargs):
        with self.mutex:
            self.items_enqueued += 1
        super().put(item, *args, **kwargs)


class ItemUrlScheduler(BaseScheduler):
    """
    Item Url Scheduler: receives item urls from item url downloader worker and enqueues the
    for feeding them to item spider worker
    """
