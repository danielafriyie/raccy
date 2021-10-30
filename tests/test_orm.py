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
from raccy.orm.orm import Field, QuerySet
from raccy.orm.signals import before_insert, after_insert, before_update, after_update, before_delete, after_delete
from raccy.core.signals import receiver


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


class TestModelSignals(BaseTestClass):

    def test_before_and_after_insert(self):
        self.var = None

        @receiver(before_insert, self.Dog)
        def sig_before_insert(instance):
            if instance.age < 10:
                raise ValueError("Dog cannot be less than 10 years old")
            self.var = 'before insert'

        @receiver(after_insert, self.Dog)
        def sig_after_insert(instance):
            self.assertEqual(self.var, 'before insert')
            self.var = 'after insert'
            self.DogAudit.objects.create(
                dog_id=instance.pk,
                name=instance.name,
                age=instance.age,
                action='After Insert'
            )

        with self.assertRaises(ValueError):
            self.Dog.objects.create(
                name='Bee',
                age=8
            )

        with self.assertRaises(ValueError):
            dog = self.Dog()
            dog.objects.create(
                name='Billy',
                age=2
            )

        self.assertIsNone(self.var)

        d1 = dict(name='Dog1', age=12)
        d2 = dict(name='Dog2', age=32)

        self.Dog.objects.create(**d1)
        dg1 = self.Dog.objects.get(name='Dog1', age=12)
        dga1 = self.DogAudit.objects.get(dog_id=dg1.pk, age=dg1.age)
        self.assertEqual(dg1.name, dga1.name)
        self.assertEqual(dg1.age, dga1.age)
        self.assertEqual(dg1.pk, dga1.dog_id)

        self.Dog.objects.create(**d2)
        dg2 = self.Dog.objects.get(name='Dog2', age=32)
        dga2 = self.DogAudit.objects.get(dog_id=dg2.pk, age=dg2.age)
        self.assertEqual(dg2.name, dga2.name)
        self.assertEqual(dg2.age, dga2.age)
        self.assertEqual(dg2.pk, dga2.dog_id)

        self.assertEqual(self.var, 'after insert')

    def test_before_and_after_update(self):
        self.var = None

        @receiver(before_update, self.Dog)
        def sig_before_update(new, old):
            if old.name == 'Dogu1':
                raise ValueError('Cannot update Dogu1')
            if new.age < old.age:
                raise ValueError('New date cannot be less than old age')
            self.var = 'before update'

        @receiver(after_update, self.Dog)
        def sig_after_update(new, old):
            self.assertEqual(self.var, 'before update')
            self.DogAudit.objects.create(
                dog_id=new.pk,
                name=new.name,
                age=new.age,
                action='After Update'
            )
            self.var = 'after update'

        self.Dog.objects.bulk_insert(
            dict(name='Dogu1', age=12),
            dict(name='Dogu2', age=78)
        )
        d1 = self.Dog.objects.get(name='Dogu1', age=12)
        d2 = self.Dog.objects.get(name='Dogu2', age=78)
        with self.assertRaises(ValueError):
            d1.update(name='New Name')

        with self.assertRaises(ValueError):
            d2.update(age=8)

        self.assertIsNone(self.var)

        d2.update(age=99)
        self.assertEqual(self.var, 'after update')
        ud = self.Dog.objects.get(name='Dogu2')
        self.assertEqual(ud.age, 99)

    def test_before_and_after_delete(self):
        self.var = None
        self.Dog.objects.bulk_insert(
            dict(name='Dogd1', age=12),
            dict(name='Dogd2', age=78)
        )

        @receiver(after_delete, self.Dog)
        def sig_after_delete(instance):
            self.assertEqual(self.var, 'before delete')
            self.var = 'after delete'

        @receiver(before_delete, self.Dog)
        def sig_before_delete(instance):
            if instance.name == 'Dogd1':
                raise ValueError('Cannot delete Dogd1')
            self.var = 'before delete'

        with self.assertRaises(ValueError):
            self.Dog.objects.delete(name='Dogd1')

        self.assertIsNone(self.var)

        self.Dog.objects.delete(name='Dogd2')
        self.assertEqual(self.var, 'after delete')


class TestModels(BaseTestClass):

    def test_model_meta(self):
        self.assertTrue(hasattr(self.Dog, '__mappings__'))
        self.assertTrue(hasattr(self.Dog, '__table_name__'))
        self.assertTrue(hasattr(self.Dog, '_meta'))
        self.assertTrue(hasattr(self.Dog, 'objects'))
        self.assertTrue(hasattr(self.DogAudit, 'objects'))
        self.assertTrue(hasattr(self.Dog(), '__mappings__'))
        self.assertTrue(hasattr(self.Dog(), '__table_name__'))
        self.assertTrue(hasattr(self.Dog(), '_meta'))
        self.assertTrue(hasattr(self.Dog(), 'objects'))
        self.assertTrue(hasattr(self.DogAudit(), 'objects'))
        self.assertTrue(hasattr(self.Dog(), '__pk__'))
        self.assertTrue(hasattr(self.DogAudit(), '__pk__'))
        self.assertFalse(is_abstract_model(self.Dog))
        self.assertFalse(is_abstract_model(self.DogAudit))
        self.assertTrue(is_abstract_model(self.AbstractModel))

        for key in self.Dog.__mappings__.keys():
            self.assertFalse(hasattr(self.Dog, key))

        for key in self.DogAudit.__mappings__.keys():
            self.assertFalse(hasattr(self.DogAudit, key))

    def test_single_instance(self):
        self.assertEqual(self.Dog(), self.Dog())
        self.assertEqual(self.DogAudit(), self.DogAudit())

    def test_table(self):
        self.assertEqual(self.Dog.objects.table_name, 'dog')
        self.assertEqual(self.DogAudit.objects.table_name, 'dogaudit')
        self.assertEqual(self.Dog.objects._primary_key_field, 'pk')
        self.assertEqual(self.DogAudit.objects._primary_key_field, 'pk')

        dog_fields = sorted(['name', 'age', 'pk'])
        dog_audit_fields = sorted(['name', 'age', 'dog_id', 'action', 'pk'])
        self.assertEqual(sorted(self.Dog.objects._table_fields), dog_fields)
        self.assertEqual(sorted(self.DogAudit.objects._table_fields), dog_audit_fields)

    def test_crud_operations(self):
        self.Dog.objects.bulk_insert(
            dict(name='Dog1', age=25),
            dict(name='Dog2', age=32),
            dict(name='Dog3', age=43),
            dict(name='Dog4', age=12),
            dict(name='Dog5', age=90)
        )

        d1 = self.Dog.objects.get(name='Dog1', age=25)
        d2 = self.Dog.objects.get(name='Dog2', age=32)
        d3 = self.Dog.objects.get(name='Dog3', age=43)
        self.assertEqual(d1.name, 'Dog1')
        self.assertEqual(d2.age, 32)
        self.assertEqual(d3.name, 'Dog3')

        with self.assertRaises(ModelDoesNotExist):
            self.Dog.objects.get(pk=990)
            self.Dog.objects.get(pk=999)

        qs = self.Dog.objects.all()
        self.assertIsInstance(qs, map)
        for query in qs:
            self.assertIsInstance(query, QuerySet)


if __name__ == '__main__':
    unittest.main()
