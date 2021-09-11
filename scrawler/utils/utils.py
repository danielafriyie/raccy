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
