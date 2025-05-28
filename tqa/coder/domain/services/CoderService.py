import ast
import inspect
import re
from lib2to3.refactor import RefactoringTool, get_fixers_from_package
from typing import Dict, List, Tuple, Union

import autoflake
import autopep8
import pandas as pd

from tqa.coder.domain.services import coder_internal_functions
from tqa.coder.domain.services.service import ServicePrompting, add_subindex
from tqa.common.domain.services.CoderParserService import CodeParserService

# from tqa.common.utils import ensure_path, read_text


class CoderService(ServicePrompting):
    name = "coder"
    internal_functions_descriptions = Dict[str, str]

    def __init__(self, **kargs):
        super().__init__(**kargs)
        self.use_simple_names = self.config.get("use_simplified_column_names", False)
        self.internal_functions = self._load_internal_functions_descriptions()

    def _load_internal_functions_descriptions(self):
        descriptions = {}
        for name, value in vars(coder_internal_functions).items():
            if name.startswith("_") or not callable(value):
                continue

            doc = inspect.getdoc(value)
            descriptions[name] = doc
        return descriptions

    def simplify_column_names(
        self, column_names: List, column_descriptions: dict
    ) -> pd.DataFrame:
        if not self.use_simple_names or not column_descriptions:
            return column_names

        new_column_names = []
        for column in column_descriptions.get("columns"):
            simple_name = column.get("description").get("simple_name")
            original_name = column.get("name")

            if (
                self.use_simple_names
                and simple_name
                and simple_name not in new_column_names
            ):
                new_column_names.append(simple_name)
            elif (
                self.use_simple_names
                and simple_name
                and simple_name in new_column_names
            ):
                # avoid repeated names of columns. Same transformation than in explainer
                simple_name = add_subindex(simple_name, 1, new_column_names)
                new_column_names.append(simple_name)
            else:
                new_column_names.append(original_name)

        return new_column_names

    def get_prompt(
        self,
        original_question: str,
        dataframe_columns: List[str],
        list_of_steps: List[str],
        old_code=None,
        old_code_error=None,
    ) -> str:
        """
        Returns a prompt for asking for code
        """

        try:

            if old_code and old_code_error:
                self.logger.debug("Persiste system active")
                return self.get("template_persist").format(
                    dataframe_columns,
                    "\n".join(
                        [
                            str(i) + "." + " " + step
                            for i, step in enumerate(list_of_steps, start=1)
                        ]
                    ),
                    "\n".join(
                        [
                            f"- {name}: {description}"
                            for name, description in self.internal_functions.items()
                        ]
                    ),
                    old_code,
                    old_code_error,
                )
            else:
                return self.get("template").format(
                    original_question,
                    dataframe_columns,
                    "\n\n".join([f"- {name}: {description}" for name,description in self.internal_functions.items()]),
                    "\n".join(
                        [
                            str(i) + "." + " " + step
                            for i, step in enumerate(list_of_steps, start=1)
                        ]
                    ),
                    "\n".join(
                        [
                            f"- {name}: {description}"
                            for name, description in self.internal_functions.items()
                        ]
                    ),
                )
        except Exception as e:
            raise Exception(f"template was not in coder - config {e}")

    def try_run(self, code: str) -> Tuple[bool, str]:
        """
        DEPRECATED

        Refer to Runner service / use case
        """
        ...

    def correction_prompt(self, current_content: str) -> str:
        """
        Returns a prompt for correcting the code
        """
        try:
            return self.get("correction_template").format(current_content)
        except Exception as e:
            raise Exception(f"correction template was not in coder - config {e}")

    # TODO: revisar el coder parser
    def parse_llm_answer(self, llm_answer: str):
        """
        Parsers the python code from the answer of the llm
        """
        try:
            # imports, functions = self._extract_code_lines(llm_answer)
            parser = CodeParserService()
            result = parser.code_parser(llm_answer)
        except Exception as e:
            raise Exception(f"python code parsing failed {e}")
        return result
        # if len(imports) == 0 and len(functions) == 0:
        #     raise Exception("No python code was parsed from the answer")
        # return "\n".join(imports) + "\n" + "\n".join(functions)

    def check_lsp(self, code: str) -> bool:
        """
        Checks the syntax in the lsp
        """
        works, _ = self._check_ast(code)  # error is expected to be syntax error
        return works

    def correct_lsp(self, code: str) -> str:
        """
        Applies basic syntax corrector
        """
        for correction in [
            self._autopep8_correction,
            self._autoflake_correction,
            self._lib23_correction,
        ]:
            try:
                corrected_code = correction(code)
                code = corrected_code
            except Exception:
                # code = code
                pass
        return code

    def _extract_code_lines(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Returns:
            - List of import calls
            - List of functions
        """
        # compilamos las 3 regexp
        python_markdown_code_re = re.compile(r"```python\n(.*?)```")
        # bloques de funcion
        # empieza por def, seguido del formato texto(funcion?):
        # se asegura de que empieze por espacio o tabulador para una nueva linea de la funcion
        function_block_re = re.compile(r"(def\s+\w+\(.*?\):\n(?:\s+.*\n)*)")
        # TODO llamada a lo import
        import_line_re = re.compile(
            r"(?im)^\s*(from\s+[\w\.]+\s+import\s+[\w\*,\s]*|import\s+[\w\.,\s]+)"
        )

        # Caso 1, hay markdown de python
        code_blocks = python_markdown_code_re.findall(text, re.DOTALL)

        # Caso 2, no hay markdown de python
        if not code_blocks:
            code_blocks = [text]

        just_code = "\n".join(code_blocks)
        # buscamos bloques de funcion y bloques de importacion
        function_blocks = function_block_re.findall(just_code)
        import_lines = import_line_re.findall(just_code)

        return import_lines, function_blocks

    def _check_ast(self, code: str) -> Tuple[bool, Union[str, None]]:
        """
        Intenta parsear el codigo a ast
        """
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, str(e)

    def _autopep8_correction(self, code_str: str) -> str:
        """
        More stetic than functional

        Atuomatically corrects the code based on PEP8 standard
        """
        return autopep8.fix_code(code_str)

    def _autoflake_correction(self, code_str: str):
        """
        More stetic than functional

        Corrects the code using flake
        """
        return autoflake.fix_code(code_str, remove_unused_variables=True)

    def _lib23_correction(self, code_str: str):
        """
        Applies a python2 to 3 library for parsing simple errors (i.e. lack of parenthesis)
        """
        # Inicias el fixer
        fixers = get_fixers_from_package("lib2to3.fixes")
        refactor_tool = RefactoringTool(fixers)

        try:
            # Devuelve el Arbol Corregido
            corrected_tree = refactor_tool.refactor_string(code_str, "<string>")
            corrected_code = str(corrected_tree)
            return corrected_code
        except Exception:
            # No es capaz de corregirlo
            return code_str
