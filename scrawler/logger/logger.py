import logging


class _Logger:
    """
    Base Logger class
    """

    def __init__(self, name: str = None, fmt: str = None, filename: str = None):
        self.name = name if name else __name__
        self.fmt = fmt if fmt else '%(asctime)s:%(levelname)s:%(message)s'
        self.filename = filename if filename else 'scrawler.log'

        self._logger = logging.getLogger(name)
        self._logger.setLevel(level=logging.DEBUG)

        # self._log_file_manager()

        formatter = logging.Formatter(self.fmt)
        file_handler = logging.FileHandler(self.filename)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)

        self._logger.addHandler(file_handler)
        self._logger.addHandler(stream_handler)

    def _log_file_manager(self):
        """
        check if the log file is more thn 10mb then it deletes it
        """
        raise NotImplementedError(f'{self.__class__.__name__}._log_file_manager() method is not implemented!')

    def __call__(self):
        return self._logger


def logger(name: str = None, fmt: str = None, filename: str = None):
    logger_ = _Logger(name, fmt, filename)
    return logger_()
