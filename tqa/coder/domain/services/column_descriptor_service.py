import itertools
import json
import logging
import math
import os
from collections import deque
from json.decoder import JSONDecodeError
from typing import Dict, List

import pandas as pd
from datasets import load_dataset
from joblib import Parallel, delayed
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pandas.api.types import is_numeric_dtype

from tqa.common.domain.services.Service import Service


def sliding_window_combinations(lst, window_size):
    """Generate combinations as a rolling window over a list."""
    if window_size > len(lst):
        return  # No combinations possible if window is larger than list length

    queue = deque(lst[:window_size])  # Initialize deque with first window
    yield tuple(queue)  # Yield the first window

    for item in lst[window_size:]:
        queue.popleft()  # Remove the leftmost element
        queue.append(item)  # Add the next element in the sequence
        yield tuple(queue)  # Yield the new window as a combination


# Function to check if a subset is one-hot encoded
def _check_one_hot_subset(df, subset):
    # Compute the row-wise sum for the subset and check the condition
    if (df[list(subset)].sum(axis=1) <= 1).all():
        return subset
    return None


class ColumnDescriptorService(Service):
    name = "column_descriptor"

    def _serialize_dataframe(
        self, df, row_max: int = 10, col_max: int = 20, max_characters: int = 40
    ):

        serialization_list = []

        column_list = df.columns
        col_iterations = math.ceil((1.0 * len(column_list)) / col_max)

        for _it in range(col_iterations):
            it_column_list = column_list[
                (_it * col_max) : min((col_max) * (_it + 1), len(column_list))
            ]

            table_snippet = ""

            for index, row in df.iterrows():
                row_text = f"Row {index}: "
                for it_col, _col in enumerate(it_column_list):
                    if it_col != 0:
                        row_text += ", "

                    if (
                        not is_numeric_dtype(df[_col].dtype)
                        and len(str(row[_col])) > max_characters
                    ):
                        row_text += f'"{_col}" is {str(row[_col])[:max_characters].replace("{","").replace("}","")}...'
                    else:
                        row_text += f'"{_col}" is {str(row[_col]).replace("{","").replace("}","")}'

                table_snippet += f"{row_text}\n"

            serialization_list.append(
                {"it_columns": list(it_column_list), "table": table_snippet}
            )

        return serialization_list

    # Main function to identify suspected one-hot sets
    def _identify_one_hot_sets(self, df, binary_columns, max_columns=150):
        suspected_one_hot_sets = []

        # Limit columns to improve performance if exceeding max_columns
        if len(binary_columns) <= max_columns:
            for group_size in range(2, len(binary_columns) + 1):
                # subsets = itertools.combinations(binary_columns, group_size)

                subsets = [
                    sub
                    for sub in sliding_window_combinations(binary_columns, group_size)
                ]

                # print("Subsets ", subsets)

                # Parallel processing to speed up execution
                results = Parallel(n_jobs=-1)(
                    delayed(_check_one_hot_subset)(df, subset) for subset in subsets
                )

                # Filter out None results and append valid subsets
                suspected_one_hot_sets.extend([res for res in results if res])

        return suspected_one_hot_sets

    def _get_binary_subsets(self, df):

        # Identify binary columns
        binary_columns = [
            col for col in df.columns if df[col].isin([0, 1, math.nan]).all()
        ]

        # Ensuring that columns are binary
        binary_columns = [
            col for col in binary_columns if pd.api.types.is_numeric_dtype(df[col])
        ]

        # print("Binary columns ", len(binary_columns))

        # Identify binary suspects
        # suspected_one_hot_sets = []

        # This process is slow. That is the reason it is limited to 25 columns
        # if len(binary_columns) < 25:
        #    for group_size in range(2, len(binary_columns) + 1):
        #        for subset in itertools.combinations(binary_columns, group_size):

        #            if (df[list(subset)].sum(axis=1) <= 1).all():
        #                suspected_one_hot_sets.append(subset)

        suspected_one_hot_sets = self._identify_one_hot_sets(df, binary_columns)

        print("Suspected one hot ", len(suspected_one_hot_sets))

        return suspected_one_hot_sets

    def _analyze_dataframe(self, df):

        _num_freq_values = self.freq_values

        binary_subsets = self._get_binary_subsets(df)

        table_info = {
            "table": {"len": len(df.index)},
            "columns": [],
            "binary_subsets": binary_subsets,
        }

        for _column in df.columns:
            _name = _column
            _type = str(df[_column].dtype)
            _per_nas = df[_column].isna().sum()

            try:
                _num_unique_values = len(df[_column].unique())

            except TypeError:
                _num_unique_values = None

            _is_binary = df[_column].isin([0, 1]).all()

            if is_numeric_dtype(df[_column].dtype):
                _mean = df[_column].mean()
                _std = df[_column].std()
                _min = df[_column].min()
                _max = df[_column].max()

                most_freq_values = None

            else:
                _mean = 0.0
                _std = 0.0
                _min = 0.0
                _max = 0.0

                # FIXME: move 1000 to configuration
                if _num_unique_values is not None and _num_unique_values < 1000:

                    # FIXME: move the "5" to configuration
                    most_freq_values = [
                        str(_obj)
                        for _obj in df[_column]
                        .value_counts()[:_num_freq_values]
                        .index.tolist()
                    ]

                else:
                    most_freq_values = None

            table_info["columns"].append(
                {
                    "name": _name,
                    "type": _type,
                    "missing_values": int(_per_nas),
                    "unique": _num_unique_values,
                    "flag_binary": bool(_is_binary),
                    "mean": float(_mean),
                    "std": float(_std),
                    "min": float(_min),
                    "max": float(_max),
                    "freq_values": most_freq_values,
                }
            )

        return table_info

    def _get_prompts(self, sel_col_list: list, table) -> Dict:
        system_template = (
            self.service_config.get("template", {})
            .get("system")
            .format("name", "description")
        )

        user_template = (
            self.service_config.get("template", {})
            .get("user")
            .format(sel_col_list, table)
        )

        return system_template, user_template

    def get_serialization_list(self, df: pd.DataFrame) -> Dict:

        max_cols = self.service_config.get("max_col_serialization", 20)

        reference_df = df[~df.isnull().any(axis=1)]
        serialization_list = self._serialize_dataframe(
            reference_df.head(5), col_max=max_cols
        )
        return serialization_list

    def get_column_descriptions_from_cache(self):
        path_to_descriptions = self.service_config.get(
            "path_cache_descriptions", ""
        )  # "tests/assets/table_result.json"

        directory_path = os.path.dirname(path_to_descriptions)
        if not os.path.exists(directory_path):
            # Create the directory
            os.makedirs(directory_path)

        if os.path.exists(path_to_descriptions):
            with open(path_to_descriptions, "r") as file:
                data = json.load(file)
        else:
            data = {}

        return data

    def get_table_descriptions(self, data, table_name):

        columns = data.get(table_name, {})  # .get("columns")

        return columns

    def save_descriptions(self, data):
        path_to_descriptions = self.service_config.get("path_cache_descriptions", "")
        if path_to_descriptions:
            with open(path_to_descriptions, "w") as outfile:
                json.dump(data, outfile)
