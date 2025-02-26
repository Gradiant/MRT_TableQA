from abc import ABC, abstractmethod
from typing import Any


class AbstractEngine(ABC):
    @abstractmethod
    def execute(self, sql: str) -> bool:
        pass

    @abstractmethod
    def query(self, sql: str) -> Any:
        pass
