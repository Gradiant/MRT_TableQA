from tqa.common.domain.entities.Dataset import Dataset


def test_get_data():
    dataset_service = Dataset()

    databench = dataset_service.get_data()

    table_set = databench[4]

    margin = "-" * 20
    print(margin)
    print(
        "Table Set:\nTable: {}\nColumns: {}\nAmount of questions: {}".format(
            table_set["table_name"], table_set["columns"], len(table_set["questions"])
        )
    )

    questions = table_set["questions"]
    print("Example: {}".format(questions[0]))
    print(margin)


def test_get_tabular_df():
    dataset_service = Dataset()
    databench = dataset_service.get_data()
    table_set = databench[6]
    dataset_name = table_set["table_name"]
    df = dataset_service.get_tabular_df(dataset_name)
    print(df)
    print(len(df))
