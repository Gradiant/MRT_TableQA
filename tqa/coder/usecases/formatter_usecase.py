import os
from typing import Dict

import pandas as pd

from tqa.coder.domain.services.service import FormatterSemevalService
from tqa.common.domain.services.InferenceService import InferenceService
from tqa.common.domain.services.Reporter import Reporter
from tqa.common.usecases.base import BaseUseCase
from tqa.common.utils import ensure_path, eval_secure, get_str_date, read_json


class FormatterUseCase(BaseUseCase):
    def __init__(
        self,
        resultado: str,
        formatter: FormatterSemevalService,
        reporter: Reporter=Reporter()
    ):
        super().__init__()
        self.resultado = resultado
        self._formatter = formatter
        self._result = None
        self.reporter = reporter

    @property
    def result(self) -> Dict:
        return self._result

    def execute(self):

        self._result = self._formatter.format(self.resultado)
