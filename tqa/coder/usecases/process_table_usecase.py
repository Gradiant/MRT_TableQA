import os
import re
from time import time
from typing import List, Optional

import pandas as pd
from tqdm import tqdm

from tqa.coder.domain.services.column_descriptor_service import ColumnDescriptorService
from tqa.coder.domain.services.service import (
    CoderService,
    ExplainerService,
    InterpreterService,
    RunnerService,
)
from tqa.coder.usecases.column_description_usecase import ColumnDescriptorUseCase
from tqa.coder.usecases.interpreter_usecase import InterpretUseCase
from tqa.coder.usecases.qa_usecase import CoderUseCase, ExplainUseCase, RunnerUseCase
from tqa.common.configuration.logger import get_logger
from tqa.common.domain.entities.Dataset import Dataset
from tqa.common.domain.entities.ExeContext import exeContext
from tqa.common.domain.services.InferenceService import InferenceService
from tqa.common.domain.services.Reporter import Reporter
from tqa.common.errors.application_exception import InterpreterException
from tqa.common.usecases.base import BaseUseCase
from tqa.common.utils import ensure_path, get_str_date, read_csv, save_csv, save_json

logger = get_logger("usecases")


def run_use_case(
    usecase_class: str, *load_params, **execute_params
) -> tuple[List | dict, dict]:
    """Execute an usecase: CoderUseCase,ExplainUseCase,ColumnDescriptorUseCase,InterpretUseCase or RunnerUsecase.
    All usecases have load params which mush be added to the constructor of the class, and mandatory params for the execution.
    Finally, all usecases save its results in the variable _results and could have specific variables to be printed in the trace systen (info_extra)

    Args:
        usecase_class (str): string with Usecase class, p.e. ColumndescirptorUsecase, ExplainUseCase, etc.

    Returns:
        uc.result: Execution results for each usecase
        info_extra: Initizalate to None, but could contain a dict which will be added to the execution trace.
    """
    uc = usecase_class(*load_params)
    uc.execute(**execute_params),
    info_extra = {"info_extra": None}
    if usecase_class == ExplainUseCase:
        info_extra = {"info_extra": uc.used_columns_in_report}
    return uc.result, info_extra


class ProcessTableUseCase(BaseUseCase):
    def __init__(
        self,
        question: str,
        df: pd.DataFrame,
        table_name: str,
        descripter: ColumnDescriptorService,
        explainer: ExplainerService,
        inferer: InferenceService,
        coder: CoderService,
        runner: RunnerService,
        interpreter: InterpreterService,
        reporter: Reporter = None,
        max_step: int = 5,
        max_persist: int = 3,
    ):
        self._question = question
        self._df = df
        self._table_name = table_name
        self._descripter = descripter
        self._explainer = explainer
        self._inferer = inferer
        self._coder = coder
        self._runner = runner
        self._max_steps = max_step
        self.reporter = reporter if reporter else Reporter()
        self._interpreter = interpreter
        self.old_code = None
        self.old_code_exception = None
        self.max_persist = max_persist

    def _run_module(self, module_name: str, prev_res=None) -> tuple[List | dict, dict]:
        """_summary_

        Args:
            module_name (str): name of the module
            prev_res (_type_, optional): result of the revious module. Defaults to None.

        Returns:
            tuple[List|dict,dict]: returns the ouput of the function run_use_case
        """
        match module_name:
            case "descriptor":
                return run_use_case(
                    ColumnDescriptorUseCase,
                    self._df,
                    self._descripter,
                    self._inferer,
                    **{"table_name": self._table_name},
                )
            case "explainer":
                return run_use_case(
                    ExplainUseCase,
                    self._question,
                    self._df.columns,
                    prev_res,
                    self._max_steps,
                    self._explainer,
                    self._inferer,
                    Reporter(),
                    **{"table_name": self._table_name},
                )
            case "coder":
                return run_use_case(
                    CoderUseCase,
                    self._df.columns,
                    prev_res,
                    self._coder,
                    self._inferer,
                    self.old_code,
                    self.old_code_exception,
                )
            case "runner":
                return run_use_case(RunnerUseCase, self._df, prev_res, self._runner)
            case "interpreter":
                return run_use_case(
                    InterpretUseCase,
                    self._question,
                    prev_res,
                    self._interpreter,
                    self._inferer,
                )

    def execute(self):
        """This function

        Raises:
            Exception: _description_
            e: _description_

        Returns: result saved in _result variable.
        """

        # set execution context for trace system
        execution = exeContext().get_or_new(
            question=self._question, table_name=self._table_name
        )
        exeContext().set_current(exe_id=execution.exe_id)

        # module declaration
        modules = ["descriptor", "explainer", "coder", "runner", "interpreter"]

        prev_res = None
        results = {}

        persist_count = 0
        i_coder = modules.index("coder")
        self.old_code = None
        self.old_code_exception = None
        i = 0
        secure_loop = 15
        loop = 0

        # TODO: clean df and set simple columns
        self._df = Dataset().clean_column_names(self._df)

        while i < len(modules):

            if loop >= secure_loop:
                raise Exception("Secure loop:15 loops in while")
            else:
                loop += 1

            module = modules[i]

            try:
                prev_res, info_extra = self._run_module(module, prev_res)
                results[module] = prev_res

                self.reporter.report_trace(
                    module,
                    self._table_name,
                    self._question,
                    state=True,
                    result=prev_res,
                    persist_count=persist_count,
                    use_model=self._inferer.key_matching.get(
                        module, self._inferer.key_matching.get("default")
                    ),
                    **info_extra,
                )

            except Exception as e:
                for module_name in modules[i::]:
                    self.reporter.report_trace(
                        module_name,
                        self._table_name,
                        self._question,
                        state="Exception:{}".format(e)
                        if module_name == module
                        else False,
                        result=False,
                        runer_out=None,
                        persist_count=persist_count,
                    )
                if module == "runner":
                    if persist_count <= self.max_persist:
                        persist_count += 1
                        self.old_code = results["coder"]
                        self.old_code_exception = "Exception:{}".format(e)
                        i = (
                            i_coder - 1
                        )  # posicionamos i para que el siguiente modulo sea el coder
                        prev_res = results[
                            "explainer"
                        ]  # dejamos preparada la entrada que necesita el coder
                    else:
                        raise Exception("Exception: Persist system out " + str(e))
                else:
                    raise e

            i += 1

        self._result = prev_res

        return prev_res

