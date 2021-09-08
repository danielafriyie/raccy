import logging
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _Logger:
    """
    Base Logger class
    """
    __loggers = {}

    def __init__(self, name: str = None, fmt: str = None, filename: str = None):
        self.name = name if name else __name__
        self.fmt = fmt if fmt else '%(asctime)s:%(levelname)s:%(message)s'
        self.filename = filename if filename else os.path.join(BASE_DIR, 'scrawler.log')

    def _create_logger(self):
        _logger = logging.getLogger(self.name)
        _logger.setLevel(level=logging.DEBUG)

        formatter = logging.Formatter(self.fmt)
        file_handler = logging.FileHandler(self.filename)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)

        _logger.addHandler(file_handler)
        _logger.addHandler(stream_handler)

        return _logger

    def _log_file_manager(self):
        """
        check if the log file is more thn 10mb then it deletes it
        """
        raise NotImplementedError(f'{self.__class__.__name__}._log_file_manager() method is not implemented!')

    def __call__(self):
        if self.name in self.__loggers:
            return self.__loggers.get(self.name)
        else:
            _logger = self._create_logger()
            self.__loggers[self.name] = _logger
            return _logger


def logger(name: str = None, fmt: str = None, filename: str = None):
    logger_ = _Logger(name, fmt, filename)
    return logger_()
