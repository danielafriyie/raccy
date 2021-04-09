"""
Scrawler: web scraping library based on selenium
"""
from .scheduler.scheduler import ItemUrlScheduler, DatabaseScheduler
from .worker.downloader import UrlDownloaderWorker
from .worker.crawler import CrawlerWorker
from .worker.database import DatabaseWorker

__version__ = '1.0.0'
__author__ = 'Daniel Afriyie'
__author_email__ = 'afriyiedaniel1@outlook.com'

__all__ = [
    '__version__', '__author__', '__author_email__',
    'ItemUrlScheduler', 'DatabaseScheduler', 'UrlDownloaderWorker', 'CrawlerWorker', 'DatabaseWorker'
]
