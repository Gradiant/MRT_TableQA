import os
import re
import requests
import zipfile

import pandas as pd
from datasets import load_dataset

from tqa.common.configuration.config import load_config

def get_databench_split():
    config = load_config()
    return config["databench_split"]

def get_databench_path():
    config = load_config()
    databench_split = config["databench_split"]
    databench_path = config["databench_path"]
    return databench_path.format(databench_split)

def get_tabular_data_url():
    config = load_config()
    return config["data_url_base"]

def get_tabular_data_storage():
    config = load_config()
    tabular_data_storage_path = config["tabular_data_storage_path"]
    databench_split = config["databench_split"]
    return tabular_data_storage_path.format(databench_split)

def get_test_data_url():
    config = load_config()
    return config["test_data_url"]

databench_split = get_databench_split()
databench_path = get_databench_path()
data_url_base = get_tabular_data_url()
tabular_data_storage = get_tabular_data_storage()
test_data_url = get_test_data_url()


class Dataset:
    def __init__(self, storage_folder=tabular_data_storage):
        self.storage_folder = storage_folder
        self.databench_df = None
        self.load_databench()
        self.ensure_datasets_downloaded()

    def load_databench(self):
        # print(f"{'-'*40}\nChecking Databench QA Pairs Existence\n{'-'*40}")
        # print(f"{'-'*40}\nDataset Split: {databench_split}\n{'-'*40}")
        if not os.path.isfile(databench_path):
            os.makedirs(os.path.split(databench_path)[0], exist_ok=True)
            if databench_split == "test":
                qa_pairs = pd.read_csv(test_data_url.format("test_qa.csv"))
                qa_pairs.to_csv(databench_path, index= False)
            else:
                qa_pairs = load_dataset(
                    "cardiffnlp/databench", name="semeval", split=databench_split
                )
                qa_pairs.to_csv(databench_path)
        self.databench_df = pd.read_csv(databench_path, low_memory=False)

    def ensure_datasets_downloaded(self):
        # print(f"{'-'*40}\nChecking Tabular Dataset Existence\n{'-'*40}")
        # print(f"{'-'*40}\nDataset Split: {databench_split}\n{'-'*40}")
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
        if databench_split == "test":
            dataset_url = test_data_url.format(dataset_name) + "/all.parquet"
        else:
            dataset_url = data_url_base.format(dataset_name)
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
            if databench_split == "test":
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
