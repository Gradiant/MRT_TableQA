import traceback
from typing import Dict

import pandas as pd

from tqa.coder.domain.services.column_selector_service import ColumnSelectorService
from tqa.common.configuration.logger import get_logger
from tqa.common.domain.entities.ExeContext import exeContext
from tqa.common.domain.services.InferenceService import InferenceService
from tqa.common.domain.services.Reporter import Reporter
from tqa.common.usecases.base import BaseUseCase

logger = get_logger("column_selector")


class ColumnSelectorUseCase(BaseUseCase):
    def __init__(
        self,
        df: pd.DataFrame,
        question: str,
        columns_descriptions: dict,
        selector_service: ColumnSelectorService,
        inferer: InferenceService,
    ):
        super().__init__()

        self.question = question
        self.columns_descriptions = columns_descriptions
        self._selector_service = selector_service
        self._inferer = inferer
        self._df = df
        self.reporter = Reporter()
        self._result = None

    @property
    def result(self) -> Dict:
        return self._result

    def execute(self, table_name: str = ""):

        exeContext().get_or_new(question="", table_name="")
        try:
            columns_useful = []
            cols = self.columns_descriptions.get(
                "columns"
            )  # [0:10] + self.columns_descriptions.get("columns")[-5:]
            for chunk_columns in self._selector_service.chunk_list_columns(cols):

                system_prompt, user_prompt = self._selector_service._get_prompts(
                    chunk_columns, self._df, self.question
                )

                _res = self._inferer.inference(
                    self._selector_service.name,
                    user_prompt,
                    "user",
                    system_prompt,
                    "system",
                )

                exeContext().add(use_model="tmp")
                self.reporter.report_llm_out("selector", llm_out=_res)

                columns_useful_chunk = self._selector_service.parse_columnlist(_res)
                columns_valid_chunk = self._selector_service.filter_valid_columns(
                    columns_useful_chunk, self._df
                )
                columns_useful.extend(columns_valid_chunk)

            columns_useful = self._selector_service.check_too_much_columns(
                columns_useful
            )

            # Remove columns duplicates
            columns_useful = list(set(columns_useful))

            self.columns_descriptions, self._df = self._selector_service.filter_columns(
                self._df, self.columns_descriptions, columns_useful
            )

            logger.info("Columns useful {}".format(columns_useful))

            self.columns_descriptions = self.columns_descriptions  # results filtered
            self._result = self._df
        except ValueError:
            print(traceback.format_exc())
            logger.info(traceback.format_exc())
            raise Exception

        return self._result
