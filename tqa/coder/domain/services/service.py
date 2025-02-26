import ast
import locale
import os
import re
import textwrap
from lib2to3.refactor import RefactoringTool, get_fixers_from_package
from typing import Any, Callable, Iterable, List, Optional, Tuple, Union

import autoflake
import autopep8
import pandas as pd
from pandas.api.types import is_numeric_dtype

from tqa.common.domain.services.CoderParserService import CodeParserService
from tqa.common.domain.services.Service import Service
from tqa.common.utils import ensure_path, eval_secure, read_jsonl


class ServicePrompting(Service):
    mandatory_keys = ["trash", "trash_file", "max_len_trash"]

    def __init__(self, **kargs):
        super().__init__(**kargs)

        os.makedirs(ensure_path(self.trash), exist_ok=True)
        self.file_path = os.path.join(ensure_path(self.trash), self.trash_file)
        if os.path.isfile(self.file_path):
            trash_data = read_jsonl(self.file_path)
        else:
            trash_data = []
        i = 1
        name = self.trash_file.split(".")[0]
        while len(trash_data) >= self.max_len_trash:

            filename = "{}_{}.jsonl".format(name, i)
            self.file_path = os.path.join(ensure_path(self.trash), filename)
            if os.path.isfile(self.file_path):
                trash_data = read_jsonl(self.file_path)
            else:
                trash_data = []

class FormatterSemevalService(ServicePrompting):
    name = "formatter"

    def __init__(self, **kargs):
        super().__init__(**kargs)
        
    def format(self,result:str|float|int|list|dict):
        return self._format_semeval(result)
        
    def _format_semeval(self, result: str | list | dict | bool):
            if isinstance(result, list):
                return self._try_sub_parse_list(result)

            elif isinstance(result, str):
                if self._is_int(result):
                    return int(result)
                new_res = self._try_number(result)
                if new_res is None:
                    return result
                else:
                    return new_res
            elif isinstance(result,tuple):
                return list(result)
            else:
                return result
            return result

    def _try_sub_parse_list(
        self, list_of_elements: List[str]
    ) -> Union[List[str], List[float], List[int]]:
        """
        Triest
        list of str ["", "", ""] -> list of:
        - float [1,2.0,3]
        - int [1,2,3]
        - str (stays the same)
        """
        _list_nums = []
        _list_ints = []
        flag_num, flag_int = 1, 1

        for element in list_of_elements:
            if flag_num:
                num = self._try_number(element)
                if num is None:
                    flag_num = 0
                else:
                    _list_nums.append(num)
                if self._is_int(element):
                    int_el = int(element)
                    _list_ints.append(int_el)
                else:
                    flag_int = 0

            if not flag_num and not flag_int:
                break

        # floats tienen prioridad
        if flag_int and flag_num:
            if all(True if i==f else False for i,f in zip(_list_ints,_list_nums)):
                return _list_ints
            else:
                return _list_nums
        if flag_int:
            return _list_ints
        if flag_num:
            return _list_nums

        return list_of_elements

    def _try_number(self, num_str):
        """
        Tries str -> num || returns either the number or None (not possible)
        """
        # Step 1: Try locale-based parsing for different number formats
        try:
            # Attempt to use comma as thousand separator and period as decimal point
            locale.setlocale(locale.LC_NUMERIC, "en_US.UTF-8")  # US format
            return locale.atof(num_str)
        except ValueError:
            pass
        except Exception:
            pass

        try:
            # Da error
            # locale.setlocale(locale.LC_NUMERIC, 'eu')  # European format
            # return locale.atof(num_str)
            # los type ignore es pq no entiende que hay un try-catch
            if "." in num_str and "," in num_str:
                num_str = float(num_str.replace(".", "").replace(",", "."))  # type: ignore
            elif "." in num_str and not "," in num_str:
                num_str = float(num_str)
            else:
                num_str = float(num)
            return num_str  # type: ignore
        except ValueError:
            pass
        except Exception:
            pass

        try:
            # normal float?
            num = float(num_str)
            return num
        except ValueError:
            pass
        except Exception:
            pass

        return None

    def _is_int(self, string: str):
        try:
            _ = int(string)
            return True
        except Exception:
            return False
        
        
