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
from .base import _config


def is_abstract_model(model):
    return model._meta.abstract


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
