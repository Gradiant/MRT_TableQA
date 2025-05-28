import ast
import locale
import os
import re
from typing import Any, Dict, List, Union

import pandas as pd
from langchain_core.output_parsers import JsonOutputParser
from pandas.api.types import is_numeric_dtype
from thefuzz import process

from tqa.coder.domain.services import coder_internal_functions
from tqa.common.configuration.logger import get_logger
from tqa.common.domain.services.Service import Service
from tqa.common.utils import ensure_path, read_jsonl

logger = get_logger("service")


def add_subindex(text, index, list_names):

    for i in range(1000):
        new_text = text + "_" + str(index)
        if new_text in list_names:
            new_text = add_subindex(text, index + 1, list_names)
            return new_text
        else:
            return new_text

    return new_text


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

    def format(self, result: str | float | int | list | dict):
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
        elif isinstance(result, tuple):
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
            if all(True if i == f else False for i, f in zip(_list_ints, _list_nums)):
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
            elif "." in num_str and "," not in num_str:
                num_str = float(num_str)
            else:
                num_str = float(num_str)
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

        if str(llm_response).lower() in [
            "boolean",
            "string",
            "number",
            "list of string",
            "list of numbers",
        ]:
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
        self.use_simple_names = self.config.get("use_simplified_column_names", False)

    def get_prompt(
        self,
        question: str,
        column_names: List[str],
        column_descriptions: List[dict],
        max_steps: int,
        max_categories_for_describe: int = 4,
        table_name: str = None,
        max_columns: int = 10,
    ) -> str:
        try:
            columns_section = self.get_columns_prompt(
                column_names, column_descriptions, max_categories_for_describe
            )
            table_name_section = self.get_table_name_section(table_name)
            return self.template_explainer.format(
                table_name_section,
                columns_section,
                question,
                max_steps,
                column_names[:max_columns].to_string(),
            )
        except Exception as e:
            raise Exception(f"Exception in explainer/get_prompt: {e}")

    def _get_closest_cell_value(
        self, cell_value: Any, df: pd.DataFrame, threshold: int = 40
    ):

        all_unique_values = pd.melt(df).value.unique()
        value_selection = process.extractOne(cell_value, all_unique_values)
        value = value_selection[0] if value_selection[1] > threshold else None

        return value

    def _filter_columns_by_value(self, df: pd.DataFrame, column: str):
        """Filter string cells by column value

        df: a pandas Dataframe
        column : a name of column in the pandas dataframe
        """

        if column not in df.columns:
            # try something to find the most similar column
            column_selection = process.extractOne(column, df.columns)
            column = column_selection[0]
            print("Column", column)

        return column

    def _add_reinforce_instructions(self, instruction_list: List, new_value):
        new_instruction = f"One of the values to use in the filters is '{new_value}' "

        instruction_list.append(new_instruction)

        return instruction_list

    def _add_clarification_instructions(
        self, instruction_list: List, old_value: str, new_value: str
    ):

        new_instruction = f"Be careful!. The value {old_value} appears in the database with the following format: '{new_value}' "

        instruction_list.append(new_instruction)

        return instruction_list

    def _replace_instructions(
        self, instruction_list: List, old_value: str, new_value: str
    ):

        new_instruction_list = []

        for idx in range(len(instruction_list)):

            _inst = instruction_list[idx]

            if old_value in _inst and new_value not in _inst:
                _inst = _inst.replace(old_value, new_value)

            new_instruction_list.append(_inst)

        return new_instruction_list

    def apply_fuzzy_correction(self, json_result: Dict, df: pd.DataFrame):
        """Apply fuzzy correction"""

        # Correct columns
        if isinstance(json_result, dict) and "columns" in json_result:
            column_list = json_result["columns"]

            new_column_list = []
            for _column in column_list:
                new_column = self._filter_columns_by_value(df, _column)
                new_column_list.append(new_column)

                if new_column != _column:
                    logger.info(f"Modify Column {_column} -> {new_column}")
                    # modify instructions
                    if "instructions" in json_result:
                        json_result["instructions"] = self._replace_instructions(
                            json_result["instructions"], _column, new_column
                        )
            json_result["columns"] = new_column_list

            # Correct values (only if there are filtering columns)
            if isinstance(json_result, dict) and "filter_values" in json_result:

                for _value in json_result["filter_values"]:

                    if isinstance(_value, str):
                        df_filter = df[json_result["columns"]]

                        new_value = self._get_closest_cell_value(_value, df_filter)
                        if new_value is None:
                            new_value = _value

                    else:
                        new_value = _value

                    if new_value != _value:
                        logger.info(f"Modify Cell {_value} -> {new_value}")

                        # modify instructions
                        if "instructions" in json_result:
                            json_result[
                                "instructions"
                            ] = self._add_clarification_instructions(
                                json_result["instructions"], _value, new_value
                            )

                    else:
                        # Modify instructions to add filter values
                        if "instructions" in json_result:
                            json_result[
                                "instructions"
                            ] = self._add_reinforce_instructions(
                                json_result["instructions"], new_value
                            )

                logger.info("Updating cells")

        return json_result

    def add_column_information_to_instructions(
        self, json_result: Dict, column_description: List[Dict], table_name: str
    ):

        if (
            isinstance(json_result, dict)
            and "columns" in json_result
            and column_description is not None
            and "instructions" in json_result
        ):

            column_list = json_result["columns"]

            for _column in column_list:
                for _desc_column in column_description.get("columns"):
                    if _column == _desc_column["name"]:
                        _type = _desc_column["type"]

                        values = _desc_column["freq_values"]

                        if values is not None:

                            values = [f"{_value}" for _value in values]
                            joint_values = ", ".join(values)

                            new_instruction = f"""The column '{_column}' is of type '{_type}'
 and has the following example values: {joint_values} """
                        else:
                            new_instruction = (
                                f"The column '{_column}' is of type '{_type}'"
                            )

                        logger.info(f"Adding new instruction {new_instruction}")

                        json_result["instructions"].append(new_instruction)
                        break

        return json_result

    def get_prompt_correction(
        self,
        current_prompt: List,
        question: str,
        column_names: List[str],
        column_descriptions: List[dict],
        max_categories_for_describe: int = 4,
        table_name: str = None,
        max_columns: int = 10,
    ) -> str:

        try:
            columns_section = self.get_columns_prompt(
                column_names, column_descriptions, max_categories_for_describe
            )
            logger.info("Explainer Correction prompt")

            table_name_section = self.get_table_name_section(table_name)
            return self.template_correction.format(
                table_name_section,
                columns_section,
                question,
                str(current_prompt),
                column_names[:max_columns].to_string(),
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
            simple_names_used = []
            for column in column_descriptions.get("columns"):
                options = column.get("freq_values", [])
                example_values = column.get("example_values", [])
                unique_values = column.get("unique", 1000)
                description = column.get("description").get("description")
                simple_name = column.get("description").get("simple_name")

                if (
                    self.use_simple_names
                    and simple_name
                    and simple_name not in simple_names_used
                ):
                    name = simple_name
                    simple_names_used.append(name)
                elif (
                    self.use_simple_names
                    and simple_name
                    and simple_name in simple_names_used
                ):
                    # avoid repeated names of columns
                    name = add_subindex(simple_name, 1, simple_names_used)
                    simple_names_used.append(name)
                else:
                    name = column.get("name")
                    if simple_name in simple_names_used:
                        self.logger.debug(
                            "Name of simple name already in use: " + str(simple_name)
                        )

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
                elif type_data == "category" and example_values:
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

    def parse_llm_json_answer(self, llm_answer: str):

        logger.info(f"To parse: content Explainer {llm_answer}")
        parser = JsonOutputParser()
        next_content = parser.parse(llm_answer)
        logger.info(f"Parsed content Explainer {next_content}")

        return next_content

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


class RunnerService(Service):
    initial_global_vars = {"pd": pd}

    def __init__(self, **kargs):
        super().__init__(**kargs)
        self.use_simple_names = self.config.get("use_simplified_column_names", False)

    def _get_internal_functions(self):
        global_vars = {}
        for name, value in vars(coder_internal_functions).items():
            if name.startswith("_") or not callable(value):
                continue
            global_vars[name] = getattr(coder_internal_functions, name)
        import re

        global_vars["re"] = re
        return dict(self.initial_global_vars, **global_vars)

    def simplify_column_names(
        self, df: pd.DataFrame, column_descriptions: dict
    ) -> pd.DataFrame:
        if not self.use_simple_names or not column_descriptions:
            return df

        simple_names_used = []
        for column in column_descriptions.get("columns"):
            simple_name = column.get("description").get("simple_name")
            original_name = column.get("name")

            if (
                self.use_simple_names
                and simple_name
                and simple_name not in simple_names_used
            ):
                simple_names_used.append(simple_name)
            elif (
                self.use_simple_names
                and simple_name
                and simple_name in simple_names_used
            ):
                # avoid repeated names of columns. Same transformation than in explainer
                simple_name = add_subindex(simple_name, 1, simple_names_used)
                simple_names_used.append(simple_name)

            if simple_name and original_name in df.columns:
                df.rename(columns={original_name: simple_name}, inplace=True)

        return df

    def try_run(
        self,
        code: str,
        df: pd.DataFrame,
    ) -> Any:
        """
        Can return the result (theoretically conserves te python typing)
        """
        local_vars = {"df": df}
        global_vars = self._get_internal_functions()
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
