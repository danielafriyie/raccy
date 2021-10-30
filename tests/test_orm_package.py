import unittest
import os
import sys
from textwrap import dedent

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from raccy import model
from raccy.orm.utils import is_abstract_model
from raccy.core.exceptions import InsertError, QueryError, ModelDoesNotExist, ImproperlyConfigured
from raccy.orm.base import AttrDict, BaseSQLDbMapper
from raccy.orm.orm import Field


class BaseTestClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config = model.Config()
        config.DATABASE = model.SQLiteDatabase(':memory:')

        class AbstractModel(model.Model):
            name = model.CharField()
            age = model.IntegerField()

            class Meta:
                abstract = True

        class Dog(AbstractModel):
            pass

        class DogAudit(AbstractModel):
            dog_id = model.IntegerField()
            action = model.CharField()

        cls.Dog = Dog
        cls.DogAudit = DogAudit
        cls.AbstractModel = AbstractModel


class TestAttrDict(BaseTestClass):

    @classmethod
    def setUpClass(cls):
        cls.attrdict = AttrDict(name='Test', age=10, dob='21-04-1996')

    def test_getattr(self):
        self.assertEqual(self.attrdict.name, 'Test')
        self.assertEqual(self.attrdict.age, 10)
        self.assertEqual(self.attrdict.dob, '21-04-1996')

        with self.assertRaises(AttributeError):
            you = self.attrdict.you

    def test_setattr(self):
        self.assertEqual(self.attrdict.name, 'Test')
        self.attrdict.name = 'Hello'
        self.assertEqual(self.attrdict.name, 'Hello')
        self.assertEqual(self.attrdict.age, 10)
        self.attrdict.age = 99
        self.assertEqual(self.attrdict.age, 99)

        with self.assertRaises(AttributeError):
            self.attrdict.you = 'I am you!'


class TestConfig(BaseTestClass):

    @classmethod
    def setUpClass(cls):
        pass

    def test_single_instance(self):
        c1 = model.Config()
        c2 = model.Config()

        self.assertEqual(c1, c2)

        c1.DATABASE = model.SQLiteDatabase(':memory:')
        self.assertEqual(c1, c2)
        self.assertEqual(c1.DATABASE, c2.DATABASE)
        self.assertEqual(c1.DBMAPPER, c2.DBMAPPER)
        c2.foo = 'I am fooo'
        self.assertEqual(c2.foo, c1.foo)

    def test_setattr(self):
        config = model.Config()

        with self.assertRaises(ImproperlyConfigured):
            config.DATABASE = 'foo'

        config.DATABASE = model.SQLiteDatabase(':memory:')
        self.assertIsNotNone(config.DBMAPPER)
        self.assertIsInstance(config.DBMAPPER, BaseSQLDbMapper)

        with self.assertRaises(ImproperlyConfigured):
            config.DATABASE = None

    def test_getattribute(self):
        c = model.Config()

        with self.assertRaises(ImproperlyConfigured):
            c.DATABASE

        with self.assertRaises(ImproperlyConfigured):
            c.DBMAPPER


