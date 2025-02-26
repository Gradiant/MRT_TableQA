from typing import List, Optional

import pandas as pd

from tqa.coder.domain.services.service import (
    CoderService,
    ExplainerService,
    RunnerService,
)
from tqa.common.domain.entities.ExeContext import exeContext
from tqa.common.domain.services.InferenceService import InferenceService
from tqa.common.domain.services.Reporter import Reporter
from tqa.common.usecases.base import BaseUseCase
from tqa.common.configuration.logger import get_logger
logger = get_logger("explainer")

class ExplainUseCase(BaseUseCase):
    def __init__(
        self,
        question: str,
        table_columns: list,
        column_description: dict,
        max_steps: int,
        explainer: ExplainerService,
        inferer: InferenceService,
        reporter: Reporter = Reporter(),
        max_categories_for_describe=4,
    ):
        super().__init__()
        self.explainer = explainer
        self.question = question
        self.inferer = inferer
        self.table_columns = table_columns
        self.column_description = column_description
        self.max_steps = max_steps
        self.max_categories_for_describe = max_categories_for_describe
        self.reporter = reporter

    def execute(self, table_name: str = None):

        prompt = self.explainer.get_prompt(
            self.question,
            self.table_columns,
            self.column_description,
            self.max_steps,
            max_categories_for_describe=self.max_categories_for_describe,
            table_name=table_name,
        )

        try:
            llm_answer = self.inferer.inference(self.explainer.name, prompt)
        except Exception as e:
            raise Exception(f"Exception in explainer/inference: {e}")

        self._result = self.explainer.parse_llm_answer(llm_answer)

        self._result = self.explainer._correct_column_names(
            self._result, self.table_columns
        )

        if self.explainer.config.get("explainer").get("correct_prompt"):
            prompt_correction = self.explainer.get_prompt_correction(
                self._result,
                self.question,
                self.table_columns,
                self.column_description,
                max_categories_for_describe=self.max_categories_for_describe,
                table_name=table_name,
            )
            llm_answer_corrected = self.inferer.inference(self.explainer.name, prompt_correction)
            self._result = self.explainer.parse_llm_answer_corrected(
                llm_answer_corrected, self._result
            )

        # FIXME: do not know what to do with this (print on screen right now)
        # It might be interesting for filtering the df before the coder or just to check if the explainer is doing its job right
        used_columns_in_report = self.explainer.get_used_columns_in_instructions(
            self._result, self.table_columns
        )

        # print("Used Columns in Instructions", used_columns_in_report)
        self.used_columns_in_report = used_columns_in_report

        self.reporter.report_llm_out(
            "explainer", llm_out=llm_answer, parsed_out=self._result
        )
        logger.debug(self._result)


class RunnerUseCase(BaseUseCase):
    def __init__(
        self,
        df: pd.DataFrame,
        code_string: str,
        runner: RunnerService,
    ) -> None:
        super().__init__()
        self.df = df
        self.code_string = code_string
        self.runner = runner

    def execute(self) -> None:

        self._result = self.runner.try_run(self.code_string, self.df)


