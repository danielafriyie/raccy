"""
Copyright [2021] [Daniel Afriyie]

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

from raccy.core.meta import SingletonMeta
from raccy.core.exceptions import ModelDoesNotExist, InsertError, QueryError, ImproperlyConfigured


#################################################
#       DATABASE CONFIGURATION
#################################################
class Config(metaclass=SingletonMeta):
    DATABASE = None
    DBMAPPER = None

    def __setattr__(self, key, value):
        if key == 'DATABASE':
            if not isinstance(value, BaseDatabase):
                raise ImproperlyConfigured(f"{self.__class__.__name__}: DATABASE must be an instance of BaseDatabase!")
            object.__setattr__(self, 'DBMAPPER', value.DB_MAPPER)
        object.__setattr__(self, key, value)

    def __getattribute__(self, item):
        if item == 'DATABASE' or item == 'DBMAPPER':
            if object.__getattribute__(self, 'DATABASE') is None:
                raise ImproperlyConfigured(f"{self.__class__.__name__}: DATABASE or DBMAPPER is None!")
        return object.__getattribute__(self, item)


####################################################
#       DATABASE MAPPER
####################################################
class BaseDbMapper:
    """Base Class for all database mappers"""


class BaseSQLDbMapper(BaseDbMapper):
    """Base Class for all SQL type database mapper"""

    PRIMARYKEYFIELD = None
    CHARFIELD = None
    TEXTFIELD = None
    INTEGERFIELD = None
    FLOATFIELD = None
    BOOLEANFIELD = None
    DATEFIELD = None
    DATETIMEFIELD = None
    FOREIGNKEYFIELD = None

    def _get_foreign_key_sql(self, model, field_name, on_field, on_delete='CASCADE', on_update='CASCADE'):
        raise NotImplementedError(f"{self.__class__.__name__}: _get_foreign_key_sql is not implemented!")

    def _get_field_sql(self, type_, max_length=None, null=True, unique=False, default=None):
        raise NotImplementedError(f"{self.__class__.__name__}: _get_field_sql is not implemented!")

    def _get_create_table_sql(self, table_name, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: _get_create_table_sql is not implemented!")

    def _get_insert_sql(self, table_name, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: _get_insert_sql is not implemented!")

    def _get_update_sql(self, table_name, pk, pk_field, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: _get_update_sql is not implemented!")

    def _get_bulk_update_sql(self, table_name, query_dict, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: _get_bulk_update_sql is not implemented!")

    def _get_delete_sql(self, table_name, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: _get_delete_sql is not implemented!")

    def _get_select_sql(self, table, fields):
        raise NotImplementedError(f"{self.__class__.__name__}: _get_select_sql is not implemented!")

    def _get_select_where_sql(self, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: _get_select_where_sql is not implemented!")


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

    def _get_foreign_key_sql(self, model, field_name, on_field, on_delete='CASCADE', on_update='CASCADE'):
        sql = f"""
            FOREIGN KEY ({field_name})
            REFERENCES {model} ({on_field}) 
                ON UPDATE {on_update}
                ON DELETE {on_delete}
        """
        return sql

    def _get_field_sql(self, type_, max_length=None, null=True, unique=False, default=None):
        sql = f'{type_}'
        if max_length:
            sql = sql + f' ({max_length})'
        if null is False:
            sql = sql + ' NOT NULL'
        if unique:
            sql = sql + ' UNIQUE'
        if default:
            sql = sql + f' DEFAULT {default}'
        return sql

    def _get_create_table_sql(self, table_name, **kwargs):
        fields = []
        foreign_key_sql = []

        for name, field in kwargs.items():
            if isinstance(field, ForeignKeyField):
                foreign_key_sql.append(field._foreign_key_sql(name))
            fields.append(f"{name} {field.sql}")

        fields = ', '.join(fields)
        if foreign_key_sql:
            fields = fields + ','
        foreign_key_sql = ', '.join(foreign_key_sql) if foreign_key_sql else ''

        sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {fields} 
                    {foreign_key_sql}
                );
            """
        return sql

    def _get_insert_sql(self, table_name, **kwargs):
        insert_sql = 'INSERT INTO {name} ({fields}) VALUES ({placeholders});'
        fields, values, placeholders = [], [], []

        for key, val in kwargs.items():
            fields.append(key)
            placeholders.append('?')
            values.append(val)

        sql = insert_sql.format(name=table_name, fields=', '.join(fields), placeholders=', '.join(placeholders))
        return sql, values

    def _get_update_sql(self, table_name, pk, pk_field, **kwargs):
        update_sql = "UPDATE {table} SET {placeholders} WHERE {query};"
        query = f"{pk_field}=?"
        values, placeholders = [], []

        for key, val in kwargs.items():
            values.append(val)
            placeholders.append(f"{key}=?")

        values.append(pk)
        sql = update_sql.format(table=table_name, placeholders=', '.join(placeholders), query=query)
        return sql, values

    def _get_bulk_update_sql(self, table_name, query_dict, **kwargs):
        update_sql = 'UPDATE {table} SET {placeholders} WHERE {query}'
        placeholders, values = [], []
        query_vals, query_placeholders = [], []

        for key, val in query_dict.items():
            query_placeholders.append(f"{key}=?")
            query_vals.append(val)

        for key, val in kwargs.items():
            placeholders.append(f"{key}=?")
            values.append(val)

        sql = update_sql.format(table=table_name, placeholders=', '.join(placeholders),
                                query=' AND '.join(query_placeholders))
        values = values + query_vals
        return sql, values

    def _get_delete_sql(self, table_name, **kwargs):
        delete_sql = 'DELETE FROM {table} WHERE {query};'
        query, values = [], []

        for key, val in kwargs.items():
            values.append(val)
            query.append(f'{key}=?')

        sql = delete_sql.format(table=table_name, query=' AND '.join(query))
        return sql, values

    def _get_select_sql(self, table, fields):
        select_sql = 'SELECT {fields} FROM {table};'
        sql = select_sql.format(table=table, fields=', '.join(fields))
        return sql

    def _get_select_where_sql(self, table_name, fields, **kwargs):
        select_sql = 'SELECT {fields} FROM {table} WHERE {query};'

        query, values = [], []
        for key, val in kwargs.items():
            values.append(val)
            query.append(f"{key}=?")

        sql = select_sql.format(fields=', '.join(fields), table=table_name, query=' AND '.join(query))
        return sql, values


