import unittest
from random import randint
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from raccy import DatabaseQueue, ItemUrlQueue
from raccy.core.exceptions import QueueError


class QueueTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ds1, cls.ds2 = DatabaseQueue(), DatabaseQueue()
        cls.is1, cls.is2 = ItemUrlQueue(), ItemUrlQueue()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_single_instance(self):
        assert self.ds1 == self.ds2
        assert self.ds1.get_queue == self.ds2.get_queue
        assert self.ds1.queue() == self.ds2.queue()
        assert self.is1 == self.is2
        assert self.is2.get_queue == self.is1.get_queue
        assert self.is1.queue() == self.is2.queue()
        for _ in range(500):
            v = dict(rand=randint(5, 100))
            self.ds1.put(v)
            self.is2.put(v)
        assert self.ds1.qsize() == self.ds2.qsize()
        assert self.is1.qsize() == self.is1.qsize()
        for _ in range(250):
            v = dict(rand=randint(5, 100))
            self.ds2.put(v)
            self.ds1.put(v)
        self.assertEqual(self.ds1.queue(), self.ds2.queue())
        self.assertEqual(self.ds1.qsize(), self.ds2.qsize())
        self.assertEqual(self.is1.queue(), self.is2.queue())
        self.assertEqual(self.is1.qsize(), self.is2.qsize())
        for _ in range(5):
            v = {'rand': randint(5, 100)}
            self.is2.put(v)
        for _ in range(50):
            self.is1.get()
            self.ds1.get()
            self.is1.task_done()
            self.ds1.task_done()
        self.assertEqual(self.ds1.queue(), self.ds2.queue())
        self.assertEqual(self.ds1.qsize(), self.ds2.qsize())
        self.assertEqual(self.is1.queue(), self.is2.queue())
        self.assertEqual(self.is1.qsize(), self.is2.qsize())

        with self.assertRaises(QueueError):
            self.ds2.put(['this is an item'])
            self.ds1.put('item')

    def test_different_subclass_instance(self):
        for _ in range(2):
            v = dict(rand=randint(5, 100))
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
