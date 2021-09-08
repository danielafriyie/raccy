"""
Object Relational Mapper Built into the library to
simplify SQL operations, and encapsulate database operations.
Currently it supports on SQLite Database.
"""
import sqlite3 as sq

from scrawler.core.meta import SingletonMeta
from scrawler.core.exceptions import ModelDoesNotExist, InsertError, QueryError


#################################################
#       MODEL CONFIGURATION
#################################################
class Config(metaclass=SingletonMeta):
    db_path = 'db.sqlite3'


#####################################################
#       MODEL FIELDS
####################################################
class Field:
    """Base class for all field types"""

    def __init__(self, type_, max_length=None, null=True, unique=False, default=None):
        self.type = type_
        self.max_length = max_length
        self.null = null
        self.unique = unique
        self.default = default

    @property
    def sql(self):
        _sql = f'{self.type}'
        if self.max_length:
            _sql = _sql + f'({self.max_length}) '
        if self.null is False:
            _sql = _sql + ' NOT NULL '
        if self.unique:
            _sql = _sql + ' UNIQUE '
        if self.default:
            _sql = _sql + f' DEFAULT {self.default}'
        return _sql


class PrimaryKeyField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__('INTEGER', *args, **kwargs)

    @property
    def sql(self):
        sql = super().sql + ' PRIMARY KEY AUTOINCREMENT'
        return sql


class CharField(Field):

    def __init__(self, max_length=120, *args, **kwargs):
        super().__init__('VARCHAR', max_length, *args, **kwargs)


class TextField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__('TEXT', *args, **kwargs)


class IntegerField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__('INTEGER', *args, **kwargs)


class FloatField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__('DOUBLE', *args, **kwargs)


class BooleanField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__('BOOLEAN', *args, **kwargs)


class DateField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__('DATE', *args, **kwargs)


class DateTimeField(Field):

    def __init__(self, *args, **kwargs):
        super().__init__('DATETIME', *args, **kwargs)


class ForeignKeyField(Field):

    def __init__(self, model, on_field, on_delete='CASCADE', on_update='CASCADE'):
        super().__init__('INTEGER', null=False)
        self.__model = model
        self.__on_field = on_field
        self.__on_delete = on_delete
        self.__on_update = on_update

    def _foreign_key_sql(self, field_name):
        sql = f"""
            FOREIGN KEY ({field_name})
            REFERENCES {self.__model.objects.table_name} ({self.__on_field}) 
                ON UPDATE {self.__on_update}
                ON DELETE {self.__on_delete}
        """
        return sql


####################################################
#       QUERY AND QUERYSET
####################################################
class BaseQuery:
    """Base class for all query and queryset"""

    def __init__(self, data):
        self._data = data

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
        update_sql = "UPDATE {table} SET {placeholders} WHERE {query};"
        query = f"{self._pk_field}=?"
        values, placeholders = [], []

        for key, val in kwargs.items():
            values.append(val)
            placeholders.append(f"{key}=?")

        values.append(self._pk)
        sql = update_sql.format(table=self._table, placeholders=', '.join(placeholders), query=query)
        self.db.execute(sql, values)
        self.db.commit()


class Query(BaseQuery):
    """
    Query class for making complex and advance queries
    """

    def __init__(self, data, db, table, sql=None):
        super().__init__(data)
        self._db = db
        self._table = table
        self._sql = sql
        self.__state = None

    def set_state(self, state):
        self.__state = state

    @property
    def state(self):
        return self.__state

    @classmethod
    def select(cls, db, table, fields):
        try:
            temp_sql = f"SELECT {', '.join(fields)} FROM {table}"
            sql = temp_sql + ';'
            data = db.execute(sql).fetchall()
            klass = cls(data, db, table, temp_sql)
            klass.set_state('select')
        except sq.OperationalError as e:
            raise QueryError(str(e))
        return klass

    @classmethod
    def _from_query(cls, data, db, table, sql):
        return cls(data, db, table, sql)

    def where(self, **kwargs):
        if self._sql is None:
            raise QueryError(f"{self._table}: select method must be called before where method!")

        query, values = [], []
        where_sql = " WHERE {query}"

        for key, val in kwargs.items():
            values.append(val)
            query.append(f"{key}=?")

        where_sql = where_sql.format(query=' AND '.join(query))
        temp_sql = self._sql + where_sql
        sql = temp_sql + ';'
        data = self._db.execute(sql, values).fetchall()
        klass = self._from_query(data, self._db, self._table, temp_sql)
        klass._where_sql = where_sql
        klass._where_values = values
        klass.set_state('where')
        return klass

    def bulk_update(self, **kwargs):
        if self.__state != 'where':
            raise QueryError(f"{self._table}: where method must be called before bulk_update method!")

        where_sql = self._where_sql
        where_values = self._where_values
        temp_sql = 'UPDATE {table} SET {placeholders}'
        placeholders, values = [], []

        for key, val in kwargs.items():
            placeholders.append(f"{key}=?")
            values.append(val)

        temp_sql = temp_sql.format(table=self._table, placeholders=', '.join(placeholders)) + where_sql
        sql = temp_sql + ';'
        values = values + where_values
        self._db.execute(sql, values)
        self._db.commit()


