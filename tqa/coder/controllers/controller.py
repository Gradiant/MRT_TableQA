import os
import re
from typing import Dict, List

import pandas as pd

from tqa.coder.domain.services.column_selector_service import ColumnSelectorService
from tqa.coder.domain.services.column_descriptor_service import ColumnDescriptorService
from tqa.coder.domain.services.CoderService import CoderService
from tqa.coder.domain.services.service import (
    ExplainerService,
    InterpreterService,
    RunnerService,
    FormatterSemevalService,
)
from tqa.coder.usecases.column_description_usecase import ColumnDescriptorUseCase
from tqa.coder.usecases.process_table_usecase import (
    ProcessAllTablesUseCase,
    ProcessTableUseCase,
)
from tqa.coder.usecases.process_batches_usecase import ProcessAllTablesBatchUseCase
from tqa.coder.usecases.qa_usecase import CoderUseCase, ExplainUseCase
from tqa.coder.usecases.report_usecase import ReportUseCase, SupervisorUseCase
from tqa.common.configuration.config import load_config
from tqa.common.domain.services.InferenceService import InferenceService
from tqa.common.domain.services.Reporter import Reporter
from tqa.common.configuration.logger import get_logger


logger = get_logger("code_controller")

class CoderController:
    def __init__(self) -> None:
        self.config = load_config()
        self.inferencer = InferenceService()
        self.explainer = ExplainerService()
        self.coder = CoderService()
        self.descriptor = ColumnDescriptorService()
        self.column_selector = ColumnSelectorService()
        self.runner = RunnerService()
        self.interpreter = InterpreterService()
        self.formatter = FormatterSemevalService()
        self.columns_descriptions: dict = None

    def explain(
        self,
        question: str,
        table_columns: List[str],
        column_description: dict,
        max_steps: int,
    ) -> List[str]:

        uc = ExplainUseCase(
            question,
            table_columns,
            column_description,
            max_steps,
            self.explainer,
            self.inferencer,
        )
        uc.execute()
        return uc.result

    def code(self, question, table_columns: List[str], steps: List[str]) -> str:
        uc = CoderUseCase(table_columns, steps, question, self.coder, self.inferencer, self.columns_descriptions)
        uc.execute()
        return uc.result

    def describe_columns(self, df: pd.DataFrame, table_name: str) -> Dict:
        uc = ColumnDescriptorUseCase(df, self.descriptor, self.inferencer)
        uc.execute(table_name)
        return uc.result

    def process_all_tables(
        self,
        result_path=None,
    ):

        
        uc = ProcessAllTablesUseCase(
            self.descriptor,
            self.column_selector,
            self.explainer,
            self.inferencer,
            self.coder,
            self.runner,
            self.interpreter
        )
        uc.execute(result_path)
        return uc.result

    def process_table(
        self, question: str, df: pd.DataFrame, max_steps=5, table_name=None
    ) -> Dict:

        uc = ProcessTableUseCase(
            question,
            df,
            table_name,
            self.descriptor,
            self.column_selector,
            self.explainer,
            self.inferencer,
            self.coder,
            self.runner,
            self.interpreter,
            max_step=max_steps,
        )
        uc.execute()
        return uc.result

    def process_all_tables_batch(self, result_path=None, max_steps=5,exe_steps=["descriptor","selector", "explainer","coder","runner","interpreter","formatter"],mode="full"):
        
        logger.info("Calling Batch Processing")

        uc = ProcessAllTablesBatchUseCase(
            self.descriptor,
            self.column_selector,
            self.explainer,
            self.inferencer,
            self.coder,
            self.runner,
            self.interpreter,
            self.formatter,
            max_steps,
            exe_steps=exe_steps,
            mode=mode
        )
        uc.execute(result_path)
        return uc.result

    def process_report(self, execution_path="reports"):
        uc = ReportUseCase(Reporter())

        uc.execute()
        return uc.result

    def process_supervisors_files(self, files_supervisors=[]):
        uc = SupervisorUseCase(Reporter(), files_supervisors)
        uc.execute()
        return uc.result
