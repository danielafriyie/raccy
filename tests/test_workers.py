import unittest
from random import randint
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from selenium import webdriver

from raccy import UrlDownloaderWorker, DatabaseWorker, CrawlerWorker
from raccy.core.exceptions import CrawlerException


def get_driver():
    driver_path = os.path.join(BASE_DIR, 'chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    return driver


class Crawler(CrawlerWorker):
    pass


class Db(DatabaseWorker):
    pass


class BaseTest(unittest.TestCase):
    pass


class TestClasses(BaseTest):

    def test_urldownloader_worker(self):
        class UrlD1(UrlDownloaderWorker):
            pass

        class UrlD2(UrlDownloaderWorker):
            start_url = 'start url'

        class Crawler(CrawlerWorker):
            pass

        class Db(DatabaseWorker):
            pass

        with self.assertRaises(CrawlerException):
            UrlD1(get_driver())

        # with self.assertRaises(NotImplementedError):
        #     w1 = UrlDownloaderWorker(get_driver())
        #     w2 = Crawler(get_driver())
        #     w3 = Db()
        #     w1.start()
        #     w2.start()
        #     w3.start()

        url1, url2 = UrlD2(get_driver()), UrlD2(get_driver())
        self.assertEqual(url1, url2)
        self.assertFalse(url1.is_alive())