class TestSQLiteModelFields(BaseTestClass):

    def _test_field(self, field, type_, sql, *field_args, **field_kwargs):
        f = field(*field_args, **field_kwargs)
        self.assertEqual(type_, f._type)
        self.assertEqual(sql, f.sql)
        self.assertIsInstance(f, Field)

    def test_primary_key_field(self):
        self._test_field(model.PrimaryKeyField, 'INTEGER PRIMARY KEY AUTOINCREMENT',
                         'INTEGER PRIMARY KEY AUTOINCREMENT')

    def test_charfield(self):
        self._test_field(model.CharField, 'VARCHAR', 'VARCHAR (60)', max_length=60)

    def test_textfield(self):
        self._test_field(model.TextField, 'TEXT', 'TEXT NOT NULL', null=False)

    def test_integerfield(self):
        self._test_field(model.IntegerField, 'INTEGER', 'INTEGER')
        self._test_field(model.IntegerField, 'INTEGER', 'INTEGER DEFAULT 150', default=150)

    def test_floatfield(self):
        self._test_field(model.FloatField, 'DOUBLE', 'DOUBLE')
        self._test_field(model.FloatField, 'DOUBLE', 'DOUBLE DEFAULT 150', default=150)

    def test_booleanfield(self):
        self._test_field(model.BooleanField, 'BOOLEAN', 'BOOLEAN')
        self._test_field(model.BooleanField, 'BOOLEAN', 'BOOLEAN DEFAULT FALSE', default='FALSE')

    def test_datefield(self):
        self._test_field(model.DateField, 'DATE', 'DATE')

    def test_datetimefield(self):
        self._test_field(model.DateTimeField, 'DATETIME', 'DATETIME')

    def test_foreign_key_field(self):
        self._test_field(model.ForeignKeyField, 'INTEGER', 'INTEGER NOT NULL', model=self.Dog, on_field='pk')
        fk = model.ForeignKeyField(self.Dog, 'pk')
        fk_sql = f"""
            FOREIGN KEY (fk)
            REFERENCES {self.Dog.objects.table_name} (pk) 
                ON UPDATE CASCADE
                ON DELETE CASCADE
        """
        self.assertEqual(dedent(fk_sql), fk._foreign_key_sql('fk'))


