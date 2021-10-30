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


def receiver(signal, sender):
    def _decorator(dispatch):
        signal.register_dispatch(sender, dispatch)
        sender.register_signal(signal)

    return _decorator


def execute_or_debug(func):
    def _decorator(self, sender, *args, **kwargs):
        try:
            return func(self, sender, *args, **kwargs)
        except KeyError:
            raise SignalException(f"{self.__class__.__name__} has no registered dispatch <{sender}>")

    return _decorator


class Signal:
    """
    Base class for all signals
    """

    def __init__(self):
        self._dispatchers = {}

    @property
    def dispatchers(self):
        return self._dispatchers

    def register_dispatch(self, sender, dispatch):
        try:
            self._dispatchers[sender].append(dispatch)
        except KeyError:
            self._dispatchers[sender] = [dispatch]

    def notify(self, sender, *args, **kwargs):
        self._dispatch(sender, *args, **kwargs)

    @execute_or_debug
    def _dispatch(self, sender, *args, **kwargs):
        dispatchers = self._dispatchers[sender]
        for dispatch in dispatchers:
            dispatch(*args, **kwargs)

    @execute_or_debug
    def remove_dispatch(self, sender, dispatch):
        self._dispatchers[sender].remove(dispatch)
