"""
Copyright 2021 Daniel Afriyie

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
from .exceptions import SignalException
from .utils import abstractmethod


def receiver(signal, sender):
    def _decorator(func):
        signal.register_dispatch(func)
        sender.register_signal(signal)

    return _decorator


class Signal:
    """
    Base class for all signals
    """

    def __init__(self):
        self._dispatchers = []

    @property
    def dispatchers(self):
        return self._dispatchers

    def register_dispatch(self, dispatch):
        if not callable(dispatch):
            raise SignalException(f"{self.__class__.__name__}: dispatch or signal must be a callable!")
        self._dispatchers.append(dispatch)

    @abstractmethod
    def notify(self, *args, **kwargs):
        pass

    def _dispatch(self, *args, **kwargs):
        for func in self._dispatchers:
            func(*args, **kwargs)

    def remove_dispatch(self, dispatch):
        self._dispatchers.remove(dispatch)
