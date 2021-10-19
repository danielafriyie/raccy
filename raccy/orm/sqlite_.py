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

from raccy.core.exceptions import DatabaseException
from .base import (
    BaseSQLBuilder, BaseSQLDbMapper, BaseSQLDatabase, _config, Migration
)
from .utils import table_exists
from .orm import (
    ForeignKeyField, PrimaryKeyField
)


#######################################
#      SQL AND QUERY BUILDERS
#######################################
class SQLBuilder(BaseSQLBuilder):
    pass


class CreateTableSQLStmt(SQLBuilder):

    def __init__(self, table_name, **kwargs):
        self._table_name = table_name
        self._kwargs = kwargs
        self._partial_sql = None

    def _build_sql(self, table_name, **kwargs):
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
            migration.mk_migrations(table_name, migration_fields)
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
                    raise DatabaseException(
                        f"{table_name}: sqlite database does not support adding primary key "
                        f"field after table is created."
                    )
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
            migration.mk_migrations(table_name, existing_fields)
            return sql

    @property
    def sql(self):
        sql = self._clean_stmt(self._build_sql(self._table_name, **self._kwargs))
        return sql


class InsertSQLStmt(SQLBuilder):

    def __init__(self, table_name, **kwargs):
        self._table_name = table_name
        self._kwargs = kwargs
        self._partial_sql = None

    def _build_sql(self, table_name, **kwargs):
        insert_sql = 'INSERT INTO {name} ({fields}) VALUES ({placeholders});'
        fields, values, placeholders = [], [], []

        for key, val in kwargs.items():
            fields.append(key)
            placeholders.append('?')
            values.append(val)

        sql = insert_sql.format(name=table_name, fields=', '.join(fields), placeholders=', '.join(placeholders))
        return self._clean_stmt(sql), values

    @property
    def sql(self):
        return self._build_sql(self._table_name, **self._kwargs)


class UpdateSQLStmt(SQLBuilder):

    def __init__(self, table_name, pk, pk_field, **kwargs):
        self._table_name = table_name
        self._pk = pk
        self._pk_field = pk_field
        self._kwargs = kwargs

    def _build_sql(self, table_name, pk, pk_field, **kwargs):
        update_sql = "UPDATE {table} SET {placeholders} WHERE {query};"
        query = f"{pk_field}=?"
        values, placeholders = [], []

        for key, val in kwargs.items():
            values.append(val)
            placeholders.append(f"{key}=?")

        values.append(pk)
        sql = update_sql.format(table=table_name, placeholders=', '.join(placeholders), query=query)
        return self._clean_stmt(sql), values

    @property
    def sql(self):
        return self._build_sql(self._table_name, self._pk, self._pk_field, **self._kwargs)


class DeleteSQLStmt(SQLBuilder):

    def __init__(self, table_name, **kwargs):
        self._table_name = table_name
        self._kwargs = kwargs

    def _build_sql(self, table_name, **kwargs):
        delete_sql = 'DELETE FROM {table} WHERE {query};'
        query, values = [], []

        for key, val in kwargs.items():
            values.append(val)
            query.append(f'{key}=?')

        sql = delete_sql.format(table=table_name, query=' AND '.join(query))
        return self._clean_stmt(sql), values

    @property
    def sql(self):
        return self._build_sql(self._table_name, **self._kwargs)


class ForeignKeySQLStmt(SQLBuilder):

    def __init__(self, model, field_name, on_field, on_delete='CASCADE', on_update='CASCADE'):
        self._model = model
        self._field_name = field_name
        self._on_field = on_field
        self._on_delete = on_delete
        self._on_update = on_update

    def _build_sql(self, model, field_name, on_field, on_delete='CASCADE', on_update='CASCADE'):
        sql = f"""
            FOREIGN KEY ({field_name})
            REFERENCES {model} ({on_field}) 
                ON UPDATE {on_update}
                ON DELETE {on_delete}
        """
        return self._clean_stmt(sql)

    @property
    def sql(self):
        return self._build_sql(self._model, self._field_name, self._on_field, self._on_delete, self._on_update)


