import os
import re
import requests
import zipfile

import pandas as pd
from datasets import load_dataset

from tqa.common.configuration.config import load_config

CONFIG = load_config()

class Dataset:

    databench_split = CONFIG.get("databench_split")
    databench_path = CONFIG.get("databench_path").format(CONFIG.get("databench_split"))
    data_url_base = CONFIG.get("data_url_base")
    tabular_data_storage = CONFIG.get("tabular_data_storage_path").format(CONFIG.get("databench_split"))
    test_data_url = CONFIG.get("test_data_url")
    load_dataset_route = CONFIG.get("load_dataset_route")
    load_dataset_name = CONFIG.get("load_dataset_name")

    def __init__(self, storage_folder=tabular_data_storage):
        self.storage_folder = storage_folder
        self.databench_df = None
        self.load_databench()
        self.ensure_datasets_downloaded()

    def load_databench(self):

        if not os.path.isfile(self.databench_path):
            os.makedirs(os.path.split(self.databench_path)[0], exist_ok=True)
            if self.databench_split == "test":
                qa_pairs = pd.read_csv(self.test_data_url.format("test_qa.csv"))
                qa_pairs.to_csv(self.databench_path, index= False)
            else:
                qa_pairs = load_dataset(
                    self.load_dataset_route, name=self.load_dataset_name, split=self.databench_split
                )
                qa_pairs.to_csv(self.databench_path)
        self.databench_df = pd.read_csv(self.databench_path, low_memory=False)

    def ensure_datasets_downloaded(self):

        os.makedirs(self.storage_folder, exist_ok=True)

        datasets = self.databench_df["dataset"].unique()
        for dataset_name in datasets:
            dataset_path = os.path.join(self.storage_folder, f"{dataset_name}.csv")
            if not os.path.isfile(dataset_path):
                self.download_dataset(dataset_name)
                dataset_loaded = "Downloading " + dataset_name
                print(dataset_loaded, end="\r")
        # print(f"{'-'*40}\nTabular Dataset: OK\n{'-'*40}")

    def download_dataset(self, dataset_name):
        if self.databench_split == "test":
            dataset_url = self.test_data_url.format(dataset_name) + "/all.parquet"
        else:
            dataset_url = self.data_url_base.format(dataset_name)
        dataset_path = os.path.join(self.storage_folder, f"{dataset_name}.csv")
        dataset_df = pd.read_parquet(dataset_url)
        dataset_df.to_csv(dataset_path, index=False)

    def get_data(self, name=None):

        data = []

        for dataset_name in self.databench_df["dataset"].unique():
            dataset_path = os.path.join(self.storage_folder, f"{dataset_name}.csv")
            if not os.path.isfile(dataset_path):
                self.download_dataset(dataset_name)
            dataset = pd.read_csv(dataset_path, low_memory=False)
            dataset = self.clean_column_names(dataset)
            filtered = self.databench_df[self.databench_df["dataset"] == dataset_name]
            if self.databench_split == "test":
                fields = ["question"]
            else:
                fields = ["question", "answer", "type"]
            if name:
                if name == dataset_name:
                    return {
                        "table_name": dataset_name,
                        "columns": list(dataset.columns),
                        "questions": list(filtered[fields].to_dict("index").values()),
                    }

            data.append(
                {
                    "table_name": dataset_name,
                    "columns": list(dataset.columns),
                    "questions": list(filtered[fields].to_dict("index").values()),
                }
            )

        return data

    def get_tabular_df(self, dataset_name):
        dataset_path = os.path.join(self.storage_folder, f"{dataset_name}.csv")
        df = pd.read_csv(dataset_path, low_memory=False)
        return df

    def clean_column_names(self, df):

        columns = list(df.columns)
        new_columns = []
        debug_replace = False
        for column in columns:
            original_column = column
            # For names like Age<gx:number>
            column = re.sub(r"(<gx:.*>)", "", column).strip()
            column = self.remove_emojis(column).strip()

            if debug_replace and original_column != column:
                print(
                    "*REPLACE COLUMN: " + original_column + "\t\t --> \t" + str(column)
                )

            new_columns.append(column)

        df.columns = new_columns
        return df

    def remove_emojis(self, data):
        emoj = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002500-\U00002BEF"  # chinese char
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"  # dingbats
            "\u3030"
            "]+",
            re.UNICODE,
        )
        return re.sub(emoj, "", data)

    def format_data_for_batch_exec(self, tables_set):
        tables_info = []
        question_id = 0
        # p_bar_tables = tqdm(tables_set)
        for table_set in tables_set:
            questions = []
            df = self.get_tabular_df(table_set.get("table_name"))
            for question in table_set.get("questions"):
                question_info = {
                    "question_id": question_id,
                    "question": question.get("question"),
                    "answer": question.get("answer"),
                    "type": question.get("type"),
                    "explainer": None,
                    "coder": None,
                    "result": None,
                }
                questions.append(question_info)
                question_id += 1
            tables_info.append(
                {
                    "table_name": table_set.get("table_name"),
                    "df": df,
                    "descriptions": [],
                    "columns": table_set.get("columns"),
                    "questions": questions,
                }
            )

        return tables_info
