"""Global exception and warning module"""


########################################
#       GLOBAL EXCEPTIONS
#######################################
class ImproperlyConfigured(ValueError):
    pass


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


#######################################
#       SCHEDULER EXCEPTIONS
######################################
class SchedulerError(TypeError):
    pass
