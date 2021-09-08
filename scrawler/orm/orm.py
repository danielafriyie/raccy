"""
Object Relational Mapper Built into the library to
simplify SQL operations, and encapsulate database operations.
Currently it supports on SQLite Database.
"""
import sqlite3 as sq


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
#       QUERY SET
####################################################
class QuerySet:

    def __init__(self, data, sql=None):
        self._data = data
        self._sql = sql

    @property
    def get_data(self):
        return self._data

    def __getattribute__(self, item):
        data = object.__getattribute__(self, '_data')
        if item in data and isinstance(data, dict):
            return data[item]
        return object.__getattribute__(self, item)

    @classmethod
    def select(cls, table, *fields):
        sql = f"SELECT {', '.join(fields)} FROM {table};"


    def update(self, **kwargs):
        update_sql = 'UPDATE {table} SET {placeholders} WHERE {query}'
        placeholders, values = [], []

        for key, val in kwargs.items():
            values.append(val)
            placeholders.append(f'{key}=?')


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
        for key, value in attr.items():
            if isinstance(value, Field):
                mappings[key] = value

        # Delete fields that are already stored in mapping
        for key in mappings.keys():
            del attr[key]
        # print(name, mappings)

        # Model metadata
        _meta = mcs._get_meta_data(mcs, attr)

        # Save mapping between attribute and columns and table name
        attr['_meta'] = _meta
        attr['__mappings__'] = mappings
        attr['__table_name__'] = _meta.db_name if _meta.db_name else name.lower()
        new_class = type.__new__(mcs, name, base, attr)

        return new_class


class ModelManager:
    """Manager for handling all database operations"""

    def __init__(self, model):
        self._model = model
        self._mapping = model.__mappings__.items()
        self._db = sq.connect('test.db')

    @property
    def table_name(self):
        return self._model.__table_name__

    def _create_table(self):
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
        self._db.commit()

    @property
    def _table_fields(self):
        fields = [x[0] for x in self._mapping]
        return fields

    def create(self, **kwargs):
        return self.insert(**kwargs)

    def insert(self, **kwargs):
        insert_sql = 'INSERT INTO {name} ({fields}) VALUES ({placeholders});'
        fields, values, placeholders = [], [], []

        for key, val in kwargs.items():
            fields.append(key)
            placeholders.append('?')
            values.append(val)

        sql = insert_sql.format(name=self.table_name, fields=', '.join(fields), placeholders=', '.join(placeholders))
        cursor = self._db.execute(sql, values)
        self._db.commit()
        return cursor.lastrowid

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

        sql = get_sql.format(table=self.table_name, query=' AND '.join(query))
        query_set = self._db.execute(sql, values).fetchone()
        query_set = dict(zip(self._table_fields, query_set))
        query_set['_table'] = self.table_name

        return QuerySet(query_set)


class Model(metaclass=ModelBaseMetaClass):

    def __init_subclass__(cls, **kwargs):
        # Creates database table immediately Model class is subclassed
        _meta = cls._meta
        if _meta.abstract is False:
            cls.objects = ModelManager(cls)
            cls.objects._create_table()


class Author(Model):
    author_id = PrimaryKeyField()
    name = CharField(max_length=75)
    age = IntegerField()
    lucky_number = IntegerField(default=90)
    salary = FloatField(default=50000)

    class Meta:
        db_name = 'author_table'


class BaseDb(Model):
    author_id = ForeignKeyField(Author, 'author_id')

    class Meta:
        abstract = True


class Post(BaseDb):
    post_id = PrimaryKeyField()
    post = TextField(null=False)

    class Meta:
        db_name = 'post_table'


class AuthorPost(BaseDb):
    post_id = ForeignKeyField(Post, 'post_id')
    text = TextField()


# author = Author.objects.create(name='Brother Mensah', age=19, lucky_number=120, salary=2500)
# Post.objects.insert(post="This is Brother's post", author_id=author)
# Author.objects.delete(author_id=4, age=19)
a = Author.objects.get(author_id=1)
print(a.name)
