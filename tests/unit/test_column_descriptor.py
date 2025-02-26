import itertools
import json
import logging
import math
import os

import pandas as pd
import pytest
from datasets import load_dataset
from dotenv import load_dotenv
from pandas.api.types import is_numeric_dtype

from tqa.coder.controllers.controller import CoderController
from tqa.common.configuration.config import load_config
from tqa.common.configuration.logger import get_logger
from tqa.common.utils import ensure_path, read_json

load_dotenv()
logger = get_logger("tests")
config = load_config()


@pytest.fixture
def tables_descriptions():
    return read_json(ensure_path("tests/assets/table_result.json"))


"""def test_is_openai_key():

    assert os.getenv("OPENAI_API_KEY") is not None


def test_one(tables_descriptions):
    assert os.getenv("OPENAI_API_KEY") is not None

    table_name = "037_Ted"

    # good_result=tables_descriptions.get(table_name)

    df = pd.read_parquet(
        f"hf://datasets/cardiffnlp/databench/data/{table_name}/all.parquet"
    )

    controller = CoderController(use_model="openai")
    result = controller.describe_columns(df, table_name)
    print(result)
    assert result

def test_one_bypass():
    table_name = "037_Ted"
    df = pd.read_parquet(
        f"hf://datasets/cardiffnlp/databench/data/{table_name}/all.parquet"
    )
    controller = CoderController(use_model="bypass")
    result = controller.describe_columns(df, table_name)
    print(result)
    assert result

def test_one_meta(tables_descriptions):

    table_name = "037_Ted"

    # good_result=tables_descriptions.get(table_name)

    df = pd.read_parquet(
        f"hf://datasets/cardiffnlp/databench/data/{table_name}/all.parquet"
    )

    controller = CoderController(use_model="meta")
    result = controller.describe_columns(df, table_name)
    print(result)
    assert result


def test_all_tables():

    assert os.getenv("OPENAI_API_KEY") is not None

    # Read input data
    # Load SemEval 2025 task 8 Question-Answer splits
    semeval_train_qa = load_dataset(
        "cardiffnlp/databench", name="semeval", split="train"
    )
    # semeval_dev_qa = load_dataset("cardiffnlp/databench", name="semeval", split="dev")
    output_file = "table_result.json"

    # A small chache to store analysed datasets
    analysed_datasets = {}

    controller = CoderController(use_model="openai")
    # Do the same for semeval_dev_qa??
    for ds_id in semeval_train_qa["dataset"]:

        print("DS ID", ds_id)

        if ds_id in analysed_datasets:
            continue

        print("Reading table")

        # Reading the table
        df = pd.read_parquet(
            f"hf://datasets/cardiffnlp/databench/data/{ds_id}/all.parquet"
        )

        print("Describing column")

        # in fork
        result = controller.describe_columns(df, ds_id)
        analysed_datasets[ds_id] = result

        with open(output_file, "w+") as f_out:
            f_out.write("{}".format(json.dumps(analysed_datasets, indent=4)))"""

# --------------------------------------------
# WITH GENERIC INFERENCE SERVICES (NO OPENAI)
# --------------------------------------------


def test_one():
    table_name = "037_Ted"
    df = pd.read_parquet(
        f"hf://datasets/cardiffnlp/databench/data/{table_name}/all.parquet"
    )
    controller = CoderController()
    result = controller.describe_columns(df, table_name)
    print(result)
    assert result


def test_all_tables():

    # Read input data
    # Load SemEval 2025 task 8 Question-Answer splits
    semeval_train_qa = load_dataset(
        "cardiffnlp/databench", name="semeval", split="train"
    )

    # A small chache to store analysed datasets
    analysed_datasets = {}

    controller = CoderController()
    # Do the same for semeval_dev_qa??
    for ds_id in semeval_train_qa["dataset"]:

        print("DS ID", ds_id)

        if ds_id in analysed_datasets:
            continue

        print("Reading table")

        # Reading the table
        df = pd.read_parquet(
            f"hf://datasets/cardiffnlp/databench/data/{ds_id}/all.parquet"
        )

        print("Describing column")

        # in fork
        result = controller.describe_columns(df, ds_id)
        analysed_datasets[ds_id] = result
