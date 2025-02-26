import os
from abc import abstractmethod

from tqa.common.configuration.config import load_config
from tqa.common.configuration.logger import get_logger
from tqa.common.errors.application_exception import ConfigException


class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        # elif hasattr(cls._instances.get(cls), "update"):
        #     cls._instances[cls] = cls._instances[cls].update(*args, **kwargs)
        return cls._instances[cls]

    @abstractmethod
    def update(self, *args, **kwargs):
        pass


# quito el singleton, el model_registry ya actua como un pseudo singleton asegurandose que
# no haya multiinstancias
class Service:
    name = None
    mandatory_keys = []

    def __init__(self, **kargs) -> None:
        self.config = load_config()
        self.logger = get_logger(self.name)
        self.service_config = self.config.get(self.name, {})

        self.ensure_mandatory_keys()
        self.load_attr(self.service_config)

    def update(self, *args, **kwargs):
        for key, value in kwargs.items():
            if key in self.__dict__:
                setattr(self, key, value)
        return self

    def load_attr(self, dict):
        for key, items in dict.items():
            setattr(self, key, items)

    def get(self, *args, search_in=None, not_found_value=None):
        search_in = self.service_config if search_in is None else search_in

        for arg in args:
            search_in = search_in.get(arg, {})

        return search_in if search_in != {} else not_found_value

    def join_paths(self, dict: dict, *args):
        paths = [dict.get(arg, None) for arg in args]
        if all(paths):
            return os.path.join(paths)
        else:
            non_args = [dict.get(arg, None) for arg in args if not dict.get(arg, None)]
            self.logger.error("No arguments in {}".format(non_args))

            return False

    def ensure_mandatory_keys(self):
        for key in self.mandatory_keys:
            if "." in key:
                if self.get(key.split(".")) is None:
                    raise ConfigException(
                        "No mandatory key {} in {}".format(key, self.name)
                    )
            else:
                if self.get(key) is None:
                    raise ConfigException(
                        "No mandatory key {} in {}".format(key, self.name)
                    )
        return True
