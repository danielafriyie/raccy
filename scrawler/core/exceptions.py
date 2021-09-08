"""Global exception and warning module"""


########################################
#       ORM EXCEPTIONS
#######################################
class ModelDoesNotExist(TypeError):
    pass


class InsertError(TypeError):
    pass


class QueryError(TypeError):
    pass


########################################
#       CRAWLER EXCEPTIONS
#######################################
class CrawlerException(TypeError):
    pass