class ProcessAllTablesUseCase(BaseUseCase):
    def __init__(
        self,
        descripter: ColumnDescriptorService,
        explainer: ExplainerService,
        inferer: InferenceService,
        coder: CoderService,
        runner: RunnerService,
        interpreter: InterpreterService,
        max_execution: int = None,
        times_per_table: bool = False,
        filter_answer_type: str = None,
    ):
        self._descripter = descripter
        self._explainer = explainer
        self._inferer = inferer
        self._coder = coder
        self._runner = runner
        self.max_execution = max_execution
        self.times_per_table = times_per_table
        self.filter_answer_type = filter_answer_type
        self._interpreter = interpreter

    def execute(self, result_path=None):

        result_path = (
            "execution_{}".format(get_str_date()) if not result_path else result_path
        )
        dataset_service = Dataset()
        tables_set = dataset_service.get_data()
        exe_supervisor_path = Reporter().exe_supervisor_path

        if os.path.isfile(exe_supervisor_path):
            supervisor_data = read_csv(exe_supervisor_path)
        else:
            supervisor_data = [
                {
                    "date": get_str_date(),
                    "table": table["table_name"],
                    "question": question.get("question"),
                    "exe": False,
                    "true": question.get("answer"),
                    "pred": None,
                }
                for table in tables_set
                for question in table["questions"]
            ]

        tables_to_process = [
            (d.get("table"), d.get("question"))
            for d in supervisor_data
            if d.get("exe") is False
        ]
        
        logger.info(
            "tables to process {}/{}".format(
                len(tables_to_process), len(supervisor_data)
            )
        )

        executions = 0
        for table_set in tables_set:
            times = 0

            dataset_name = table_set["table_name"]
            df = dataset_service.get_tabular_df(dataset_name)

            for question_dict in tqdm(
                table_set["questions"],
                desc="Processing questions from {}".format(dataset_name),
            ):

                question = question_dict.get("question")
                answers = question_dict.get("answer")
                if (dataset_name, question) in tables_to_process:
                    if self.filter_answer_type:
                        answer_type = (
                            type(eval(answers)).__name__ if answers != "" else "str"
                        )
                        if self.filter_answer_type != answer_type:
                            break

                    exeContext().new(
                        question=question, table_name=dataset_name, answer=answers
                    )

                    uc = ProcessTableUseCase(
                        question,
                        df,
                        dataset_name,
                        self._descripter,
                        self._explainer,
                        self._inferer,
                        self._coder,
                        self._runner,
                        self._interpreter,
                    )
                    res = None
                    try:
                        res = uc.execute()
                    except Exception as e:
                        logger.error(e)
                        # raise e
                        res = "Exception " + str(e)
                    except InterpreterException as e:
                        logger.error(e)
                        # raise e
                        res = "Exception " + str(e)

                    supervisor_entry = {
                        "date": get_str_date(),
                        "table": dataset_name,
                        "question": question,
                        "exe": True,
                        "true": answers,
                        "pred": res,
                    }
                    index_old_entry = supervisor_data.index(
                        [
                            entry
                            for entry in supervisor_data
                            if entry.get("table") == dataset_name
                            and entry.get("question") == question
                        ][0]
                    )
                    supervisor_data.pop(index_old_entry)
                    supervisor_data.insert(index_old_entry, supervisor_entry)
                    save_csv(
                        exe_supervisor_path, pd.DataFrame.from_records(supervisor_data)
                    )
                    logger.debug(
                        "Table:{} and question {} processed".format(
                            dataset_name, question
                        )
                    )
                    executions += 1
                    times += 1
                    if self.max_execution:
                        if executions >= self.max_execution:
                            self._result = result_path
                            return self._result

                    if self.times_per_table:
                        if times >= self.times_per_table:
                            break

        self._result = result_path