####################################################
#       MODEL BASE, MANAGER, AND MODEL CLASS
####################################################
class ModelBaseMetaClass(type):
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
        for key, value in attr.items():
            if isinstance(value, PrimaryKeyField):
                has_primary_key = True
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

        # Save mapping between attribute and columns and table name
        attr['_meta'] = _meta
        attr['__mappings__'] = mappings
        attr['__table_name__'] = _meta.db_name if _meta.db_name else name.lower()
        new_class = type.__new__(mcs, name, base, attr)

        return new_class


class ModelManager:
    """Manager for handling all database operations"""

    def __init__(self, model, db_path):
        self._model = model
        self._mapping = model.__mappings__.items()
        self._db = sq.connect(db_path)

    @property
    def table_name(self):
        return self._model.__table_name__

    def _create_table(self, commit=True):
        fields = []
        foreign_key_sql = []

        for name, field in self._mapping:
            if isinstance(field, ForeignKeyField):
                foreign_key_sql.append(field._foreign_key_sql(name))
            fields.append(f"{name} {field.sql}")

        fields = ', '.join(fields)

        sql = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                {fields} {',' if foreign_key_sql else ''}
                {', '.join(foreign_key_sql) if foreign_key_sql else ''}
            );
        """
        self._db.execute(sql)
        if commit:
            self._db.commit()

    def _get_primary_key_field(self):
        for key, val in self._mapping:
            if isinstance(val, PrimaryKeyField):
                return key

    @property
    def _table_fields(self):
        fields = [x[0] for x in self._mapping]
        return fields

    def create(self, **kwargs):
        return self.insert(**kwargs)

    def _get_insert_sql(self, **kwargs):
        insert_sql = 'INSERT INTO {name} ({fields}) VALUES ({placeholders});'
        fields, values, placeholders = [], [], []

        for key, val in kwargs.items():
            fields.append(key)
            placeholders.append('?')
            values.append(val)

        sql = insert_sql.format(name=self.table_name, fields=', '.join(fields), placeholders=', '.join(placeholders))
        return sql, values

    def insert(self, **kwargs):
        try:
            sql, values = self._get_insert_sql(**kwargs)
            cursor = self._db.execute(sql, values)
            self._db.commit()
        except sq.OperationalError as e:
            raise InsertError(str(e))
        return cursor.lastrowid

    def bulk_insert(self, *data):
        for d in data:
            if not isinstance(d, dict):
                raise InsertError(f"bulk_insert accepts only dictionary values!")
            sql, values = self._get_insert_sql(**d)
            self._db.execute(sql, values)
        self._db.commit()

    def delete(self, **kwargs):
        delete_sql = 'DELETE FROM {table} WHERE {query};'
        query, values = [], []

        for key, val in kwargs.items():
            values.append(val)
            query.append(f'{key}=?')

        sql = delete_sql.format(table=self.table_name, query=' AND '.join(query))
        self._db.execute(sql, values)
        self._db.commit()

    def get(self, **kwargs):
        get_sql = 'SELECT * FROM {table} WHERE {query}'
        query, values = [], []

        for key, val in kwargs.items():
            values.append(val)
            query.append(f'{key}=?')

        try:
            sql = get_sql.format(table=self.table_name, query=' AND '.join(query))
            query_set = self._db.execute(sql, values).fetchone()
            data = dict(zip(self._table_fields, query_set))
            pk_field = self._get_primary_key_field()
            data['_table'] = self.table_name
            data['_pk'] = data[pk_field]
            data['_pk_field'] = pk_field
            query_class = QuerySet(data)
            query_class.db = self._db
        except TypeError:
            raise ModelDoesNotExist(f"{self.table_name}: No model matches the given query!")

        return query_class

    def select(self, fields):
        return Query.select(self._db, self.table_name, fields)


class Model(metaclass=ModelBaseMetaClass):
    class Meta:
        db_name = None
        abstract = True

    def __init_subclass__(cls, **kwargs):
        # If the model is not abstract model then
        # create database table immediately the Model class is subclassed
        if cls._meta.abstract is False:
            cls.objects = ModelManager(cls, Config.db_path)
            cls.objects._create_table()
