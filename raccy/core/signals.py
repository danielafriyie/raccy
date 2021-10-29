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
    def _decorator(func):
        signal.register_dispatch(sender, func)
        sender.register_signal(signal)

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
        if not callable(dispatch):
            raise SignalException(f"{self.__class__.__name__}: dispatch or signal must be a callable!")
        try:
            self._dispatchers[sender].append(dispatch)
        except KeyError:
            self._dispatchers[sender] = [dispatch]

    def notify(self, sender, *args, **kwargs):
        self._dispatch(sender, *args, **kwargs)

    def _dispatch(self, sender, *args, **kwargs):
        dispatchers = self._dispatchers[sender]
        for dispatch in dispatchers:
            dispatch(*args, **kwargs)

    def remove_dispatch(self, sender, dispatch):
        self._dispatchers[sender].remove(dispatch)
