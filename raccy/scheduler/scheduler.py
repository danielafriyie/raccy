"""
Copyright [2021] [Daniel Afriyie]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from queue import Queue

from raccy.core.meta import SingletonMeta
from raccy.core.exceptions import SchedulerError


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
