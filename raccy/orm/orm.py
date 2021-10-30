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
from typing import Iterator, Dict
from functools import lru_cache

from .signals import ModelSignal
from raccy.core.exceptions import (
    ModelDoesNotExist, InsertError, QueryError, SignalException
)
from raccy.logger.logger import logger as _logger
from .base import (
    _config, BaseQuery, BaseDbManager, AttrDict
)
from .utils import render_sql_dict

_log = _logger()


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


#################################
#       QUERY AND QUERYSET
################################
class Query(BaseQuery):
    """
    Query class for making complex and advance queries
    """

    def __init__(self, model, data, table, fields=None, **kwargs):
        super().__init__(model, data)
        self._table = table
        self._fields = fields
        self._kwds = kwargs
        self.__state = None

    @property
    def state(self):
        return self.__state

    @classmethod
    def select(cls, model, table, fields, distinct=False):
        """
        Equivalent to SELECT statement in SQL. Selects field(s) / column(s) from a database.
        If distinct argument is set to True, unique rows are selected using the DISTINCT clause
        Example:
        >>>from raccy import model
        >>>
        >>>config = model.Config()
        >>>config.DATABASE = model.SQLiteDatabase('db.sqlite3')
        >>>
        >>>class Dog(model.Model):
        ...    breed = model.CharField()
        ...
        >>>Dog.objects.create(breed='Bull dog')
        1
        >>>q = Dog.objects.select(['*'])
        >>>q.get_data
        [('Bull dog', 1)]
        """
        db = _config.DATABASE
        mapper = _config.DBMAPPER
        sql = mapper._render_select_sql_stmt(table, fields, distinct=distinct)
        try:
            data = db.fetchall(sql)
            klass = cls(model, data, table, fields)
            klass.set_state('select')
        except sq.OperationalError as e:
            raise QueryError(str(e))
        return klass

    @classmethod
    def _from_query(cls, model, data, table, fields=None, **kwargs):
        return cls(model, data, table, fields, **kwargs)

    def set_state(self, state):
        self.__state = state

    def where(self, *args):
        """
        Equivalent to filtering with WHERE in SQL. Filter rows of a result set using various conditions
        NB: select method must be called before this method.
        Example:
        >>>from raccy import model
        >>>from datetime import datetime as dt
        >>>
        >>>config = model.Config()
        >>>config.DATABASE = model.SQLiteDatabase('db.sqlite3')
        >>>
        >>>class Author(model.Model):
        ...    author_id = model.PrimaryKeyField()
        ...    name = model.CharField(max_length=75)
        ...    age = model.IntegerField()
        ...    lucky_number = model.IntegerField(default=90)
        ...    salary = model.FloatField(default=50000)
        ...    date = model.DateField()
        ...    datetime = model.DateTimeField()
        ...    adult = model.BooleanField(default=False)
        ...
        >>>Author.objects.bulk_insert(
        ...    dict(name='Kwame', age=45, date=dt.now().date(), datetime=dt.now(), lucky_number=99, salary=6400),
        ...    dict(name='Yaw', age=32, date=dt.now().date(), datetime=dt.now(), lucky_number=56, salary=6400),
        ...    dict(name='Fiifi', age=23, date=dt.now().date(), datetime=dt.now(), lucky_number=34),
        ...    dict(name='Navas', age=21, date=dt.now().date(), datetime=dt.now()),
        ...    dict(name='Jesus', age=34, date=dt.now().date(), datetime=dt.now(), salary=6400, adult=True)
        ... )
        >>>authors = Author.objects.select(['name', 'age'])
        >>>authors_with_high_lucky_number = authors.where(Author.lucky_number >= 90)
        >>>for author in authors_with_high_lucky_number.get_data:
        ...    print(author.name)
        ...
        Kwame
        Navas
        """
        if self.__state != 'select':
            raise QueryError(f"{self._table}: select method must be called before where method!")

        if self.__state == 'where':
            raise QueryError(f"{self._table}: where method called more than one!")

        sql, values = self._mapper._render_select_where_sql_stmt(*args)
        data = self._db.fetchall(sql, values)
        klass = self._from_query(self._model, data, self._table, self._fields)
        klass.set_state('where')
        return klass

    def limit(self, value):
        """
        Constrain the number of rows returned by a query.
        Example:
        >>>from raccy import model
        >>>from datetime import datetime as dt
        >>>
        >>>config = model.Config()
        >>>config.DATABASE = model.SQLiteDatabase('db.sqlite3')
        >>>
        >>>class Author(model.Model):
        ...    author_id = model.PrimaryKeyField()
        ...    name = model.CharField(max_length=75)
        ...    age = model.IntegerField()
        ...    lucky_number = model.IntegerField(default=90)
        ...    salary = model.FloatField(default=50000)
        ...    date = model.DateField()
        ...    datetime = model.DateTimeField()
        ...    adult = model.BooleanField(default=False)
        ...
        >>>Author.objects.bulk_insert(
        ...    dict(name='Kwame', age=45, date=dt.now().date(), datetime=dt.now(), lucky_number=99, salary=6400),
        ...    dict(name='Yaw', age=32, date=dt.now().date(), datetime=dt.now(), lucky_number=56, salary=6400),
        ...    dict(name='Fiifi', age=23, date=dt.now().date(), datetime=dt.now(), lucky_number=34),
        ...    dict(name='Navas', age=21, date=dt.now().date(), datetime=dt.now()),
        ...    dict(name='Jesus', age=34, date=dt.now().date(), datetime=dt.now(), salary=6400, adult=True)
        ... )
        >>>qs = Author.objects.select(['name', 'age', 'lucky_number']).limit(2)
        >>>print(qs.get_data)
        [('Kwame', 45, 99), ('Yaw', 32, 56)]
        """
        if self.__state not in ('select', 'where'):
            raise QueryError(f"{self._table}: select or where method must be called before limit method!")

        sql, values = self._mapper._render_limit_sql_stmt(value)
        if values:
            data = self._db.fetchall(sql, values)
        else:
            data = self._db.fetchall(sql)
        return self._from_query(self._model, data, self._table)

    def bulk_update(self, **kwargs):
        """
        Update existing rows in a database.
        NB: select method must be called before this method.
        Example:
        >>>from raccy import model
        >>>from datetime import datetime as dt
        >>>
        >>>config = model.Config()
        >>>config.DATABASE = model.SQLiteDatabase('db.sqlite3')
        >>>
        >>>class Author(model.Model):
        ...    author_id = model.PrimaryKeyField()
        ...    name = model.CharField(max_length=75)
        ...    age = model.IntegerField()
        ...    lucky_number = model.IntegerField(default=90)
        ...    salary = model.FloatField(default=50000)
        ...    date = model.DateField()
        ...    datetime = model.DateTimeField()
        ...    adult = model.BooleanField(default=False)
        ...
        >>>Author.objects.bulk_insert(
        ...    dict(name='Kwame', age=45, date=dt.now().date(), datetime=dt.now(), lucky_number=99, salary=6400),
        ...    dict(name='Yaw', age=32, date=dt.now().date(), datetime=dt.now(), lucky_number=56, salary=6400),
        ...    dict(name='Fiifi', age=23, date=dt.now().date(), datetime=dt.now(), lucky_number=34),
        ...    dict(name='Navas', age=21, date=dt.now().date(), datetime=dt.now()),
        ...    dict(name='Jesus', age=34, date=dt.now().date(), datetime=dt.now(), salary=6400, adult=True)
        ... )
        >>>qs = Author.objects.select(['*']).where(Author.lucky_number >= 90)
        >>>qs.bulk_update(lucky_number=100)
        >>>all_authors = Author.objects.all()
        >>>for author in all_authors:
        ...    print(author.name, author.lucky_number)
        ...
        Kwame 100
        Yaw 56
        Fiifi 34
        Navas 100
        Jesus 100
        """
        if self.__state not in ('select', 'where'):
            raise QueryError(f"{self._table}: select or where method must be called before bulk_update method!")

        sql, values = self._mapper._render_bulk_update_sql_stmt(self._table, **kwargs)
        self._db.execute(sql, values)
        self._db.commit()


