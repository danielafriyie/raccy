"""
Scrawler: web scraping library based on selenium
"""
from .scheduler.scheduler import ItemUrlScheduler, DatabaseScheduler
from .worker.url_downloader_worker import UrlDownloaderWorker
from .worker.crawler_worker import CrawlerWorker
from .worker.database_worker import DatabaseWorker

__version__ = '1.0.0'
__author__ = 'Daniel Afriyie'
__author_email__ = 'afriyiedaniel1@outlook.com'

__all__ = [
    '__version__', '__author__', '__author_email__',
    'ItemUrlScheduler', 'DatabaseScheduler', 'UrlDownloaderWorker', 'CrawlerWorker', 'DatabaseWorker'
]
