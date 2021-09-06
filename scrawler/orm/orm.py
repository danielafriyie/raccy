import sqlite3 as sq
import inspect

SQLITE_TYPE_MAP = {
    int: 'INTEGER',
    float: 'REAL',
    str: 'TEXT',
    bytes: 'BLOB',
    bool: 'INTEGER'
}
CREATE_TABLE_SQL = 'CREATE TABLE {name} ({fields});'
SELECT_TABLE_SQL = "SELECT name FROM sqlite_master WHERE type='table';"
INSERT_SQL = 'INSERT INTO {name} ({fields}) VALUES ({placeholders});'
SELECT_ALL_SQL = 'SELECT {fields} FROM {names};'


class Database:

    def __init__(self, path):
        self.conn = sq.Connection(path)

    @property
    def tables(self):
        query = self._execute(SELECT_TABLE_SQL)
        return [row[0] for row in query.fetchall()]

    def _execute(self, sql, params=None):
        if params:
            return self.conn.execute(sql, params)
        return self.conn.execute(sql)

    def create(self, table):
        self._execute(table._get_create_sql())

    def save(self, instance):
        cursor = self._execute(instance._get_insert_sql())
        instance._data['id'] = cursor.lastrowid

    def all(self, table):
        pass


class Table:

    def __init___(self, **kwargs):
        self._data = {
            'id': None
        }
        for key, value in kwargs.items():
            self._data[key] = value

    def __getattribute__(self, key):
        data = object.__getattribute__(self, '_data')
        if key in self._data:
            return data[key]
        return object.__getattribute__(self, key)

    @classmethod
    def _get_name(cls):
        return cls.__name__.lower()

    def _get_insert_sql(self):
        fields = []
        placeholders = []
        values = []

        for name, field in inspect.getmembers(self.__class__):
            if isinstance(field, Column):
                fields.append(name)
                values.append(getattr(self, name))
                placeholders.append('?')

        sql = INSERT_SQL.format(
            name=self.__class__._get_name(),
            fields=', '.join(fields),
            placeholders=', '.join(placeholders)
        )
        return sql, values

    @classmethod
    def _get_create_sql(cls):
        fields = [
            ('id', 'INTEGER PRIMARY KEY AUTOINCREMENT')
        ]

        for name, field in inspect.getmembers(cls):
            if isinstance(field, Column):
                fields.append((name, field.sql_type))
            elif isinstance(field, ForeignKey):
                fields.append((name + '_id', 'INTEGER'))

        fields = [' '.join(x) for x in fields]

        return CREATE_TABLE_SQL.format(name=cls._get_name(), fields=', '.join(fields))


class Column:

    def __init__(self, type_):
        self.type = type_

    @property
    def sql_type(self):
        return SQLITE_TYPE_MAP[self.type]


class ForeignKey:

    def __init__(self, table):
        self.table = table
