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
