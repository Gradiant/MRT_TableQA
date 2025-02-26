from typing import Dict

from tqa.common.configuration.config import load_config
from tqa.common.configuration.logger import get_logger
from tqa.common.domain.services.Service import SingletonMeta
from tqa.common.errors.application_exception import ContextException
from tqa.common.utils import get_str_date

logger = get_logger("context")


class Execution:
    id: int = 0
    question: str = ""
    table_name: str = ""
    answer: str = ""
    use_model: str = ""

    def __init__(
        self,
        exe_id: int = 0,
        question: str = None,
        table_name: str = None,
        answer: str = "",
        use_model: str = "",
    ):
        self.question = question
        self.table_name = table_name
        self.answer = answer
        self.use_model = use_model
        self.exe_id = exe_id if exe_id != 0 else int(get_str_date("%Y%m%d%H%M%S"))


class exeContext(metaclass=SingletonMeta):

    current_execution: Execution = None
    executions: Dict[int, Execution] = {}

    def new(
        self,
        question: str = None,
        table_name: str = None,
        answer: str = "",
        use_model: str = "",
    ):

        exe = Execution(0, question, table_name, answer, use_model)
        self.executions[exe.exe_id] = exe
        self.current_execution = exe
        return exe

    def get(
        self,
        question: str = None,
        table_name: str = None,
        answer: str = "",
        use_model: str = "",
    ):
        for exe_id, exe in self.executions.items():

            if exe.question == question and exe.table_name == table_name:
                self.current_execution = exe
                return exe
        logger.warning(
            "No execution with parameters {},{},{}".format(question, table_name, answer)
        )
        return None

    def get_or_new(
        self,
        question: str = None,
        table_name: str = None,
        answer: str = "",
        use_model: str = "",
    ):
        exe = self.get(question, table_name, answer, use_model)
        if not exe:
            return self.new(question, table_name, answer, use_model)
        else:
            return exe

    def set_current(self, exe_id: int):
        if exe_id in self.executions:
            self.current_execution = self.executions.get(exe_id)
        else:
            logger.warning(
                "No {} execution. Keep current execution: {}".format(
                    exe_id, self.current_execution.exe_id
                )
            )

        return self.current_execution

    def add(
        self,
        question: str = None,
        table_name: str = None,
        answer: str = "",
        use_model: str = "",
    ):  
        if self.current_execution:
            self.current_execution.question = (
                question if question else self.current_execution.question
            )
            self.current_execution.table_name = (
                table_name if table_name else self.current_execution.table_name
            )
            self.current_execution.answer = (
                answer if answer else self.current_execution.answer
            )
            self.current_execution.use_model = (
                use_model if use_model else self.current_execution.use_model
            )
        return self.current_execution

    def change(
        self,
        exe_id: int = 0,
        question: str = None,
        table_name: str = None,
        answer: str = "",
        use_model: str = "",
    ):
        if exe_id == self.current_execution:
            self.current_execution.question = (
                question if question else self.current_execution.question
            )
            self.current_execution.table_name = (
                table_name if table_name else self.current_execution.table_name
            )
            self.current_execution.answer = (
                answer if answer else self.current_execution.answer
            )
            self.current_execution.use_model = (
                use_model if use_model else self.current_execution.use_model
            )
        elif exe_id in self.executions:
            self.executions.get(exe_id).question = (
                question if question else self.execution.get(exe_id).question
            )
            self.executions.get(exe_id).table_name = (
                table_name if table_name else self.execution.get(exe_id).table_name
            )
            self.executions.get(exe_id).answer = (
                answer if answer else self.execution.get(exe_id).answer
            )
            self.executions.get(exe_id).use_model = (
                use_model if use_model else self.execution.get(exe_id).use_model
            )
            logger.warning("{} changed but is not the current execution".format(exe_id))
        else:
            logger.warning(
                "No {} execution. Keep current execution: {}".format(
                    exe_id, self.current_execution.exe_id
                )
            )
