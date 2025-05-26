import os
import traceback
from typing import List

import pandas as pd
from tqdm import tqdm

from tqa.coder.domain.services.CoderService import CoderService
from tqa.coder.domain.services.column_descriptor_service import ColumnDescriptorService
from tqa.coder.domain.services.column_selector_service import ColumnSelectorService
from tqa.coder.domain.services.service import (
    ExplainerService,
    FormatterSemevalService,
    InterpreterService,
    RunnerService,
)
from tqa.coder.usecases.column_description_usecase import ColumnDescriptorUseCase
from tqa.coder.usecases.column_selector_usecase import ColumnSelectorUseCase
from tqa.coder.usecases.formatter_usecase import FormatterUseCase
from tqa.coder.usecases.interpreter_usecase import InterpretUseCase
from tqa.coder.usecases.process_table_usecase import run_use_case
from tqa.coder.usecases.qa_usecase import CoderUseCase, ExplainUseCase, RunnerUseCase
from tqa.common.configuration.config import load_config
from tqa.common.configuration.logger import get_logger
from tqa.common.domain.entities.Dataset import Dataset
from tqa.common.domain.entities.ExeContext import exeContext
from tqa.common.domain.services.InferenceService import InferenceService
from tqa.common.domain.services.Reporter import Reporter
from tqa.common.errors.application_exception import InterpreterException
from tqa.common.usecases.base import BaseUseCase
from tqa.common.utils import read_csv, save_csv, save_json

logger = get_logger("batch_usecase")


