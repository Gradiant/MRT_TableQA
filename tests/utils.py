from tqa.common.domain.entities.Dataset import Dataset


def get_table_from_dataset(num_table):
    dataset_service = Dataset()
    databench = dataset_service.get_data()
    table_set = databench[num_table]
    dataset_name = table_set["table_name"]
    df = dataset_service.get_tabular_df(dataset_name)
    return df