class InterpreterService(ServicePrompting):
    name = "interpreter"

    def __init__(self, **kargs):
        super().__init__(**kargs)

    def get_prompt(self, question: str, answer: str, answer_type: str) -> str:
        try:
            return self.prompt.format(question, answer, answer_type, answer_type)
        except Exception as e:
            raise Exception(f"Exception in interpreter/get_prompt: {e}")

    def get_prompt_types(self, question: str) -> str:
        try:
            return self.prompt_types.format(question)
        except Exception as e:
            raise Exception(f"Exception in interpreter/get_prompt: {e}")

    def parse(self, llm_response, return_string=False):
        
        if str(llm_response).lower() in ["boolean","string","number","list of string","list of numbers"]:
            return llm_response
        
        try:
            eval_response = eval(llm_response)
        except Exception:
            eval_response = None
            

        if eval_response:
            return eval_response

        response = re.findall(r"```markdown(.*)```", llm_response, re.DOTALL)
        if len(response) == 0:
            response = re.findall(r"```python(.*)```", llm_response, re.DOTALL)
        if len(response) == 0:
            response = re.findall(r"```json(.*)```", llm_response, re.DOTALL)

        if len(response) >= 1:
            self.logger.warning("More than one results parsed {}".format(response))

            try:
                final_response = eval(response[0].strip("\n").strip(" "))
                
            except Exception as e:
                if return_string:
                    return response[0].strip("\n").strip(" ")
                else:
                    raise e
            return final_response

        else:
            raise Exception("Nothing parsed")

    


