import unittest
from random import randint
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from scrawler import ItemUrlScheduler, DatabaseScheduler


class TestSingleton(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ds1, cls.ds2, cls.ds3 = DatabaseScheduler(), DatabaseScheduler(), DatabaseScheduler()
        cls.is1, cls.is2 = ItemUrlScheduler(), ItemUrlScheduler()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_single_instance(self):
        self.assertEqual(self.ds1, self.ds2)
        self.assertEqual(self.ds1.get_queue, self.ds2.get_queue)
        self.assertEqual(self.is1, self.is2)
        self.assertEqual(self.is1.get_queue, self.is2.get_queue)
        for _ in range(500):
            v = randint(5, 100)
            self.ds1.put(v)
            self.ds3.put(v)
            self.is2.put(v)
            self.is1.put(v)
        self.assertEqual(self.ds1.queue(), self.ds2.queue())
        self.assertEqual(self.ds1.qsize(), self.ds2.qsize())
        self.assertEqual(self.is1.queue(), self.is2.queue())
        self.assertEqual(self.is1.qsize(), self.is2.qsize())
        for _ in range(250):
            v = randint(5, 100)
            self.ds2.put(v)
            self.ds1.put(v)
        self.assertEqual(self.ds1.queue(), self.ds2.queue())
        self.assertEqual(self.ds1.qsize(), self.ds2.qsize())
        self.assertEqual(self.is1.queue(), self.is2.queue())
        self.assertEqual(self.is1.qsize(), self.is2.qsize())
        for _ in range(5):
            v = randint(5, 100)
            self.ds3.put(v)
            self.is2.put(v)
        for _ in range(50):
            self.ds3.get()
            self.is1.get()
            self.ds1.get()
            self.ds3.task_done()
            self.is1.task_done()
            self.ds1.task_done()
        self.assertEqual(self.ds1.queue(), self.ds2.queue())
        self.assertEqual(self.ds1.qsize(), self.ds2.qsize())
        self.assertEqual(self.ds3.qsize(), self.ds2.qsize())
        self.assertEqual(self.ds3.queue(), self.ds2.queue())
        self.assertEqual(self.is1.queue(), self.is2.queue())
        self.assertEqual(self.is1.qsize(), self.is2.qsize())
        # self.assertEqual(self.ds1.items_enqueued, self.ds2.items_enqueued)

    def test_different_subclass_instance(self):
        for _ in range(2):
            v = randint(5, 100)
            self.ds1.put(v)
            self.ds2.put(v)
            self.is1.put(v)
        self.assertNotEqual(self.ds1, self.is1)
        self.assertNotEqual(self.ds1.get_queue, self.is1.get_queue)
        self.assertNotEqual(self.ds1, self.is2)
        self.assertNotEqual(self.ds1.get_queue, self.is2.get_queue)
        self.assertNotEqual(self.ds2, self.is1)
        self.assertNotEqual(self.ds2.get_queue, self.is1.get_queue)
        self.assertNotEqual(self.ds2, self.is2)
        self.assertNotEqual(self.ds2.get_queue, self.is2.get_queue)
        self.assertNotEqual(self.ds3.get_queue, self.is2.get_queue)
        self.assertNotEqual(self.ds1.qsize(), self.is1.qsize())
        self.assertNotEqual(self.ds1.qsize(), self.is2.qsize())
        self.assertNotEqual(self.ds2.qsize(), self.is1.qsize())
        self.assertNotEqual(self.ds2.qsize(), self.is2.qsize())
        self.assertNotEqual(self.ds1.queue(), self.is1.queue())
        self.assertNotEqual(self.ds1.queue(), self.is2.queue())
        self.assertNotEqual(self.ds2.queue(), self.is1.queue())
        self.assertNotEqual(self.ds2.queue(), self.is2.queue())


if __name__ == '__main__':
    unittest.main()