class QuerySet(BaseQuery):
    """Query class for single row instance from database"""

    def _get_new_instance(self, kwargs):
        old_data = {self._pk_field: self.pk}
        for field in self._model.objects._table_fields:
            if field not in kwargs:
                if field != self._pk_field:
                    old_data[field] = getattr(self, field)
        kwargs.update(old_data)
        new = self._model.objects.mk_attr_dict(**kwargs)

        return new

    def update(self, **kwargs):
        """
        Updates a row in a database.
        Example:
        >>>from raccy import model
        >>>
        >>>config = model.Config()
        >>>config.DATABASE = model.SQLiteDatabase('db.sqlite3')
        >>>
        >>> class Post(model.Model):
        ...     post = model.TextField()
        ...
        >>> Post.objects.insert(post='this is a post')
        1
        >>>post = Post.objects.get(pk=1)
        >>>post.update(post='this is the post update')
        >>>updated_post = Post.objects.get(pk=1)
        >>>updated_post.post
        'this is the post update'
        """
        new = self._get_new_instance(kwargs)
        self._model.objects._dispatch('before_update', new, self)
        pk = new.attrs.pop(self._pk_field)

        sql, values = self._mapper._render_update_sql_stmt(self._table, self.pk, self._pk_field, **new.attrs)
        self._db.execute(sql, values)
        self._db.commit()

        new.attrs[self._pk_field] = pk
        self._model.objects._dispatch('after_update', new, self)

    def __repr__(self):
        return str(self._data)


