"""Global exception and warning module"""


class _BaseException(Exception):
    """Base Exception class for all exception class"""


class ModelDoesNotExist(_BaseException):
    pass


class InsertError(_BaseException):
    pass


class QueryError(_BaseException):
    pass