#
# class TestModels(unittest.TestCase):
#
#     @classmethod
#     def setUpClass(cls) -> None:
#         cls.author1 = Author()
#         cls.author2 = Author()
#         cls.post1 = Post()
#         cls.post2 = Post()
#
#     def test_model_meta(self):
#         self.assertTrue(hasattr(self.author1, '__mappings__'))
#         self.assertTrue(hasattr(self.author1, '__table_name__'))
#         self.assertTrue(hasattr(self.author1, '_meta'))
#         self.assertTrue(hasattr(self.author1, 'objects'))
#         self.assertTrue(hasattr(Author, 'objects'))
#         self.assertTrue(hasattr(self.post2, '__mappings__'))
#         self.assertTrue(hasattr(self.post2, '__table_name__'))
#         self.assertTrue(hasattr(self.post2, '_meta'))
#         self.assertTrue(hasattr(self.post2, 'objects'))
#         self.assertTrue(hasattr(Post, 'objects'))
#         self.assertTrue(hasattr(Post, '__pk__'))
#         self.assertTrue(hasattr(Author, '__pk__'))
#
#         for key in self.author1.__mappings__.keys():
#             self.assertFalse(hasattr(self.author1, key))
#
#         for key in self.post2.__mappings__.keys():
#             self.assertFalse(hasattr(self.post2, key))
#
#     def test_single_instance(self):
#         self.assertEqual(self.author1, self.author2)
#         self.assertEqual(self.post1, self.post2)
#         self.assertEqual(self.author1, Author())
#
#     def test_table(self):
#         self.assertEqual(self.author1.objects.table_name, 'author')
#         self.assertEqual(self.author1.__table_name__, self.author2.objects.table_name)
#         self.assertEqual(self.post1.objects.table_name, 'post')
#         self.assertEqual(self.post2.objects.table_name, Post.__table_name__)
#         self.assertEqual(self.post1.objects._get_primary_key_field(), '_pk')
#         self.assertEqual(self.author1.objects._get_primary_key_field(), 'author_id')
#         self.assertEqual(self.author1.objects._get_primary_key_field(), Author.objects._get_primary_key_field())
#         self.assertEqual(self.post2.objects._get_primary_key_field(), Post.objects._get_primary_key_field())
#         self.assertNotEqual(Author.objects._get_primary_key_field(), Post.objects._get_primary_key_field())
#
#         a_fields = ['author_id', 'name', 'age']
#         p_fields = ['author_id', 'post', '_pk']
#         self.assertEqual(self.author1.objects._table_fields, a_fields)
#         self.assertEqual(self.post2.objects._table_fields, p_fields)
#
#         author_data = dict(name='Daniel Afriyie', age=25)
#         id_ = self.author1.objects.create(**author_data)
#         a_sql = 'INSERT INTO author (name, age) VALUES (?, ?);'
#         self.assertEqual(
#             self.author1.objects._db_mapper._render_insert_sql_stmt(self.author1.objects.table_name, **author_data)[0],
#             a_sql
#         )
#         self.post1.objects.insert(author_id=id_, post='This is a test post')
#
#         with self.assertRaises(InsertError):
#             self.post1.objects.bulk_insert([1, 'This is a new post'])
#         with self.assertRaises(InsertError):
#             self.post1.objects.create(post='This is a new post', wrong_field='wrong field')
#
#         self.assertTrue(is_abstract_model(AbstractModel))
#         self.assertTrue(is_abstract_model(AbstractModel()))
#         self.assertFalse(is_abstract_model(Author))
#         self.assertFalse(is_abstract_model(Post))
#         self.assertFalse(is_abstract_model(self.post2))
#         self.assertFalse(is_abstract_model(self.author1))
#
#     def test_crud_operations(self):
#         self.author1.objects.bulk_insert(
#             dict(name='Daniel Afriyie', age=25),
#             dict(name='David Afriyie', age=32),
#             dict(name='John Afriyie', age=43),
#             dict(name='Yaw Afriyie', age=12),
#             dict(name='Jesus Afriyie', age=90)
#         )
#         self.post2.objects.bulk_insert(
#             dict(author_id=1, post='This is post 1'),
#             dict(author_id=2, post='This is post 1'),
#             dict(author_id=3, post='This is post 1'),
#             dict(author_id=4, post='This is post 1')
#         )
#
#         a1 = self.author1.objects.get(name='Daniel Afriyie', age=25)
#         a2 = self.author1.objects.get(name='David Afriyie', age=32)
#         a3 = self.author1.objects.get(name='John Afriyie', age=43)
#         self.assertEqual(a1.name, 'Daniel Afriyie')
#         self.assertEqual(a2.age, 32)
#         self.assertEqual(a3.name, 'John Afriyie')
#
#         p1 = self.post2.objects.get(author_id=a1.author_id)
#         self.assertEqual(p1.author_id, a1.author_id)
#
#         a3.update(name='John New Update')
#         a4 = self.author1.objects.get(name='John New Update')
#         self.assertEqual(a4.name, 'John New Update')
#
#         with self.assertRaises(ModelDoesNotExist):
#             self.post1.objects.get(author_id=990)
#             self.author1.objects.get(author_id=999)
#
#         qs = self.post2.objects.all()
#         self.assertIsInstance(qs, map)
#         for query in qs:
#             self.assertIsInstance(query, model.QuerySet)
#
#
# class TestQuery(unittest.TestCase):
#
#     @classmethod
#     def setUpClass(cls) -> None:
#         cls.author = Author()
#
#     def test_query(self):
#         self.author.objects.bulk_insert(
#             dict(name='Daniel Afriyie', age=25),
#             dict(name='David Afriyie', age=32),
#             dict(name='John Afriyie', age=43),
#             dict(name='Yaw Afriyie', age=12),
#             dict(name='Jesus Afriyie', age=90)
#         )
#
#         with self.assertRaises(QueryError):
#             self.author.objects.select(['author_idf', 'name', 'age'])
#
#         query = self.author.objects.select(['author_id', 'name', 'age'])
#         self.assertIsInstance(query, model.BaseQuery)
#         self.assertIsInstance(query.get_data, list)
#         self.assertEqual(query.state, 'select')
#         query = query.where(age=25, name='David Afriyie')
#         self.assertEqual(query.state, 'where')
#
#         with self.assertRaises(QueryError):
#             query._fields = None
#             query.where(age=20)
#
#         data = self.author.objects.select(['*']).get_data
#         query = model.Query(data, self.author.objects.table_name)
#         self.assertIsInstance(query.get_data, list)
#         self.assertIsInstance(query, model.BaseQuery)
#
#         with self.assertRaises(QueryError):
#             query.where(name='Test Name')
#             query.bulk_update(name='Yaw')


if __name__ == '__main__':
    unittest.main()
