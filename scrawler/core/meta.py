class SingletonMeta(type):
    """
    Singleton metaclass: restricts the instantiation of a class to one object
    """
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]
