import os

import pandas as pd

from tqa.common.domain.services.Reporter import Reporter
from tqa.common.usecases.base import BaseUseCase
from tqa.common.utils import ensure_path, get_str_date, read_json


class ReportUseCase(BaseUseCase):
    def __init__(self, reporter: Reporter):
        super().__init__()
        self.reporter = reporter

    def execute(self):
        self.reporter.make_excel()


class SupervisorUseCase(BaseUseCase):
    def __init__(self, reporter: Reporter, files: list):
        super().__init__()
        self.reporter = reporter
        self.files = files

    def execute(self):
        self._result=self.reporter.save_supervisors(self.files)
