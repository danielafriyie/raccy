import logging
import os

from scrawler.utils.config import BASE_DIR
from scrawler.utils.utils import check_path_exists


class _Logger:
    """
    Base Logger class
    """

    def __init__(self, name=None, fmt=None, filename=None):
        self._path = os.path.join(BASE_DIR, 'logs')
        if not check_path_exists(self._path):
            os.mkdir(self._path)

        self.name = name if name else __name__
        self.fmt = fmt if fmt else '%(asctime)s:%(levelname)s:%(message)s'
        self.filename = filename if filename else 'event.log'

        self._logger = logging.getLogger(name)
        self._logger.setLevel(level=logging.DEBUG)

        self._log_file_manager()

        formatter = logging.Formatter(self.fmt)
        file_handler = logging.FileHandler(f'{self._path}/{self.filename}')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        self._logger.addHandler(file_handler)

    def _log_file_manager(self):
        """
        check if the log file is more thn 10mb then it deletes it
        """
        path = f'{self._path}/{self.filename}'
        if os.path.exists(path):
            if os.path.getsize(path) > 10485760:
                try:
                    os.remove(path)
                except PermissionError as e:
                    self._logger.exception(e)

    def __call__(self):
        return self._logger


def logger(name=None, fmt=None, filename=None):
    logger_ = _Logger(name, fmt, filename)
    return logger_()
