import os
from typing import Dict

import pandas as pd

from tqa.coder.domain.services.service import InterpreterService
from tqa.common.domain.services.InferenceService import InferenceService
from tqa.common.domain.services.Reporter import Reporter
from tqa.common.errors.application_exception import InterpreterException
from tqa.common.usecases.base import BaseUseCase
from tqa.common.utils import ensure_path, eval_secure, get_str_date, read_json


class InterpretUseCase(BaseUseCase):
    def __init__(
        self,
        question: str,
        answer: str,
        interpreter: InterpreterService,
        inferer: InferenceService,
        reporter: Reporter = Reporter()
    ):
        super().__init__()
        self.question = question
        self.answer = answer
        self.interpreter = interpreter
        self.inferer = inferer
        self._result = None
        self.reporter = reporter

    @property
    def result(self) -> Dict:
        return self._result

    def execute(self):

        try:
            prompt_types = self.interpreter.get_prompt_types(self.question)
        except Exception as e:
            raise Exception("Error in get_prompt: {}".format(str(e)))

        try:
            llm_response = self.inferer.inference("interpreter", prompt_types)
        except Exception as e:
            raise Exception("Error in inferer: {}".format(str(e)))

        try:
            type_response = self.interpreter.parse(llm_response, return_string=True)
        except Exception as e:
            raise Exception("Error in parse: {}".format(str(e)))

        try:
            prompt = self.interpreter.get_prompt(
                self.question, self.answer, type_response
            )
        except Exception as e:
            raise Exception("Error in get_prompt: {}".format(str(e)))

        try:
            llm_response = self.inferer.inference("interpreter", prompt)
        except Exception as e:
            raise Exception("Error in inferer: {}".format(str(e)))

        try:
            final_response = self.interpreter.parse(llm_response)
        except Exception as e:
            final_response = eval_secure(self.answer)

            if final_response:
                self._result = final_response
                return final_response
            elif isinstance(self.answer, str):
                self._result = self.answer
                return self.answer
            raise Exception("Error in parse: {}".format(str(e)))

        self.reporter.report_llm_out(
            "interpreter",
            llm_out=llm_response,
            parsed_out=final_response,
            answer_type=type_response,
        )

        self._result = final_response
