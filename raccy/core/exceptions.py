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


class ExceptionBase(Exception):
    """Base exception class for all exceptions"""


########################################
#       GLOBAL EXCEPTIONS
#######################################
class ImproperlyConfigured(ExceptionBase):
    pass


#######################################
#       SIGNAL EXCEPTIONS
######################################
class SignalException(ExceptionBase):
    pass


########################################
#       ORM EXCEPTIONS
#######################################
class ModelDoesNotExist(ExceptionBase):
    pass


class InsertError(ExceptionBase):
    pass


class QueryError(ExceptionBase):
    pass


class DatabaseException(ExceptionBase):
    pass


########################################
#       CRAWLER EXCEPTIONS
#######################################
class CrawlerException(ExceptionBase):
    pass


#######################################
#       QUEUE EXCEPTIONS
######################################
class QueueError(ExceptionBase):
    pass