####################################################
#       DATABASE
###################################################
class BaseDatabase:
    """Base Database class for all databases"""

    @property
    def DB(self):
        return self._db

    @property
    def DB_MAPPER(self):
        return self._db_mapper


class BaseSQLDatabase(BaseDatabase):
    """Base databae class for all SQL databases"""

    def execute(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: execute is not implemented")

    def exec_lastrowid(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: exec_lastrowid is not implemented")

    def commit(self):
        raise NotImplementedError(f"{self.__class__.__name__}: commit is not implemented")

    def fetchone(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: fetchone is not implemented")

    def fetchall(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}: fetchall is not implemented")


class SQLiteDatabase(BaseSQLDatabase):

    def __init__(self, db_path, check_same_thread=False, **kwargs):
        self._db = sq.connect(
            database=db_path,
            check_same_thread=check_same_thread,
            **kwargs
        )
        self._db_mapper = SQLiteDbMapper()

    def execute(self, *args, **kwargs):
        self._db.execute(*args, **kwargs)

    def exec_lastrowid(self, *args, **kwargs):
        cursor = self._db.execute(*args, **kwargs)
        return cursor.lastrowid

    def commit(self):
        self._db.commit()

    def fetchone(self, *args, **kwargs):
        qs = self._db.execute(*args, **kwargs)
        return qs.fetchone()

    def fetchall(self, *args, **kwargs):
        qs = self._db.execute(*args, **kwargs)
        return qs.fetchall()


#####################################################
#       MODEL FIELDS
####################################################
class Field:
    """Base class for all field types"""

    def __init__(self, type_, max_length=None, null=True, unique=False, default=None):
        self._db_mapper = Config().DBMAPPER
        self._type = getattr(self._db_mapper, type_)
        self._max_length = max_length
        self._null = null
        self._unique = unique
        self._default = default

    @property
    def sql(self):
        _sql = self._db_mapper._get_field_sql(
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
        sql = self._db_mapper._get_foreign_key_sql(
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
        self._db = Config().DATABASE
        self._db_mapper = Config().DBMAPPER

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
        sql, values = self._db_mapper._get_update_sql(self._table, self._pk, self._pk_field, **kwargs)
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
    def select(cls, table, fields):
        db = Config().DATABASE
        db_mapper = Config().DBMAPPER
        sql = db_mapper._get_select_sql(table, fields)
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

    def where(self, **kwargs):
        if self._fields is None:
            raise QueryError(f"{self._table}: select method must be called before where method!")

        sql, values = self._db_mapper._get_select_where_sql(self._table, self._fields, **kwargs)
        data = self._db.fetchall(sql, values)
        klass = self._from_query(data, self._table, self._fields, **kwargs)
        klass.set_state('where')
        return klass

    def bulk_update(self, **kwargs):
        if self.__state != 'where':
            raise QueryError(f"{self._table}: where method must be called before bulk_update method!")

        sql, values = self._db_mapper._get_bulk_update_sql(self._table, self._kwds, **kwargs)
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
        self._db = Config().DATABASE
        self._db_mapper = Config().DBMAPPER

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
        sql = self._db_mapper._get_create_table_sql(self.table_name, **self._mapping)
        self._db.execute(sql)
        if commit:
            self._db.commit()

    def _get_primary_key_field(self):
        return self._model.__pk__

    def create(self, **kwargs):
        return self.insert(**kwargs)

    def insert(self, **kwargs):
        try:
            sql, values = self._db_mapper._get_insert_sql(self.table_name, **kwargs)
            lastrowid = self._db.exec_lastrowid(sql, values)
            self._db.commit()
        except sq.OperationalError as e:
            raise InsertError(str(e))
        return lastrowid

    def bulk_insert(self, *data):
        for d in data:
            if not isinstance(d, dict):
                raise InsertError(f"bulk_insert accepts only dictionary values!")
            sql, values = self._db_mapper._get_insert_sql(self.table_name, **d)
            self._db.execute(sql, values)
        self._db.commit()

    def delete(self, **kwargs):
        sql, values = self._db_mapper._get_delete_sql(self.table_name, **kwargs)
        self._db.execute(sql, values)
        self._db.commit()

    def get(self, **kwargs):
        sql, values = self._db_mapper._get_select_where_sql(self.table_name, ['*'], **kwargs)

        try:
            query_set = self._db.fetchone(sql, values)
            data = dict(zip(self._table_fields, query_set))
            pk_field = self._get_primary_key_field()
            data['_table'] = self.table_name
            data['_pk'] = data[pk_field]
            data['id'] = data[pk_field]
            data['_pk_field'] = pk_field
            query_class = QuerySet(data)
        except TypeError:
            raise ModelDoesNotExist(f"{self.table_name}: No model matches the given query!")

        return query_class

    def select(self, fields):
        return Query.select(self.table_name, fields)


class SQLModelBaseMetaClass(type):
    """Metaclass for all models."""

    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]

    def _get_meta_data(cls, attr):
        _abstract = False
        _db_name = None

        if 'Meta' in attr:
            _meta = attr['Meta']
            _abstract = getattr(_meta, 'abstract', _abstract)
            _db_name = getattr(_meta, 'db_name', _db_name)
            del attr['Meta']

        class _Meta:
            abstract = _abstract
            db_name = _db_name

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
                mappings[key] = value

        # Delete fields that are already stored in mapping
        for key in mappings.keys():
            del attr[key]

        # Model metadata
        _meta = mcs._get_meta_data(mcs, attr)

        # Checks if model has PrimaryKeyField
        # if False, then it will automatically create one
        if has_primary_key is False and _meta.abstract is False:
            mappings['_pk'] = PrimaryKeyField()
            primary_key_field = '_pk'

        # Save mapping between attribute and columns and table name
        attr['_meta'] = _meta
        attr['__mappings__'] = mappings
        attr['__table_name__'] = _meta.db_name if _meta.db_name else name.lower()
        attr['__pk__'] = primary_key_field
        new_class = type.__new__(mcs, name, base, attr)

        return new_class


class Model(metaclass=SQLModelBaseMetaClass):
    """Model class for SQL Databases"""

    class Meta:
        db_name = None
        abstract = True

    def __init_subclass__(cls, **kwargs):
        # If the model is not abstract model then
        # create database table immediately the Model class is subclassed
        if cls._meta.abstract is False:
            cls.objects = SQLModelManager(cls)
            cls.objects._create_table()
