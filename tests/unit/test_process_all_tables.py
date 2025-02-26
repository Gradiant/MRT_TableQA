# from tqa.common.domain.entities.Dataset import Dataset
from tqa.coder.controllers.controller import CoderController

# dataset_service = Dataset()
# databench = dataset_service.get_data()
# table_set = databench[4]
# dataset_name = table_set["table_name"]
# question = table_set["questions"][0]["question"]
# df = dataset_service.get_tabular_df(dataset_name)

# print(f"question: {question}")
# print(f"dataset_name: {dataset_name}")


def test_process_all_tables():
    controller = CoderController()
    result = controller.process_all_tables(result_path="./")

    print(result)
