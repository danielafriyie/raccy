"""
Provides utility functions for the ORM
"""


def is_abstract_model(model):
    return model._meta.abstract
