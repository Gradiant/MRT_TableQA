from abc import ABC, abstractmethod
from typing import Any


class AbstractRepository(ABC):
    @abstractmethod
    def list(self) -> list[Any]:
        pass

    @abstractmethod
    def get(self, entity: Any) -> Any:
        pass

    @abstractmethod
    def add(self, entity: Any) -> Any:
        pass

    @abstractmethod
    def remove(self, entity: Any) -> Any:
        pass

    @abstractmethod
    def update(self, entity: Any) -> Any:
        pass