class CoderUseCase(BaseUseCase):
    def __init__(
        self,
        table_columns: List[str],
        list_of_steps: list[str],
        coder: CoderService,
        inferer: InferenceService,
        reporter: Reporter = Reporter(),
        old_code: str = None,
        old_code_exception: str = None,
    ):
        super().__init__()
        self.columns = table_columns
        self.list_of_steps = list_of_steps
        self.coder = coder
        self.inferer = inferer
        self._result = None
        self.reporter = reporter
        self.old_code = old_code
        self.old_code_exception = old_code_exception

    def execute_and_separate_lines(self) -> None:
        self.execute()
        self._result = self._result.split("\n")

    def execute(self) -> None:

        try:
            prompt = self.coder.get_prompt(
                self.columns, self.list_of_steps, self.old_code, self.old_code_exception
            )
            llm_answer = self.inferer.inference(self.coder.name, prompt)

            code = self.coder.parse_llm_answer(llm_answer)
            self.reporter.report_llm_out("coder", llm_out=llm_answer, parsed_out=code)
            works = self.coder.check_lsp(code)
            i = 0

            if not works:
                for i in range(5):
                    # aqui usas un parser "simple" para corregir la sintaxis
                    corrected_code = self.coder.correct_lsp(code)
                    works = self.coder.check_lsp(corrected_code)
                    if works:
                        code = corrected_code
                        break

                    # aqui un llm corrige la sintaxis
                    llm_checking_prompt = self.coder.correction_prompt(corrected_code)
                    llm_answer = self.inferer.inference(
                        self.coder.name, llm_checking_prompt
                    )

                    code = self.coder.parse_llm_answer(llm_answer)
                    self.reporter.report_llm_out(
                        "coder", llm_out=llm_answer, parsed_out=code
                    )
                    works = self.coder.check_lsp(code)
                    if works:
                        break
        except Exception as e:
            raise Exception(f"Exception INSIDE coder loop: {e}")  # forward

        if i == 4:
            self._result = "CODE IMPOSSIBLE TO EXECUTE"
            raise Exception("Code was not valid Python after 5 rounds of correction.")

        else:
            self._result = (
                "import pandas as pd\n" + code + "\nresult = parse_dataframe(df)"
            )
            # print(f"Coder output RESULT\n{self._result}")

    # """
    # FUNCION DONDE SE CONSTRUYE EL CODIGO DE MANERA INCREMENTAL (A STEPS)
    # def execute(self) -> None:
    #     "
    #     Step por step cambia el codigo para hacer lo que se le pide
    #     "
    #     current_state = "Not code exists yet"

    #     for c, step in enumerate(self.list_of_steps()):
    #         prompt = self.coder.get_prompt(step, current_state)
    #         llm_answer = self.inferer.inference(prompt)
    #         code = self.coder.parse_llm_answer(llm_answer)
    #         works = self.coder.check_lsp(code)
    #         if works:
    #             current_state = code
    #             continue
    #         for i in range(5):
    #             # aqui usas un parser "simple" para corregir la sintaxis
    #             corrected_code = self.coder.correct_lsp(code)
    #             works = self.coder.check_lsp(corrected_code)
    #             if works:
    #                 current_state = corrected_code
    #                 break

    #             # aqui un llm corrige la sintaxis
    #             llm_checking_prompt = self.coder.correction_prompt(corrected_code)
    #             llm_answer = self.inferer.inference(llm_checking_prompt)
    #             code = self.coder.parse_llm_answer(llm_answer)
    #             works = self.coder.check_lsp(code)
    #             if works:
    #                 current_state = code
    #                 break

    #         # no se pudo corregir la sintaxis
    #         if i == 4:
    #             self._result = "CODE IMPOSSIBLE TO EXECUTE"
    #             break

    #     if self._result is None:
    #         self._result = current_state"""

    # """
    # ESTO ES SI FUERA CODER-RUNNER
    # def execute(self):
    #     current_state = "Not code exists yet"
    #     for i, step in enumerate(self.list_of_steps()):
    #         # TODO sampling?
    #         prompt = self.coder.get_prompt(step, current_content)
    #         llm_answer = self.inferer.inference(prompt)
    #         code = self.coder.parse_llm_answer(llm_answer)
    #         works, promise = self.coder.try_run(code)

    #         if not works:
    #             # TODO loggear error
    #             for i in range(5): # correction tries?
    #                 corr_prompt = self.coder.correction_prompt(promise, code) # aqui promise = error
    #                 llm_answer = self.inferer.inference(corr_prompt)
    #                 code = self.coder.parse_llm_answer(llm_answer)
    #                 works, promise = self.coder.try_run(code)

    #                 if works:
    #                     break

    #             if i == 5: # 4?
    #                 self._result = "Error"
    #                 break

    #     if self._result is None:
    #         self._result = promise # promise = result aqui
    # """
