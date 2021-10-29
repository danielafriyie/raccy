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
import pathlib
import os
import json
from textwrap import dedent

from raccy.utils.utils import check_path_exists
from raccy.core.utils import abstractmethod
from raccy.core.meta import SingletonMeta
from raccy.core.exceptions import ImproperlyConfigured


class AttrDict:
    __slots__ = ['_attrs']

    def __init__(self, **kwargs):
        self._attrs = kwargs

    @property
    def attrs(self):
        return self._attrs

    def __getattr__(self, item):
        try:
            return self._attrs[item]
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{item}'")

    def __setattr__(self, key, value):
        try:
            object.__setattr__(self, key, value)
        except AttributeError as e:
            if key not in self._attrs:
                raise e
            self._attrs[key] = value

    def __repr__(self):
        return str(self._attrs)


#################################################
#       DATABASE CONFIGURATION
#################################################
class Config(metaclass=SingletonMeta):
    DATABASE = None
    DBMAPPER = None

    def __setattr__(self, key, value):
        if key == 'DATABASE':
            if not isinstance(value, BaseDatabase):
                raise ImproperlyConfigured(f"{self.__class__.__name__}: DATABASE must be an instance of BaseDatabase")
            object.__setattr__(self, 'DBMAPPER', value.DB_MAPPER)
        object.__setattr__(self, key, value)

    def __getattribute__(self, item):
        if item == 'DATABASE' or item == 'DBMAPPER':
            if object.__getattribute__(self, 'DATABASE') is None:
                raise ImproperlyConfigured(f"{self.__class__.__name__}: DATABASE or DBMAPPER is None!")
        return object.__getattribute__(self, item)


_config = Config()


####################################################
#        MIXINS
####################################################
class SignalMixin:
    pass


#####################################################
#       MIGRATIONS
####################################################
class Migration:
    root_path = pathlib.Path('.').absolute()
    migrations_dir = os.path.join(root_path, 'migrations')
    migrations_path = os.path.join(migrations_dir, 'migrations.json')

    def __init__(self, table, fields):
        self._table = table
        self._fields = fields
        self._migrations = self.get_migrations()
        self.mk_migrations_dir()

    def operations(self):
        add_fields = []
        del_fields = []
        existing_fields = self.get_fields()

        if existing_fields is not None:
            # Add fields to add to the table
            for key, val in self._fields.items():
                if key not in existing_fields:
                    add_fields.append((key, val))

            # add fields to delete from the table
            for key, val in existing_fields.items():
                if key not in self._fields:
                    del_fields.append((key, val))
        return add_fields, del_fields

    def get_fields(self):
        try:
            return self._migrations[self._table]
        except KeyError:
            return None

    def mk_migrations_dir(self):
        if not check_path_exists(self.migrations_dir):
            os.mkdir(self.migrations_dir)

    def mk_migrations(self, table, fields):
        self._migrations[table] = fields
        with open(self.migrations_path, 'w') as file:
            json.dump(self._migrations, file)

    def get_migrations(self):
        if not check_path_exists(self.migrations_path, isfile=True):
            return {}
        with open(self.migrations_path) as file:
            migrations = json.load(file)
        return migrations


#####################################################
#       SQL AND QUERY BUILDERS
#####################################################
class BaseSQLBuilder:
    """Base class for all sql and query builders"""

    @property
    def partial_dict(self):
        return self._partial_dict

    @property
    def partial_values(self):
        return self._partial_values

    @property
    def partial_sql(self):
        return self._partial_sql

    def _clean_stmt(self, stmt):
        return dedent(stmt) if stmt else stmt

    @abstractmethod
    def _build_sql(self, *args, **kwargs):
        pass

    @abstractmethod
    def sql(self):
        pass


####################################################
#       DATABASE MAPPER
####################################################
class BaseDbMapper:
    """Base Class for all database mappers"""


class BaseSQLDbMapper(BaseDbMapper):
    """Base Class for all SQL type database mapper"""

    # DATA TYPES AND DEFINITIONS
    PRIMARYKEYFIELD = None
    CHARFIELD = None
    TEXTFIELD = None
    INTEGERFIELD = None
    FLOATFIELD = None
    BOOLEANFIELD = None
    DATEFIELD = None
    DATETIMEFIELD = None
    FOREIGNKEYFIELD = None

    # OPERATIONS FOR USE IN SQL EXPRESSIONS
    GT = ">"
    LT = "<"
    EQ = "="
    NE = "<>"
    GTE = ">="
    LTE = "<="
    LIKE = 'LIKE'
    LIMIT = 'LIMIT'
    DISTINCT = 'DISTINCT'

    @abstractmethod
    def _render_foreign_key_sql_stmt(self, model, field_name, on_field, on_delete='CASCADE', on_update='CASCADE'):
        pass

    @abstractmethod
    def _render_field_sql_stmt(self, type_, max_length=None, null=True, unique=False, default=None):
        pass

    @abstractmethod
    def _render_create_table_sql_stmt(self, table_name, **kwargs):
        pass

    @abstractmethod
    def _render_insert_sql_stmt(self, table_name, **kwargs):
        pass

    @abstractmethod
    def _render_update_sql_stmt(self, table_name, pk, pk_field, **kwargs):
        pass

    @abstractmethod
    def _render_bulk_update_sql_stmt(self, table_name, query_dict, **kwargs):
        pass

    @abstractmethod
    def _render_delete_sql_stmt(self, table_name, **kwargs):
        pass

    @abstractmethod
    def _render_select_sql_stmt(self, table, fields, distinct=False):
        pass

    @abstractmethod
    def _render_select_where_sql_stmt(self, *query):
        pass

    @abstractmethod
    def _render_limit_sql_stmt(self, value):
        pass

    __query_builder__ = None


###################################################
#       DATABASE
###################################################
class BaseDatabase:
    """Base Database class for all databases"""

    @property
    def DB(self):
        return self._db

    @property
    def DB_MAPPER(self):
        return self._mapper


class BaseSQLDatabase(BaseDatabase):
    """Base databae class for all SQL databases"""

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass

    @abstractmethod
    def exec_lastrowid(self, *args, **kwargs):
        pass

    @abstractmethod
    def executescript(self, *args, **kwargs):
        pass

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def fetchone(self, *args, **kwargs):
        pass

    @abstractmethod
    def fetchall(self, *args, **kwargs):
        pass

    @abstractmethod
    def tables(self) -> list:
        pass


####################################################
#       QUERY AND QUERYSET
####################################################
class BaseQuery:
    """Base class for all query and queryset"""

    def __init__(self, model, data):
        self._model = model
        self._data = data
        self._db = _config.DATABASE
        self._mapper = _config.DBMAPPER

    @property
    def get_data(self):
        return self._data

    def __getattr__(self, item):
        try:
            if isinstance(self._data, dict):
                return self._data[item]
        except KeyError:
            raise AttributeError(item)


####################################################
#       MANAGER CLASS
####################################################
class BaseDbManager:
    """Base manager class for handling all databae operations"""
