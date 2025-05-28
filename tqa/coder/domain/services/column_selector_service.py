import ast
import re
from typing import Dict

from thefuzz import fuzz

from tqa.common.configuration.logger import get_logger
from tqa.common.domain.services.Service import Service

logger = get_logger("column_selector")


class ColumnSelectorService(Service):
    name = "column_selector"

    def chunk_list_columns(self, data):
        chunk_size = self.service_config.get("size_chunks_columns_in_prompt", 25)

        for i in range(0, len(data), chunk_size):
            # Yield slices of the list
            yield data[i:(i + chunk_size)]  # fmt: skip

    def _get_prompts(self, columns_descriptions, df, question) -> Dict:

        system_template = self.service_config.get("template", {}).get("system")

        column_info = self.get_column_info(columns_descriptions)

        user_template = (
            self.service_config.get("template", {})
            .get("user")
            .format(question, column_info)
        )

        return system_template, user_template

    def get_column_info(self, columns_descriptions):
        info = ""
        for col in columns_descriptions:
            info += (
                "name: "
                + col.get("name")
                + " || description: "
                + col.get("description").get("description")
                + "\n"
            )

        return info

    def filter_columns(self, df, columns_descriptions, columns_useful):

        if not columns_useful:
            return columns_descriptions, df

        new_columns_descriptions = []
        for column in columns_descriptions.get("columns"):
            if column.get("name") in columns_useful:
                new_columns_descriptions.append(column)

        # columns_descriptions["original_columns"] = copy.deepcopy(
        #   columns_descriptions["columns"]
        #
        columns_descriptions["columns"] = new_columns_descriptions

        columns_useful_df = [col for col in columns_useful if col in list(df.columns)]
        df = df[columns_useful_df]

        return columns_descriptions, df

    def parse_columnlist(self, columns_string):

        # parse common missformat (i.e.: [name: col1, name: col2])
        if columns_string.startswith("[name: "):
            columns_string = columns_string.replace("[name: ", "['")
            columns_string = columns_string.replace(", name: ", "', '")
            if columns_string[-1] == "]" and columns_string[-2] != "'":
                columns_string = columns_string[:-1] + "']"

        # escape intermediate single quotes
        pattern = r"(?<![a-zA-Z0-9])'[^']{1,2}'(?!,|\w|\]|[^']')"
        columns_string = re.sub(
            pattern, lambda m: m.group(0).replace("'", r"\'"), columns_string
        )

        match = re.search(r"\[.*\]", columns_string)
        if match:
            list_str = match.group(0)  # Extracted list as a string
            lst = ast.literal_eval(list_str)  # Safely evaluate it to a list
            print(lst)  # Output: ['one', 'two', 'three']
            return lst
        else:
            print("No list found in the string")
            return []

    def filter_valid_columns(self, column_list, df):
        column_list_filtered = []
        black_list = self.service_config.get("filter_blacklist", {})

        for column in column_list:

            if column not in list(df.columns):
                self.logger.error(
                    "Selector found a column that not exists: {} ".format(str(column))
                )
                continue

            if any([column.startswith(term) for term in black_list]):
                continue

            values = list(set(df[column]))
            if values == ["N.P."]:
                continue
            # if values == ['N.P.', 'No menciona', 'Menciona']: # becareful, order
            #    continue

            column_list_filtered.append(column)

        return column_list_filtered

    def check_too_much_columns(self, column_list):

        if len(column_list) < 20:
            return column_list

        new_column_list = []
        for column in column_list:
            if column[-1].isdigit() and column[-2] == "_":
                continue

            new_column_list.append(column)

        new_column_list = self.remove_similar_long_strings(new_column_list)

        # ÑAPA
        if len(new_column_list) > 30:
            new_column_list = new_column_list[0:30]

        if len(new_column_list) < len(column_list):
            logger.info(
                "Removing number of columns. From {} to {}".format(
                    len(column_list), len(new_column_list)
                )
            )

        return new_column_list

    def remove_similar_long_strings(self, strings, threshold=90):
        long_strings = [s for s in strings if len(s) > 14]  # 14 arbitrary.
        short_strings = [s for s in strings if len(s) <= 14]

        to_remove = set()

        for i in range(len(long_strings)):
            for j in range(i + 1, len(long_strings)):
                if fuzz.ratio(long_strings[i], long_strings[j]) > threshold:
                    to_remove.add(long_strings[i])
                    to_remove.add(long_strings[j])

        filtered_long_strings = [s for s in long_strings if s not in to_remove]
        return short_strings + filtered_long_strings
