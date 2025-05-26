import pandas as pd

from tqa.common.configuration.logger import get_logger
from tqa.common.domain.entities.Dataset import Dataset

logger = get_logger("tests")


def test_get_data():
    dataset_service = Dataset()

    _ = dataset_service.get_data()


"""    table_set = databench[4]

    assert table_set["table_name"], "No table_name in table set"
    assert table_set["columns"], "No columns in table set"
    assert table_set["questions"], "No questions in table set"

    logger.info(
        "Table Set:\nTable: {}\nColumns: {}\nAmount of questions: {}".format(
            table_set["table_name"], table_set["columns"], len(table_set["questions"])
        )
    )

    questions = table_set["questions"]
    logger.info("Example: {}".format(questions[0]))"""


def test_get_tabular_df():
    dataset_service = Dataset()
    databench = dataset_service.get_data()
    assert databench, "No databench"
    print(len(databench))
    table_set = databench[2]
    dataset_name = table_set["table_name"]
    df = dataset_service.get_tabular_df(dataset_name)
    assert isinstance(df, pd.DataFrame), f"there is no df for {dataset_name}"


def test_analize_dataset():
    dataset_service = Dataset()
    databench = dataset_service.get_data()
    logger.info(f"Num. tables: {len(databench)}")
    table_names = [table.get("table_name") for table in databench]
    logger.info(f"Tables names: {table_names}")
    questions = [question for table in databench for question in table.get("questions")]
    logger.info(f"Num. questions: {len(questions)}")
    columns_per_table = {
        table.get("table_name"): table.get("columns") for table in databench
    }
    logger.info(
        f"Num. columns: {len([colum for k,item in columns_per_table.items() for colum in item] )}"
    )
