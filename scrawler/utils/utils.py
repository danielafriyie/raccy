import os
from random import randint
from time import sleep


def check_path_exists(path: str, isfile=False) -> bool:
    return os.path.isfile(path) if isfile else os.path.exists(path)


def random_delay(a: int, b: int) -> None:
    sleep(randint(a, b))


def download_delay(a=1, b=5):
    return random_delay(a, b)


def download_delay_per_block(a=1, b=10):
    return random_delay(a, b)


def check_has_attr(obj, attr):
    if not hasattr(obj, attr):
        raise AttributeError(f'{obj} does not have {attr} attribute or method.')
