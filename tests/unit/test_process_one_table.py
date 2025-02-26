from tqa.coder.controllers.controller import CoderController
from tqa.common.domain.entities.Dataset import Dataset


def test_process_one_table():
    dataset_service = Dataset()
    databench = dataset_service.get_data()
    table_set = databench[4]
    dataset_name = table_set["table_name"]
    question = table_set["questions"][0]["question"]
    df = dataset_service.get_tabular_df(dataset_name)

    print(f"question: {question}")
    print(f"dataset_name: {dataset_name}")

    controller = CoderController()
    result = controller.process_table(df=df, table_name=dataset_name, question=question)

    print(result)
