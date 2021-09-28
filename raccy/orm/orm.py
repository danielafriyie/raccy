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
import sqlite3 as sq
import pathlib
import os
import json

from raccy.core.meta import SingletonMeta
from raccy.core.exceptions import (
    ModelDoesNotExist, InsertError, QueryError, ImproperlyConfigured, DatabaseException
)
from raccy.utils.utils import check_path_exists
from raccy.logger.logger import logger as _logger

_log = _logger()


####################################################
#       UTILITY FUNCTIONS
####################################################
def render_sql_dict(field, operand, value):
    sql_dict = {
        'field': field,
        'operand': operand,
        'value': value
    }
    return sql_dict


def table_exists(table):
    """
    Check if a table exists in the database
    """
    db = _config.DATABASE
    tables = db.tables()
    return table in tables


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

    def create_migrations(self, table, fields):
        migrations = self.get_migrations()
        migrations[table] = fields
        with open(self.migrations_path, 'w') as file:
            json.dump(migrations, file)

    def get_migrations(self):
        if not check_path_exists(self.migrations_path, isfile=True):
            return {}
        with open(self.migrations_path) as file:
            migrations = json.load(file)
        return migrations


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

    # FILTERING DATA
    GT = None
    LT = None
    EQ = None
    NE = None
    IN = None
    GTE = None
    LTE = None
    LIKE = None
    LIMIT = None
    BETWEEN = None
    DISTINCT = None

    def _render_foreign_key_sql_stmt(self, model, field_name, on_field, on_delete='CASCADE', on_update='CASCADE'):
        raise NotImplementedError(f"{self.__class__.__name__}: _render_foreign_key_sql_stmt is not implemented!")

    def _render_field_sql_stmt(self, type_, max_length=None, null=True, unique=False, default=None):
        raise NotImplementedError(f"{self.__class__.__name__}: _render_field_sql_stmt is not implemented!")

    def _render_create_table_sql_stmt(self, table_name, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: _render_create_table_sql_stmt is not implemented!")

    def _render_insert_sql_stmt(self, table_name, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: _render_insert_sql_stmt is not implemented!")

    def _render_update_sql_stmt(self, table_name, pk, pk_field, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: _render_update_sql_stmt is not implemented!")

    def _render_bulk_update_sql_stmt(self, table_name, query_dict, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: _render_bulk_update_sql_stmt is not implemented!")

    def _render_delete_sql_stmt(self, table_name, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: _render_delete_sql_stmt is not implemented!")

    def _render_select_sql_stmt(self, table, fields, distinct=False):
        raise NotImplementedError(f"{self.__class__.__name__}: _render_select_sql_stmt is not implemented!")

    def _render_select_where_sql_stmt(self, *query):
        raise NotImplementedError(f"{self.__class__.__name__}: _render_select_where_sql_stmt is not implemented!")

    def _render_limit_sql_stmt(self, value):
        raise NotImplementedError(f"{self.__class__.__name__}: _render_limit_sql_stmt is not implemented!")

    __interim_sql__ = None
    __interim_values__ = None
    __sql_dict__ = None


class SQLiteDbMapper(BaseSQLDbMapper):
    """Mapper for SQLite Database"""
    PRIMARYKEYFIELD = "INTEGER PRIMARY KEY AUTOINCREMENT"
    CHARFIELD = "VARCHAR"
    TEXTFIELD = "TEXT"
    INTEGERFIELD = "INTEGER"
    FLOATFIELD = "DOUBLE"
    BOOLEANFIELD = "BOOLEAN"
    DATEFIELD = "DATE"
    DATETIMEFIELD = "DATETIME"
    FOREIGNKEYFIELD = "INTEGER"

    GT = ">"
    LT = "<"
    EQ = "="
    NE = "<>"
    GTE = ">="
    LTE = "<="
    LIKE = 'LIKE'
    LIMIT = 'LIMIT'
    DISTINCT = 'DISTINCT'

    def _join_sql_stmt(self, *statements, values=None):
        stmts = ''
        for stmt in statements:
            stmts += stmt
        self.__interim_sql__ = stmts
        self.__interim_values__ = values
        return self.__interim_sql__, self.__interim_values__

    def _render_sql_stmt(self, *statements, values=None):
        sql, values = self._join_sql_stmt(*statements, values=values)
        sql = sql + ';'
        return sql, values

    def _render_foreign_key_sql_stmt(self, model, field_name, on_field, on_delete='CASCADE', on_update='CASCADE'):
        sql = f"""
            FOREIGN KEY ({field_name})
            REFERENCES {model} ({on_field}) 
                ON UPDATE {on_update}
                ON DELETE {on_delete}
        """
        return sql

    def _render_field_sql_stmt(self, type_, max_length=None, null=True, unique=False, default=None):
        sql = f'{type_}'
        if max_length:
            sql = sql + f' ({max_length})'
        if null is False:
            sql = sql + ' NOT NULL'
        if unique:
            sql = sql + ' UNIQUE'
        if default is False or default:
            sql = sql + f' DEFAULT {default}'
        return sql

    def _render_create_table_sql_stmt(self, table_name, **kwargs):
        fields = []
        foreign_key_sql = []
        migration_fields = {}
        migration = Migration(table_name, kwargs)
        add_fields, del_fields = migration.operations()
        if not table_exists(table_name):
            for name, field in kwargs.items():
                if isinstance(field, ForeignKeyField):
                    foreign_key_sql.append(field._foreign_key_sql(name))
                fields.append(f"{name} {field.sql}")
                migration_fields[name] = field.type_string

            fields = ', '.join(fields)
            if foreign_key_sql:
                fields = fields + ','
            foreign_key_sql = ', '.join(foreign_key_sql) if foreign_key_sql else ''

            sql = f"""
                    PRAGMA foreign_keys = ON;

                    CREATE TABLE IF NOT EXISTS {table_name} (
                        {fields} 
                        {foreign_key_sql}
                    );
                """
            migration.create_migrations(table_name, migration_fields)
            return sql

        if del_fields:
            raise DatabaseException(
                f"{table_name}: sqlite database does not support deleting field after table is created."
            )

        if add_fields:
            for name, field in add_fields:
                if isinstance(field, ForeignKeyField):
                    raise DatabaseException(
                        f"{table_name}: sqlite database does not support adding foreign key"
                        f" field after table is created."
                    )
                if isinstance(field, PrimaryKeyField):
                    raise DatabaseException(f"{table_name}: cannot add primary key field after table is created.")
                fields.append(f"{name} {field.sql}")
                migration_fields[name] = field.type_string

            sql = ""
            for f in fields:
                sql += f"""
                        ALTER TABLE {table_name}
                        ADD COLUMN {f};
                    """
            existing_fields = migration._migrations[table_name]
            existing_fields.update(migration_fields)
            migration.create_migrations(table_name, existing_fields)
            return sql

    def _render_insert_sql_stmt(self, table_name, **kwargs):
        insert_sql = 'INSERT INTO {name} ({fields}) VALUES ({placeholders});'
        fields, values, placeholders = [], [], []

        for key, val in kwargs.items():
            fields.append(key)
            placeholders.append('?')
            values.append(val)

        sql = insert_sql.format(name=table_name, fields=', '.join(fields), placeholders=', '.join(placeholders))
        return sql, values

    def _render_update_sql_stmt(self, table_name, pk, pk_field, **kwargs):
        update_sql = "UPDATE {table} SET {placeholders} WHERE {query};"
        query = f"{pk_field}=?"
        values, placeholders = [], []

        for key, val in kwargs.items():
            values.append(val)
            placeholders.append(f"{key}=?")

        values.append(pk)
        sql = update_sql.format(table=table_name, placeholders=', '.join(placeholders), query=query)
        return sql, values

    def _render_bulk_update_sql_stmt(self, table_name, **kwargs):
        update_sql = 'UPDATE {table} SET {placeholders}'

        placeholders, values = [], []

        for key, val in kwargs.items():
            placeholders.append(f"{key}=?")
            values.append(val)

        sql = update_sql.format(table=table_name, placeholders=', '.join(placeholders))
        values = values

        if self.__interim_values__ and self.__sql_dict__:
            self.__interim_sql__ = sql
            sql, _values = self._render_select_where_sql_stmt(*self.__sql_dict__)
            values += _values

        return sql, values

    def _render_delete_sql_stmt(self, table_name, **kwargs):
        delete_sql = 'DELETE FROM {table} WHERE {query};'
        query, values = [], []

        for key, val in kwargs.items():
            values.append(val)
            query.append(f'{key}=?')

        sql = delete_sql.format(table=table_name, query=' AND '.join(query))
        return sql, values

    def _render_select_sql_stmt(self, table, fields, distinct=False):
        select_sql = 'SELECT {distinct} {fields} FROM {table}'
        sql = select_sql.format(
            table=table,
            fields=', '.join(fields),
            distinct=self.DISTINCT if distinct else ''
        )
        return self._render_sql_stmt(sql)

    def _render_select_where_sql_stmt(self, *args):
        where_sql = ' WHERE {query}'
        self.__sql_dict__ = args

        query, operators, values = [], [], []
        for d in args:
            field = d['field']
            operator = d['operand']
            value = d['value']
            query.append(f"{field} {operator} ?")
            values.append(value)

        return self._render_sql_stmt(self.__interim_sql__, where_sql.format(query=' AND '.join(query)), values=values)

    def _render_limit_sql_stmt(self, value):
        limit_sql = ' {limit} {value} '.format(limit=self.LIMIT, value=value)
        return self._render_sql_stmt(self.__interim_sql__, limit_sql, values=self.__interim_values__)


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

    def execute(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: execute is not implemented")

    def exec_lastrowid(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: exec_lastrowid is not implemented")

    def executescript(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: executescript is not implemented")

    def commit(self):
        raise NotImplementedError(f"{self.__class__.__name__}: commit is not implemented")

    def fetchone(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: fetchone is not implemented")

    def fetchall(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: fetchall is not implemented")

    def tables(self) -> list:
        raise NotImplementedError(f"{self.__class__.__name__}: tables is not implemented")


class SQLiteDatabase(BaseSQLDatabase):

    def __init__(self, db_path, check_same_thread=False, **kwargs):
        self._db = sq.connect(
            database=db_path,
            check_same_thread=check_same_thread,
            **kwargs
        )
        self._mapper = SQLiteDbMapper()

    def execute(self, *args, **kwargs):
        return self._db.execute(*args, **kwargs)

    def exec_lastrowid(self, *args, **kwargs):
        cursor = self._db.execute(*args, **kwargs)
        return cursor.lastrowid

    def executescript(self, *args, **kwargs):
        return self._db.executescript(*args, **kwargs)

    def commit(self):
        self._db.commit()

    def fetchone(self, *args, **kwargs):
        qs = self._db.execute(*args, **kwargs)
        return qs.fetchone()

    def fetchall(self, *args, **kwargs):
        qs = self._db.execute(*args, **kwargs)
        return qs.fetchall()

    def tables(self):
        sql = "SELECT name FROM sqlite_master WHERE type='table';"
        qs = self.fetchall(sql)
        tables = [x[0] for x in qs]
        return tables


#####################################################
#       MODEL FIELDS
####################################################
class Field:
    """Base class for all field types"""

    def __init__(self, type_, max_length=None, null=True, unique=False, default=None):
        self._mapper = _config.DBMAPPER
        self.type_string = type_
        self._type = getattr(self._mapper, type_)
        self._max_length = max_length
        self._null = null
        self._unique = unique
        self._default = default
        self._field_name = None

    @property
    def sql(self):
        _sql = self._mapper._render_field_sql_stmt(
            self._type,
            max_length=self._max_length,
            null=self._null,
            unique=self._unique,
            default=self._default
        )
        return _sql

    @property
    def _name(self):
        return self.__class__.__name__

    def _render_sql_dict(self, operand, other):
        return render_sql_dict(self._field_name, operand, other)

    def __gt__(self, other):
        return self._render_sql_dict(self._mapper.GT, other)

    def __lt__(self, other):
        return self._render_sql_dict(self._mapper.LT, other)

    def __eq__(self, other):
        return self._render_sql_dict(self._mapper.EQ, other)

    def __le__(self, other):
        return self._render_sql_dict(self._mapper.LTE, other)

    def __ge__(self, other):
        return self._render_sql_dict(self._mapper.GTE, other)

    def __ne__(self, other):
        return self._render_sql_dict(self._mapper.NE, other)

    def like(self, pattern):
        return self._render_sql_dict(self._mapper.LIKE, pattern)


class PrimaryKeyField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__("PRIMARYKEYFIELD", *args, **kwargs)


class CharField(Field):

    def __init__(self, max_length=120, *args, **kwargs):
        super().__init__("CHARFIELD", max_length, *args, **kwargs)


class TextField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__("TEXTFIELD", *args, **kwargs)


class IntegerField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__("INTEGERFIELD", *args, **kwargs)


class FloatField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__("FLOATFIELD", *args, **kwargs)


class BooleanField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__("BOOLEANFIELD", *args, **kwargs)


class DateField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__("DATEFIELD", *args, **kwargs)


class DateTimeField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__("DATETIMEFIELD", *args, **kwargs)


class ForeignKeyField(Field):

    def __init__(self, model, on_field, on_delete='CASCADE', on_update='CASCADE'):
        super().__init__("FOREIGNKEYFIELD", null=False)
        self.__model = model
        self.__on_field = on_field
        self.__on_delete = on_delete
        self.__on_update = on_update

    def _foreign_key_sql(self, field_name):
        sql = self._mapper._render_foreign_key_sql_stmt(
            model=self.__model.__table_name__,
            field_name=field_name,
            on_field=self.__on_field,
            on_delete=self.__on_delete,
            on_update=self.__on_update
        )
        return sql


####################################################
#       QUERY AND QUERYSET
####################################################
class BaseQuery:
    """Base class for all query and queryset"""

    def __init__(self, data):
        self._data = data
        self._db = _config.DATABASE
        self._mapper = _config.DBMAPPER

    @property
    def get_data(self):
        return self._data

    def __getattribute__(self, item):
        data = object.__getattribute__(self, '_data')
        if isinstance(data, dict) and item in data:
            return data[item]
        return object.__getattribute__(self, item)


class QuerySet(BaseQuery):

    def update(self, **kwargs):
        sql, values = self._mapper._render_update_sql_stmt(self._table, self.pk, self._pk_field, **kwargs)
        self._db.execute(sql, values)
        self._db.commit()


class Query(BaseQuery):
    """
    Query class for making complex and advance queries
    """

    def __init__(self, data, table, fields=None, **kwargs):
        super().__init__(data)
        self._table = table
        self._fields = fields
        self._kwds = kwargs
        self.__state = None

    @property
    def state(self):
        return self.__state

    @classmethod
    def select(cls, table, fields, distinct=False):
        db = _config.DATABASE
        mapper = _config.DBMAPPER
        sql, _ = mapper._render_select_sql_stmt(table, fields, distinct=distinct)
        try:
            data = db.fetchall(sql)
            klass = cls(data, table, fields)
            klass.set_state('select')
        except sq.OperationalError as e:
            raise QueryError(str(e))
        return klass

    @classmethod
    def _from_query(cls, data, table, fields=None, **kwargs):
        return cls(data, table, fields, **kwargs)

    def set_state(self, state):
        self.__state = state

    def where(self, *args):
        if self.__state != 'select':
            raise QueryError(f"{self._table}: select method must be called before where method!")

        if self.__state == 'where':
            raise QueryError(f"{self._table}: where method called more than one!")

        sql, values = self._mapper._render_select_where_sql_stmt(*args)
        data = self._db.fetchall(sql, values)
        klass = self._from_query(data, self._table, self._fields)
        klass.set_state('where')
        return klass

    def limit(self, value):
        sql, values = self._mapper._render_limit_sql_stmt(value)

        if values:
            data = self._db.fetchall(sql, values)
        else:
            data = self._db.fetchall(sql)
        return self._from_query(data, self._table)

    def bulk_update(self, **kwargs):
        if self.__state not in ('select', 'where'):
            raise QueryError(f"{self._table}: select or where method must be called before bulk_update method!")

        sql, values = self._mapper._render_bulk_update_sql_stmt(self._table, **kwargs)
        self._db.execute(sql, values)
        self._db.commit()


####################################################
#       MODEL BASE, MANAGER, AND MODEL CLASS
####################################################
class BaseDbManager:
    """Base manager class for handling all databae operations"""


class SQLModelManager(BaseDbManager):
    """Manager for handling all SQL database operations"""

    def __init__(self, model):
        self._model = model
        self._mapping = model.__mappings__
        self._db = _config.DATABASE
        self._mapper = _config.DBMAPPER

    @property
    def table_name(self):
        return self._model.__table_name__

    @property
    def _table_fields(self):
        fields = [x[0] for x in self._mapping.items()]
        return fields

    def all(self):
        table_fields = self._table_fields
        pk_field = self._get_primary_key_field()
        pk_idx = table_fields.index(pk_field)
        qs = self.select(table_fields).get_data
        datas = map(lambda x: self.get(**{pk_field: x[pk_idx]}), qs)
        return datas

    def _create_table(self, commit=True):
        sql = self._mapper._render_create_table_sql_stmt(self.table_name, **self._mapping)
        if sql is not None:
            self._db.executescript(sql)
            if commit:
                self._db.commit()

    def _get_primary_key_field(self):
        return self._model.__pk__

    def create(self, **kwargs):
        return self.insert(**kwargs)

    def insert(self, **kwargs):
        try:
            sql, values = self._mapper._render_insert_sql_stmt(self.table_name, **kwargs)
            lastrowid = self._db.exec_lastrowid(sql, values)
            self._db.commit()
        except sq.OperationalError as e:
            raise InsertError(str(e))
        return lastrowid

    def bulk_insert(self, *data):
        for d in data:
            if not isinstance(d, dict):
                raise InsertError(f"bulk_insert accepts only dictionary values!")
            sql, values = self._mapper._render_insert_sql_stmt(self.table_name, **d)
            self._db.execute(sql, values)
        self._db.commit()

    def delete(self, **kwargs):
        sql, values = self._mapper._render_delete_sql_stmt(self.table_name, **kwargs)
        self._db.execute(sql, values)
        self._db.commit()

    def get(self, **kwargs):
        args = []
        for key, val in kwargs.items():
            sql_dict = render_sql_dict(key, '=', val)
            args.append(sql_dict)

        qs = self.select(['*']).where(*args)

        try:
            query_set = qs.get_data[0]
            data = dict(zip(self._table_fields, query_set))
            pk_field = self._get_primary_key_field()
            data['_table'] = self.table_name
            data['pk'] = data[pk_field]
            data['id'] = data[pk_field]
            data['_pk_field'] = pk_field
            query_class = QuerySet(data)
        except TypeError:
            raise ModelDoesNotExist(f"{self.table_name}: No model matches the given query!")

        return query_class

    def select(self, fields, distinct=False):
        return Query.select(self.table_name, fields, distinct=distinct)

    def raw(self, *args, **kwargs):
        return self._db.execute(*args, **kwargs)


class SQLModelBaseMetaClass(type):
    """Metaclass for all models."""

    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]

    def _get_meta_data(cls, attr):
        _abstract = False
        _create_table = True
        _table_name = None

        if 'Meta' in attr:
            _meta = attr['Meta']
            _abstract = getattr(_meta, 'abstract', _abstract)
            _table_name = getattr(_meta, 'table_name', _table_name)
            _create_table = getattr(_meta, 'create_table', _create_table)
            del attr['Meta']

        class _Meta:
            abstract = _abstract
            table_name = _table_name
            create_table = _create_table

        return _Meta

    def __new__(mcs, name, base, attr):
        if base:
            for cls in base:
                if hasattr(cls, '__mappings__'):
                    attr.update(cls.__mappings__)

        # Determine model fields
        mappings = {}
        has_primary_key = False
        primary_key_field = None
        for key, value in attr.items():
            if isinstance(value, PrimaryKeyField):
                has_primary_key = True
                primary_key_field = key
            if isinstance(value, Field):
                value._field_name = key
                mappings[key] = value

        # Delete fields that are already stored in mapping
        for key in mappings.keys():
            del attr[key]

        # Model metadata
        _meta = mcs._get_meta_data(mcs, attr)

        # Checks if model has PrimaryKeyField
        # if False, then it will automatically create one
        if has_primary_key is False and _meta.abstract is False:
            mappings['pk'] = PrimaryKeyField()
            primary_key_field = 'pk'

        # Save mapping between attribute and columns and table name
        attr['_meta'] = _meta
        attr['__mappings__'] = mappings
        attr['__table_name__'] = _meta.table_name if _meta.table_name else name.lower()
        attr['__pk__'] = primary_key_field
        new_class = type.__new__(mcs, name, base, attr)

        return new_class


class Model(metaclass=SQLModelBaseMetaClass):
    """Model class for SQL Databases"""

    class Meta:
        abstract = True

    def __init_subclass__(cls, **kwargs):
        # If the model is not abstract model then
        # create database table immediately the Model class is subclassed
        if cls._meta.abstract is False:
            cls.objects = SQLModelManager(cls)
            if cls._meta.create_table:
                cls.objects._create_table()

    def __getattribute__(self, item):
        mappings = object.__getattribute__(self, '__mappings__')
        if item in mappings:
            return mappings[item]
        return object.__getattribute__(self, item)