class FieldSQLStmt(SQLBuilder):

    def __init__(self, type_, max_length=None, null=True, unique=False, default=None):
        self._type = type_
        self._max_length = max_length
        self._null = null
        self._unique = unique
        self._default = default

    def _build_sql(self, type_, max_length=None, null=True, unique=False, default=None):
        sql = f'{type_}'
        if max_length:
            sql = sql + f' ({max_length})'
        if null is False:
            sql = sql + ' NOT NULL'
        if unique:
            sql = sql + ' UNIQUE'
        if default is False or default:
            sql = sql + f' DEFAULT {default}'
        return self._clean_stmt(sql)

    @property
    def sql(self):
        return self._build_sql(self._type, self._max_length, self._null, self._unique, self._default)


class BaseQueryBuilder(SQLBuilder):

    def _join_partial_sqls(self, *statements, values=None):
        stmts = ''
        for stmt in statements:
            if stmt:
                stmts += stmt
        return stmts, values

    def _set_partial(self, partial, value):
        if value:
            partial = value
        return partial

    def _set_partials(self, sql=None, values=None, dict_=None):
        self._partial_sql = self._set_partial(self._partial_sql, sql)
        self._partial_values = self._set_partial(self._partial_values, values)
        self._partial_dict = self._set_partial(self._partial_dict, dict_)


class QueryBuilder(BaseQueryBuilder):

    def __init__(self):
        self._partial_sql = None
        self._partial_values = None
        self._partial_dict = None

    def _set_partials(self, stmt):
        self._partial_sql = self._set_partial(self._partial_sql, stmt.partial_sql)
        self._partial_values = self._set_partial(self._partial_values, stmt.partial_values)
        self._partial_dict = self._set_partial(self._partial_dict, stmt.partial_dict)

    def _get_partials(self):
        return self._partial_sql, self._partial_values, self._partial_dict

    def _render_stmt(self, klass, *args, **kwargs):
        stmt = klass(*args, **kwargs)
        sql = stmt.sql
        self._set_partials(stmt)
        return sql

    def select(self, table, fields, distinct=False):
        return self._render_stmt(SelectSQLStmt, table, fields, distinct)

    def where(self, *args):
        return self._render_stmt(WhereSQLStmt, *self._get_partials(), *args)

    def limit(self, value):
        return self._render_stmt(LimitSQLStmt, *self._get_partials(), value)

    def bulk_update(self, table_name, builder, **kwargs):
        return self._render_stmt(BulkUpdateSQLStmt, *self._get_partials(), table_name, builder, **kwargs)


class SelectSQLStmt(BaseQueryBuilder):

    def __init__(self, table, fields, distinct=False):
        self._table = table
        self._fields = fields
        self._distinct = distinct
        self._partial_sql = None
        self._partial_values = None
        self._partial_dict = None

    def _build_sql(self, table, fields, distinct=False):
        select_sql = 'SELECT {distinct} {fields} FROM {table}'
        sql = select_sql.format(
            table=table,
            fields=', '.join(fields),
            distinct=_config.DBMAPPER.DISTINCT if distinct else ''
        )
        self._set_partials(sql, self._partial_values, self._partial_dict)
        sql = sql + ';'
        return self._clean_stmt(sql)

    @property
    def sql(self):
        sql = self._build_sql(self._table, self._fields, self._distinct)
        return sql


class WhereSQLStmt(BaseQueryBuilder):

    def __init__(self, partial_sql, partial_values, partial_dict, *args):
        self._args = args
        self._partial_sql = partial_sql
        self._partial_values = partial_values
        self._partial_dict = partial_dict

    def _build_sql(self, *args):
        where_sql = ' WHERE {query}'

        query, operators, values = [], [], []
        for d in args:
            field = d['field']
            operator = d['operand']
            value = d['value']
            query.append(f"{field} {operator} ?")
            values.append(value)

        sql, values = self._join_partial_sqls(
            self._partial_sql,
            where_sql.format(query=' AND '.join(query)),
            values=values
        )
        self._set_partials(sql, values, self._args)
        sql = sql + ';'
        return self._clean_stmt(sql), values

    @property
    def sql(self):
        sql, values = self._build_sql(*self._args)
        return sql, values


