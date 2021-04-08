import os
from random import randint
from time import sleep


def check_path_exists(path, isfile=False):
    return os.path.isfile(path) if isfile else os.path.exists(path)


def random_delay(a, b):
    sleep(randint(a, b))


def download_delay(a=1, b=5):
    return random_delay(a, b)


def download_delay_per_block(a=1, b=10):
    return random_delay(a, b)