class ProcessAllTablesBatchUseCase(BaseUseCase):

    steps = [
        "descriptor",
        "selector",
        "explainer",
        "coder",
        "runner",
        "interpreter",
        "formatter",
    ]

    def __init__(
        self,
        descripter: ColumnDescriptorService,
        column_selector: ColumnSelectorService,
        explainer: ExplainerService,
        inferer: InferenceService,
        coder: CoderService,
        runner: RunnerService,
        interpreter: InterpreterService,
        formatter: FormatterSemevalService,
        max_steps: int = 5,
        exe_steps=[
            "descriptor",
            "explainer",
            "coder",
            "runner",
            "interpreter",
            "formatter",
        ],
        mode="full",
    ):
        self._descripter = descripter
        self._column_selector = column_selector
        self._explainer = explainer
        self._inferer = inferer
        self._coder = coder
        self._runner = runner
        self._interpreter = interpreter
        self._formatter = formatter
        self._max_steps = max_steps
        self.exe_steps = exe_steps
        self.mode = mode
        self.columns_descriptions = None

    def _run_module(
        self,
        module_name: str,
        prev_res=None,
        df=None,
        columns_descriptions=None,
        table_name=None,
        question=None,
        batch=None,
    ) -> tuple[List | dict, dict]:
        """_summary_

        Args:
            module_name (str): name of the module
            prev_res (_type_, optional): result of the revious module. Defaults to None.

        Returns:
            tuple[List|dict,dict]: returns the ouput of the function run_use_case
        """

        match module_name:
            case "descriptor":
                result, info_extra = run_use_case(
                    ColumnDescriptorUseCase,
                    df,
                    self._descripter,
                    self._inferer,
                    **{"table_name": table_name},
                )
                # self.columns_descriptions = result
                return result, info_extra
            case "selector":
                result, info_extra = run_use_case(
                    ColumnSelectorUseCase,
                    df,
                    question,
                    prev_res,  # self.columns_descriptions,
                    self._column_selector,
                    self._inferer,
                    **{"table_name": table_name},
                )
                df = result
                columns_descriptions = info_extra.get("columns_descriptions")
                info_extra = {}
                return (df, columns_descriptions), info_extra
            case "explainer":

                return run_use_case(
                    ExplainUseCase,
                    question,
                    df,
                    self.columns_descriptions,
                    self._max_steps,
                    self._explainer,
                    self._inferer,
                    self._reporter,
                    10,  # max_categories_for_describe
                    **{"table_name": table_name},
                )

            case "coder":
                return run_use_case(
                    CoderUseCase,
                    df.columns,
                    prev_res,
                    question,
                    self._coder,
                    self._inferer,
                    self._reporter,
                    None,
                    None,
                    self.columns_descriptions,
                )

            case "runner":
                max_persist = 3

                for persist_count in range(0, max_persist + 1):
                    try:
                        result = run_use_case(
                            RunnerUseCase,
                            df,
                            prev_res,
                            self._runner,
                            self.columns_descriptions,
                        )

                    except Exception as e:

                        if persist_count == max_persist:
                            raise e

                        old_code = prev_res
                        exception_lines = traceback.format_exc().splitlines()
                        separation_line = [
                            line
                            for line in exception_lines
                            if "During handling" in line
                        ]
                        index = (
                            exception_lines.index(separation_line[0])
                            if separation_line
                            else len(separation_line)
                        )
                        exception_lines = exception_lines[0:index]
                        old_exception = "{}".format("\n".join(exception_lines).strip())

                        prev_res = run_use_case(
                            CoderUseCase,
                            df.columns,
                            batch["explainer"],
                            question,
                            self._coder,
                            self._inferer,
                            self._reporter,
                            old_code,
                            old_exception,
                            self.columns_descriptions,
                        )[0]

                        if old_code == prev_res:
                            print("Same code")
                        else:
                            print("corrected!")
                        batch["coder"] = prev_res
                        continue
                    break

                return result

            case "interpreter":
                return run_use_case(
                    InterpretUseCase,
                    question,
                    prev_res,
                    self._interpreter,
                    self._inferer,
                    self._reporter,
                )
            case "formatter":
                return run_use_case(
                    FormatterUseCase, prev_res, self._formatter, self._reporter
                )

    def _create_batch_supervisor(self, tables_info):
        return [
            dict(
                {
                    "table": table.get("table_name"),
                    "question": question.get("question"),
                    "exe_id": exeContext()
                    .get_or_new(
                        table_name=table.get("table_name"),
                        question=question.get("question"),
                    )
                    .exe_id,
                    "answer": question.get("answer", None),
                },
                **dict(
                    {step: None for step in self.steps},
                    **{"error": False, "exe": False},
                ),
            )
            for table in tables_info
            for question in table.get("questions")
        ]

    def _mode_condition(self, batch, step):

        logger.info("Mode {}".format(self.mode))
        logger.info("Batch error {}".format(batch.get("error")))
        logger.info("Batch exe {}".format(batch.get("exe")))

        match self.mode:
            case "full":
                return not batch.get("exe") and not batch.get("error")
            case "errors":
                if "Exception" in str(batch.get(step)):
                    return True
                if batch.get(step, None) is None:
                    return True
                if isinstance(batch.get(step, []), list) or isinstance(
                    batch.get(step, []), dict
                ):
                    if not batch.get(step, []):
                        return True
                else:
                    if pd.isna(batch.get(step, pd.NA)):
                        return True
                return False
            case "force":
                return True

    def execute(self, result_path=None):
        self._reporter = Reporter(result_path)
        dataset_service = Dataset()
        tables_set = dataset_service.get_data()
        tables_set = tables_set
        tables_info = dataset_service.format_data_for_batch_exec(tables_set)
        exe_supervisor_path = self._reporter.exe_supervisor_path
        save_json(
            os.path.join(self._reporter.report_path, "config.json"), load_config()
        )
        batch_supervisor = (
            self._create_batch_supervisor(tables_info)
            if not os.path.isfile(exe_supervisor_path)
            else read_csv(exe_supervisor_path)
        )
        for batch in batch_supervisor:
            for key, item in batch.items():
                try:
                    batch[key] = eval(str(item))
                except Exception:
                    pass

        current_table = ""

        df = None

        for step in self.steps:

            logger.info("Doing step {}".format(step))

            prev_step = (
                self.steps[self.steps.index(step) - 1]
                if self.steps.index(step) - 1 >= 0
                else ""
            )
            for batch in tqdm(batch_supervisor, desc="Procesing step: {}".format(step)):
                exeContext().get_or_new(batch.get("table"), batch.get("question"))

                if step in self.exe_steps:
                    df = (
                        dataset_service.get_tabular_df(batch.get("table"))
                        if current_table != batch.get("table")
                        else df
                    )
                    current_table = batch.get("table")
                    prev_res = batch.get(prev_step, None)

                    logger.info("Check condition {}".format(step))

                    if self._mode_condition(batch, step):

                        logger.info("Passed condition {}".format(step))

                        if step in [
                            "explainer",
                            "coder",
                            "runner",
                            "interpreter",
                            "formatter",
                        ]:
                            df = batch.get("selector")[0]
                            self.columns_descriptions = batch.get("selector")[1]
                        try:

                            logger.info("Running module {}".format(step))

                            batch[step] = self._run_module(
                                step,
                                prev_res,
                                df,
                                table_name=batch.get("table"),
                                question=batch.get("question"),
                                batch=batch,
                            )[0]

                            if step == "selector" and batch["selector"]:
                                batch["selector_simple"] = {
                                    "num_columns": len(
                                        batch["selector"][1].get("columns")
                                    ),
                                    "columns_filtered": [
                                        col.get("name")
                                        for col in batch["selector"][1].get("columns")
                                    ],
                                }

                        except Exception as e:

                            logger.error("Error {}".format(str(e)))
                            
                            batch[step] = "Exception: " + str(traceback.format_exc())
                            batch["error"] = True
                            pass
                        except InterpreterException as e:

                            logger.error("Error {}".format(str(e)))

                            batch[step] = "Exception: " + str(traceback.format_exc())
                            batch["error"] = True
                            pass
                    save_csv(
                        exe_supervisor_path, pd.DataFrame.from_records(batch_supervisor)
                    )

                if step == self.steps[-1]:
                    batch["exe"] = True

        save_csv(exe_supervisor_path, pd.DataFrame.from_records(batch_supervisor))
        self._result = exe_supervisor_path
