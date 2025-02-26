from typing import Optional


class AplicationException(Exception):
    def __init__(self, root_exception: Optional[Exception], *args: object) -> None:
        self._root_exception = root_exception
        self._error_description = str(self.get_error_description())

        super().__init__(args)

    def get_error_description(self) -> str:
        return str(self._root_exception)


class ConfigException(AplicationException):
    pass


class ContextException(AplicationException):
    pass


class InterpreterException(AplicationException):
    pass