####################################################
#       MANAGER, AND MODEL CLASS
####################################################
class SQLModelManager(BaseDbManager):
    """Manager for handling all SQL database operations"""

    def __init__(self, model):
        self._model = model
        self._mapping = model.__mappings__
        self._db = _config.DATABASE
        self._mapper = _config.DBMAPPER
        self._signals: Dict[str: ModelSignal] = {}

    @property
    def signals(self):
        return self._signals

    @property
    def table_name(self) -> str:
        return self._model.__table_name__

    @property
    def _table_fields(self) -> list:
        fields = [x[0] for x in self._mapping.items()]
        return fields

    def register_signal(self, signal):
        if not isinstance(signal, ModelSignal):
            raise SignalException(f"{self.__class__.__name__}: {signal} is not an instance of {ModelSignal}")
        self._signals[signal.signal_name] = signal

    def _dispatch(self, signal_name, *args, **kwargs):
        signal = self._signals.get(signal_name, None)
        if signal:
            signal.notify(self._model, *args, **kwargs)

    def all(self) -> Iterator:
        """
        Select all data / rows in a database.
        Example:
        >>>from raccy import model
        >>>from datetime import datetime as dt
        >>>
        >>>config = model.Config()
        >>>config.DATABASE = model.SQLiteDatabase('db.sqlite3')
        >>>
        >>>class Author(model.Model):
        ...    author_id = model.PrimaryKeyField()
        ...    name = model.CharField(max_length=75)
        ...    age = model.IntegerField()
        ...    lucky_number = model.IntegerField(default=90)
        ...    salary = model.FloatField(default=50000)
        ...    date = model.DateField()
        ...    datetime = model.DateTimeField()
        ...    adult = model.BooleanField(default=False)
        ...
        >>>Author.objects.bulk_insert(
        ...    dict(name='Kwame', age=45, date=dt.now().date(), datetime=dt.now(), lucky_number=99, salary=6400),
        ...    dict(name='Yaw', age=32, date=dt.now().date(), datetime=dt.now(), lucky_number=56, salary=6400),
        ...    dict(name='Fiifi', age=23, date=dt.now().date(), datetime=dt.now(), lucky_number=34),
        ...    dict(name='Navas', age=21, date=dt.now().date(), datetime=dt.now()),
        ...    dict(name='Jesus', age=34, date=dt.now().date(), datetime=dt.now(), salary=6400, adult=True)
        ... )
        >>>all_authors = Author.objects.all()
        >>>for author in all_authors:
        ...    print(author.name)
        ...
        Kwame
        Yaw
        Fiifi
        Navas
        Jesus
        """
        table_fields = self._table_fields
        pk_field = self._primary_key_field
        pk_idx = table_fields.index(pk_field)
        qs = self.select(table_fields).get_data
        datas = map(lambda x: self.get(**{pk_field: x[pk_idx]}), qs)
        return datas

    def _create_table(self, commit=True) -> None:
        sql = self._mapper._render_create_table_sql_stmt(self.table_name, **self._mapping)
        if sql is not None:
            self._db.executescript(sql)
            if commit:
                self._db.commit()

    @property
    def _primary_key_field(self) -> str:
        return self._model.__pk__

    def create(self, **kwargs) -> int:
        return self.insert(**kwargs)

    def mk_attr_dict(self, **kwargs):
        for field in self._table_fields:
            if field not in kwargs:
                if field != self._primary_key_field:
                    kwargs[field] = ''
        instance = AttrDict(**kwargs)
        return instance

    def insert(self, **kwargs) -> int:
        """
        Inserts data / row into a database
        Example:
        >>>from raccy import model
        >>>
        >>>config = model.Config()
        >>>config.DATABASE = model.SQLiteDatabase('db.sqlite3')
        >>>
        >>> class Post(model.Model):
        ...     post = model.TextField()
        ...
        >>> Post.objects.insert(post='this is a post')
        1
        """
        instance = self.mk_attr_dict(**kwargs)
        self._dispatch('before_insert', instance)

        try:
            sql, values = self._mapper._render_insert_sql_stmt(self.table_name, **instance.attrs)
            lastrowid = self._db.exec_lastrowid(sql, values)
            self._db.commit()
        except sq.OperationalError as e:
            raise InsertError(str(e))

        instance = self.get(**{self._primary_key_field: lastrowid})
        self._dispatch('after_insert', instance)

        return lastrowid

    def bulk_insert(self, *data) -> None:
        """
        Inserts bulk data / rows into a database, this is recommended if you are inserting bulk
        data into the database. Data must be an instance of dict.
        Example:
        >>>from raccy import model
        >>>from datetime import datetime as dt
        >>>
        >>>config = model.Config()
        >>>config.DATABASE = model.SQLiteDatabase('db.sqlite3')
        >>>
        >>>class Author(model.Model):
        ...    author_id = model.PrimaryKeyField()
        ...    name = model.CharField(max_length=75)
        ...    age = model.IntegerField()
        ...    lucky_number = model.IntegerField(default=90)
        ...    salary = model.FloatField(default=50000)
        ...    date = model.DateField()
        ...    datetime = model.DateTimeField()
        ...    adult = model.BooleanField(default=False)
        ...
        >>>Author.objects.bulk_insert(
        ...    dict(name='Kwame', age=45, date=dt.now().date(), datetime=dt.now(), lucky_number=99, salary=6400),
        ...    dict(name='Yaw', age=32, date=dt.now().date(), datetime=dt.now(), lucky_number=56, salary=6400),
        ...    dict(name='Fiifi', age=23, date=dt.now().date(), datetime=dt.now(), lucky_number=34),
        ...    dict(name='Navas', age=21, date=dt.now().date(), datetime=dt.now()),
        ...    dict(name='Jesus', age=34, date=dt.now().date(), datetime=dt.now(), salary=6400, adult=True)
        ... )
        >>>
        """
        for d in data:
            if not isinstance(d, dict):
                raise InsertError(f"{self.__class__.__name__}.bulk_insert accepts only dictionary values!")
            sql, values = self._mapper._render_insert_sql_stmt(self.table_name, **d)
            self._db.execute(sql, values)
        self._db.commit()

    def delete(self, **kwargs) -> None:
        """
        Deletes data / row from a database
        Example:
        >>>from raccy import model
        >>>
        >>>config = model.Config()
        >>>config.DATABASE = model.SQLiteDatabase('db.sqlite3')
        >>>
        >>>class Dog(model.Model):
        ...    breed = model.CharField()
        ...
        >>>Dog.objects.create(breed='Bull dog')
        1
        >>>Dog.objects.create(breed='Red dog')
        2
        >>>Dog.objects.delete(pk=2)
        >>>
        """
        if 'pk' in kwargs:
            pk = kwargs.pop('pk')
            pk_kwarg = {self._primary_key_field: pk}
            kwargs.update(pk_kwarg)

        instance = self.get(**kwargs)
        self._dispatch('before_delete', instance)

        sql, values = self._mapper._render_delete_sql_stmt(self.table_name, **kwargs)
        self._db.execute(sql, values)
        self._db.commit()

        self._dispatch('after_delete', instance)

    @lru_cache(maxsize=1000)
    def get(self, **kwargs) -> QuerySet:
        """
        Retrieve single row of data from a database.
        Example:
        >>>from raccy import model
        >>>
        >>>config = model.Config()
        >>>config.DATABASE = model.SQLiteDatabase('db.sqlite3')
        >>>
        >>>class Dog(model.Model):
        ...    breed = model.CharField()
        ...
        >>>Dog.objects.create(breed='Bull dog')
        1
        >>>Dog.objects.create(breed='Red dog')
        2
        >>>red_dog = Dog.objects.get(pk=2)
        >>>red_dog.pk
        2
        >>>red_dog.breed
        'Red dog'
        >>>
        """
        args = []
        if 'pk' in kwargs:
            pk = kwargs.pop('pk')
            sd = render_sql_dict(self._primary_key_field, '=', pk)
            args.append(sd)
        for key, val in kwargs.items():
            sql_dict = render_sql_dict(key, '=', val)
            args.append(sql_dict)

        qs = self.select(['*']).where(*args)

        try:
            query_set = qs.get_data[0]
            data = dict(zip(self._table_fields, query_set))
            pk_field = self._primary_key_field
            data['_table'] = self.table_name
            data['pk'] = data[pk_field]
            data['id'] = data[pk_field]
            data['_pk_field'] = pk_field
            query_class = QuerySet(self._model, data)
        except TypeError:
            raise ModelDoesNotExist(f"{self.table_name}: No model matches the given query!")
        except IndexError:
            raise ModelDoesNotExist(f"{self.table_name}: No model matches the given query!")

        return query_class

    def select(self, fields, distinct=False) -> Query:
        """
        Equivalent to SELECT statement in SQL. Selects field(s) / column(s) from a database.
        If distinct argument is set to True, unique rows are selected using the DISTINCT clause
        Example:
        >>>from raccy import model
        >>>
        >>>config = model.Config()
        >>>config.DATABASE = model.SQLiteDatabase('db.sqlite3')
        >>>
        >>>class Dog(model.Model):
        ...    breed = model.CharField()
        ...
        >>>Dog.objects.create(breed='Bull dog')
        1
        >>>q = Dog.objects.select(['*'])
        >>>q.get_data
        [('Bull dog', 1)]
        """
        return Query.select(self._model, self.table_name, fields, distinct=distinct)

    def raw(self, *args, **kwargs):
        """
        Executes raw sql.
        Example:
        >>>from raccy import model
        >>>
        >>>config = model.Config()
        >>>config.DATABASE = model.SQLiteDatabase('db.sqlite3')
        >>>
        >>>class Dog(model.Model):
        ...    breed = model.CharField()
        ...
        >>>Dog.objects.create(breed='Bull dog')
        1
        >>>sql = "SELECT * FROM dog"
        >>>qs = Dog.objects.raw(sql)
        >>>qs.fetchall()
        [('Bull dog', 1)]
        """
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

    def register_signal(cls, signal):
        cls.objects.register_signal(signal)

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

    def __getattr__(self, item):
        try:
            return self.__mappings__[item]
        except KeyError:
            raise AttributeError(item)
