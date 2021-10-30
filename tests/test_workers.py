import unittest
from random import randint
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from selenium import webdriver

from raccy import UrlDownloaderWorker, DatabaseWorker, CrawlerWorker, WorkersManager
from raccy.core.exceptions import CrawlerException


class BaseTestClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        class UW(UrlDownloaderWorker):
            pass

        class Cw(CrawlerWorker):
            pass

        class Db(DatabaseWorker):
            pass

        cls.UW = UW
        cls.Cw = Cw
        cls.Db = Db

    def get_driver(self):
        driver_path = os.path.join(BASE_DIR, 'chromedriver.exe')
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(executable_path=driver_path, options=options)
        return driver


class TestWorkers(BaseTestClass):

    def test_workers_manager(self):
        mg = WorkersManager()

        with self.assertRaises(CrawlerException):
            mg.start()

        self.assertEqual(mg.dw, self.Db)
        self.assertEqual(mg.uw, self.UW)
        self.assertEqual(mg.cw, self.Cw)

    def test_url_downloader(self):
        with self.assertRaises(CrawlerException):
            self.UW(self.get_driver())