class ExplainerService(ServicePrompting):
    name = "explainer"

    def __init__(self, **kargs):
        super().__init__(**kargs)
        self.template_explainer = self.config.get("explainer").get("template")

    def get_prompt(
        self,
        question: str,
        column_names: List[str],
        column_descriptions: List[dict],
        max_steps: int,
        max_categories_for_describe: int = 4,
        table_name: str = None,
    ) -> str:
        try:
            columns_section = self.get_columns_prompt(
                column_names, column_descriptions, max_categories_for_describe
            )
            table_name_section = self.get_table_name_section(table_name)
            return self.template_explainer.format(
                table_name_section, columns_section, question, max_steps
            )
        except Exception as e:
            raise Exception(f"Exception in explainer/get_prompt: {e}")

    def get_prompt_correction(
        self,
        current_prompt: List,
        question: str,
        column_names: List[str],
        column_descriptions: List[dict],
        max_categories_for_describe: int = 4,
        table_name: str = None,
    ) -> str:

        try:
            columns_section = self.get_columns_prompt(
                column_names, column_descriptions, max_categories_for_describe
            )
            table_name_section = self.get_table_name_section(table_name)
            return self.template_correction.format(
                table_name_section, columns_section, question, str(current_prompt)
            )
        except Exception as e:
            raise Exception(f"Exception in explainer/get_prompt: {e}")

    def get_table_name_section(self, table_name):
        if not table_name:
            return ""
        return "\nThe name of the table is: " + str(table_name) + "."

    def get_columns_prompt(
        self, table_columns, column_descriptions=None, max_categories_show=4
    ):
        if not column_descriptions:
            return str(table_columns)
        else:
            columns_section = ""
            for column in column_descriptions.get("columns"):
                options = column.get("freq_values", [])
                unique_values = column.get("unique", 1000)
                description = column.get("description").get("description")
                name = column.get("name")
                type_data = column.get("type")
                min_value = column.get("min")
                max_value = column.get("max")
                missing_values = column.get("missing_values")
                columns_section += '\n- "' + name + '": ' + description
                columns_section += " Type: " + column.get("type") + "."
                if (
                    type_data == "category"
                    and options
                    and 0 < len(options) <= max_categories_show
                    and unique_values < max_categories_show
                ):
                    columns_section += " Options are: " + ", ".join(options) + "."
                elif (
                    type_data == "category"
                    and options
                    and unique_values > max_categories_show
                ):
                    columns_section += (
                        " Some examples of values for this column are: "
                        + ", ".join(options)
                        + "."
                    )

                if (
                    is_numeric_dtype(type_data)
                    and min_value is not None
                    and max_value is not None
                ):
                    columns_section += (
                        " The range of values goes from "
                        + str(min_value)
                        + " (min) to "
                        + str(max_value)
                        + " (max)."
                    )

                if missing_values == 0:
                    columns_section += " This column has no missing values."

            return columns_section

    def _correct_column_names(self, instructions: List[str], column_names: List[str]):
        """Correct the column names with typical llm errors"""

        conflictive_column_names = []

        for _column in column_names:
            if "<" in _column:
                _column_parts = _column.split("<")
                if len(_column_parts[0]) > 0:
                    conflictive_column_names.append([_column, _column_parts[0]])

        if len(conflictive_column_names) > 0:
            for _column in conflictive_column_names:
                pattern = re.compile(r"\b" + re.escape(_column[1]) + r"\b")
                for i, _inst in enumerate(instructions):
                    instructions[i] = pattern.sub(_column[0], _inst)

        return instructions

    def get_used_columns_in_instructions(
        self, instructions: List[str], column_names: List[str]
    ) -> List[str]:
        """Get the columns used in the instructions"""

        used_columns = set()

        for _column in column_names:
            # Create a pattern to match the exact column name
            pattern = re.compile(r"\b" + re.escape(_column) + r"\b")
            for _inst in instructions:
                if pattern.search(_inst):
                    used_columns.add(_column)

        return list(used_columns)

    def parse_llm_answer(self, llm_answer: str):
        try:
            llm_answer = llm_answer.replace("\n", " ")
            # splits by dots but avoiding spliting decimal dots in numbers
            instructions = re.split(r"(?<=\D)\.(?=.)|(?<=\d)\.(?=\D)", llm_answer)
            # removes the word dot when its on its own at the end of the string
            instructions = [
                re.sub(r"(?i)\.?\s*\b(dot)$", "", i) for i in instructions if i.strip()
            ]
            instructions = [
                re.sub(r"\s\s+", " ", i).strip() for i in instructions if i.strip()
            ]
            instructions = [
                i for i in instructions if len(i) > 5
            ]  # no tienen sentido instrucciones tan cortas, van a ser errores
            instructions = self.clean_instructions(instructions)

            return instructions
        except Exception as e:
            raise Exception(f"Exception in explainer/parse_llm_answer: {e}")

    def parse_llm_answer_corrected(self, llm_answer_corrected: str, instructions: List):
        try:
            if "[" not in llm_answer_corrected:
                # print("The corrected answer is not a list.")
                return instructions
            instructions = ast.literal_eval(llm_answer_corrected)

            return instructions
        except Exception:
            # print(f"Exception in explainer/parse_llm_answer_corrected: {e}")
            return instructions

    def clean_instructions(self, instructions):
        if "here are the" in instructions[0].lower() and ":" in instructions:
            instructions[0] = instructions[0].split(":", 1)[1].strip()
        if "." in instructions:
            instructions.remove(".")
        return instructions


# import pandas
class RunnerService:
    def try_run(self, code: str, df: pd.DataFrame) -> Any:
        """
        Can return the result (theoretically conserves te python typing)
        """
        local_vars = {"df": df}
        global_vars = {"pd": pd}
        try:
            # code = "import pandas\n"+code
            # code = code.replace("pd","pandas")

            exec(code, global_vars, local_vars)
            result = local_vars.get("result", None)
            if result is None:
                raise Exception("No result was provided in local_vars (exec - runner)")
        except Exception as e:
            raise Exception(f"Exception running code (exec): {e}")
        # print(f"Runner result: {result}")
        return result


class CoderService(ServicePrompting):
    name = "coder"

    def get_prompt(
        self,
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
                    old_code,
                    old_code_error,
                )
            else:
                return self.get("template").format(
                    dataframe_columns,
                    "\n".join(
                        [
                            str(i) + "." + " " + step
                            for i, step in enumerate(list_of_steps, start=1)
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

