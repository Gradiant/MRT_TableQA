from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseUseCase(ABC):
    def __init__(self):
        super().__init__()
        self._result = None

    @property
    def result(self) -> Optional[str]:
        return self._result

    @abstractmethod
    def execute(self) -> None:
        pass
