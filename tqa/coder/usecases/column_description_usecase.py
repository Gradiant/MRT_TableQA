import json
import os
from typing import Dict, List

import pandas as pd

from tqa.coder.domain.services.column_descriptor_service import ColumnDescriptorService
from tqa.common.domain.entities.ExeContext import exeContext
from tqa.common.domain.services.InferenceService import InferenceService
from tqa.common.domain.services.Reporter import Reporter
from tqa.common.usecases.base import BaseUseCase


class ColumnDescriptorUseCase(BaseUseCase):
    def __init__(
        self,
        df: pd.DataFrame,
        descriptor_service: ColumnDescriptorService,
        inferer: InferenceService,
        num_attempts=15,
    ):
        super().__init__()

        self._descriptor_service = descriptor_service
        self._inferer = inferer
        self._df = df
        self._num_attempts = num_attempts
        self.reporter = Reporter()
        self._result = None

    @property
    def result(self) -> Dict:
        return self._result

    def execute(self, table_name: str):
        # call to service

        exeContext().get_or_new(question="", table_name="")

        saved_columns_description = (
            self._descriptor_service.get_column_descriptions_from_cache()
        )
        if saved_columns_description:
            columns_descriptions_table = (
                self._descriptor_service.get_table_descriptions(
                    saved_columns_description, table_name
                )
            )
            if columns_descriptions_table:
                self._descriptor_service.logger.info("table info loaded from cache")
                self._result = columns_descriptions_table
                exeContext().add(use_model="tmp")
                self.reporter.report_llm_out(
                    "descriptor", llm_out=columns_descriptions_table
                )
                return columns_descriptions_table

        self._descriptor_service.logger.info(len(self._df))
        analyze_result = self._descriptor_service._analyze_dataframe(self._df)
        self._descriptor_service.logger.info("Stats {}".format(analyze_result))

        serialization_list = self._descriptor_service.get_serialization_list(self._df)

        results = []

        for _table in serialization_list:

            error_response = None

            success = False

            for _ in range(self._num_attempts):
                system_prompt, user_prompt = self._descriptor_service._get_prompts(
                    _table["it_columns"], _table["table"]
                )

                if error_response is not None:
                    user_prompt = f"{user_prompt}\n{error_response}"

                self._descriptor_service.logger.debug(
                    "RES\n{}\n{}".format(system_prompt, user_prompt)
                )

                try:
                    _res = self._inferer.inference(
                        self._descriptor_service.name,
                        user_prompt,
                        "user",
                        system_prompt,
                        "system",
                    )
                except ValueError:
                    raise Exception

                self._descriptor_service.logger.debug("OPENAI OUT", _res)
                openai_str = _res

                self._descriptor_service.logger.debug("API RESPONSE:\n{}".format(_res))

                openai_str = openai_str.replace("```json", "")
                openai_str = openai_str.replace("\n```", "")

                try:
                    _cols_des = json.loads(openai_str)

                    if isinstance(_cols_des, dict):
                        _cols_des = [_cols_des]

                except json.decoder.JSONDecodeError:
                    print("Exception, emptying column descriptions")
                    _cols_des = {}

                    error_response = f"Your previous response contained format errors and cannot be loaded as a json array: {openai_str} Avoid those errors in your next answer or correct the wrong one."

                if len(_cols_des) != len(_table["it_columns"]):
                    continue

                self.reporter.report_llm_out(
                    "descriptor", llm_out=_res, parsed_out=_cols_des
                )

                results.append(_cols_des)

                success = True

                break

            if not success:
                _cols_des = []
                for _col in _table["it_columns"]:
                    _cols_des.append({"name": _col, "description": ""})

                results.append(_cols_des)

        column_desc = []

        for _res in results:
            column_desc += _res

        # print(analyze_result["columns"])
        # print(column_desc)

        # print("LEN RESULT", len(analyze_result["columns"]), len(column_desc))
        assert len(analyze_result["columns"]) == len(column_desc)

        for _col, _desc in zip(analyze_result["columns"], column_desc):
            _col["description"] = _desc

        saved_columns_description[table_name] = analyze_result
        self._descriptor_service.save_descriptions(saved_columns_description)

        self._result = analyze_result