class LimitSQLStmt(BaseQueryBuilder):

    def __init__(self, partial_sql, partial_values, partial_dict, value):
        self._partial_sql = partial_sql
        self._partial_values = partial_values
        self._partial_dict = partial_dict
        self._value = value

    def _build_sql(self, value):
        limit_sql = ' {limit} {value} '.format(limit=_config.DBMAPPER.LIMIT, value=value)
        sql, values = self._join_partial_sqls(
            self._partial_sql,
            limit_sql,
            values=self._partial_values
        )
        self._set_partials(sql)
        sql = sql + ';'
        return self._clean_stmt(sql), values

    @property
    def sql(self):
        return self._build_sql(self._value)


class BulkUpdateSQLStmt(BaseQueryBuilder):

    def __init__(self, partial_sql, partial_values, partial_dict, table_name, builder, **kwargs):
        self._partial_sql = partial_sql
        self._partial_values = partial_values
        self._partial_dict = partial_dict
        self._table_name = table_name
        self._kwargs = kwargs
        self._builder = builder

    def _build_sql(self, table_name, **kwargs):
        update_sql = 'UPDATE {table} SET {placeholders}'

        placeholders, values = [], []

        for key, val in kwargs.items():
            placeholders.append(f"{key}=?")
            values.append(val)

        sql = update_sql.format(table=table_name, placeholders=', '.join(placeholders))

        if self._partial_values and self._partial_dict:
            self._set_partials(sql, values, self._partial_dict)
            self._builder._set_partials(self)
            sql, _values = self._builder.where(*self._partial_dict)
            values += _values

        return self._clean_stmt(sql), values

    @property
    def sql(self):
        sql, values = self._build_sql(self._table_name, **self._kwargs)
        return sql, values


############################################
#       MAPPER
############################################
class DbMapper(BaseSQLDbMapper):
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
    __query_builder__ = QueryBuilder()

    def _render_foreign_key_sql_stmt(self, model, field_name, on_field, on_delete='CASCADE', on_update='CASCADE'):
        stmt = ForeignKeySQLStmt(model, field_name, on_field, on_delete, on_update)
        return stmt.sql

    def _render_field_sql_stmt(self, type_, max_length=None, null=True, unique=False, default=None):
        stmt = FieldSQLStmt(type_, max_length, null, unique, default)
        return stmt.sql

    def _render_create_table_sql_stmt(self, table_name, **kwargs):
        stmt = CreateTableSQLStmt(table_name, **kwargs)
        return stmt.sql

    def _render_insert_sql_stmt(self, table_name, **kwargs):
        stmt = InsertSQLStmt(table_name, **kwargs)
        return stmt.sql

    def _render_update_sql_stmt(self, table_name, pk, pk_field, **kwargs):
        stmt = UpdateSQLStmt(table_name, pk, pk_field, **kwargs)
        return stmt.sql

    def _render_delete_sql_stmt(self, table_name, **kwargs):
        stmt = DeleteSQLStmt(table_name, **kwargs)
        return stmt.sql

    def _render_select_sql_stmt(self, table, fields, distinct=False):
        return self.__query_builder__.select(table, fields, distinct)

    def _render_select_where_sql_stmt(self, *args):
        return self.__query_builder__.where(*args)

    def _render_bulk_update_sql_stmt(self, table_name, **kwargs):
        return self.__query_builder__.bulk_update(table_name, self.__query_builder__, **kwargs)

    def _render_limit_sql_stmt(self, value):
        return self.__query_builder__.limit(value)


############################################
#       DATABASE
###########################################
class SQLiteDatabase(BaseSQLDatabase):

    def __init__(self, db_path, check_same_thread=False, **kwargs):
        self._db = sq.connect(
            database=db_path,
            check_same_thread=check_same_thread,
            **kwargs
        )
        self._mapper = DbMapper()

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
        sql = "SELECT name FROM sqlite_master WHERE type=?;"
        qs = self.fetchall(sql, ('table',))
        tables = [x[0] for x in qs]
        return tables
