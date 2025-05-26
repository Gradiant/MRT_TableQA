from typing import Any

import pandas as pd
from thefuzz import fuzz


def flatten_column_values_from_df(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Obtains the value of a column but flattened if they are lists
    It returns the same dataframe with the column provided falttened

     Parameters:
     - df: The pandas DataFrame to filter.
     - column: The name of the column to apply the filter on.

     Returns:
     - The same pandas DataFrame with the column values provided flattened if the values are lists of objects/strings
    (it uses the explode functionality)

    """
    df = df.explode(column)
    return df


def get_top_n_records_with_non_nan_column_value(
    df: pd.DataFrame, column: str, number: int
) -> pd.DataFrame:
    """
    Returns the first 'number' records in a DataFrame where the specified column has non-NaN values.

    Parameters:
    - df: The pandas DataFrame to filter.
    - column: The name of the column to apply the filter on.
    - number: The number of records to return.

    Returns:
    - A pandas DataFrame containing the first 'number' records with non-NaN values in the specified column.
    """
    df_filter = df.dropna(subset=[column])
    return df_filter.head(number)


def get_tail_n_records_with_non_nan_column_value(
    df: pd.DataFrame, column: str, number: int
) -> pd.DataFrame:
    """
    Returns the last 'number' records in a DataFrame where the specified column has non-NaN values.

    Parameters:
    - df: The pandas DataFrame to filter.
    - column: The name of the column to apply the filter on.
    - number: The number of records to return.

    Returns:
    - A pandas DataFrame containing the last 'number' records with non-NaN values in the specified column.
    """
    df_filter = df.dropna(subset=[column])
    return df_filter.tail(number)


def delete_rows_by_column_value(
    df: pd.DataFrame, column: str, value: Any = None
) -> pd.DataFrame:
    """
    Obtains a new dataframe deleting the rows that have a certain value in a column

    Parameters:
    - df: The pandas DataFrame to filter.
    - column: The name of the column to apply the filter on.
    - value: The numeric value to compare against.

    """
    if value is pd.NA or value is pd.NaT:
        return df.dropna(subset=column)

    df_filter = df[df[column] != value]

    if len(df_filter) == len(df):

        df_filter = df_filter[
            ~df_filter[column].astype(str).str.contains("{} ".format(value))
        ]

        return df_filter


def sort_dataframe_column_alphabetical_order(df: pd.DataFrame, column_name: str):
    """
    This function sorts the dataframe based on the specified column in alphabetical order.

    Parameters:
    df (pandas.DataFrame): The dataframe to be sorted.
    column_name (str): The name of the column to sort by.

    Returns:
    pandas.DataFrame: The sorted dataframe.
    """

    df[column_name] = df[column_name].astype(str)

    sorted_df = df.sort_values(by=column_name, ascending=True)
    return sorted_df


def filter_rows_by_column_equals_or_less_than_numeric_value(
    df: pd.DataFrame, column: str, value: Any = None
) -> pd.DataFrame:
    """
    Filters rows in a DataFrame where the specified column's value is equal to or less than the given value.

    Parameters:
    - df: The pandas DataFrame to filter.
    - column: The name of the column to apply the filter on.
    - value: The numeric value to compare against.

    Returns:
    - A pandas DataFrame containing only the rows where the column's value is equal to or less than the specified value.
    """
    import re

    if value is pd.NA or value is pd.NaT:
        return df[df[column].isna()]

    def extract_numeric(val):
        """Extract the first numeric value from a string, if present."""
        if pd.isna(val):
            return None
        match = re.match(r"\d+", str(val))
        return float(match.group()) if match else None

    def is_column_numeric(col):
        return pd.api.types.is_numeric_dtype(col)

    col = df[column]
    if is_column_numeric(col):
        return df[col <= value].copy()

    numeric_values = col.apply(extract_numeric)
    df_filter = df[numeric_values <= value].copy()

    return df_filter


def filter_rows_by_column_strictly_less_than_numeric_value(
    df: pd.DataFrame, column: str, value: Any = None
) -> pd.DataFrame:
    """
    Filters rows in a DataFrame where the specified column's value is strictly less than the given value.

    Parameters:
    - df: The pandas DataFrame to filter.
    - column: The name of the column to apply the filter on.
    - value: The numeric value to compare against.

    Returns:
    - A pandas DataFrame containing only the rows where the column's value is strictly less than the specified value.
    """
    import re

    if value is pd.NA or value is pd.NaT:
        return df[df[column].isna()]

    def extract_numeric(val):
        """Extract the first numeric value from a string, if present."""
        if pd.isna(val):
            return None
        match = re.match(r"\d+", str(val))
        return float(match.group()) if match else None

    def is_column_numeric(col):
        return pd.api.types.is_numeric_dtype(col)

    col = df[column]
    if is_column_numeric(col):
        return df[col < value].copy()

    numeric_values = col.apply(extract_numeric)
    df_filter = df[numeric_values < value].copy()

    return df_filter


def filter_rows_by_column_equals_or_higher_than_numeric_value(
    df: pd.DataFrame, column: str, value: Any = None
) -> pd.DataFrame:
    """
    Filters rows in a DataFrame where the specified column's value is equal to or greater than the given value.

    Parameters:
    - df: The pandas DataFrame to filter.
    - column: The name of the column to apply the filter on.
    - value: The numeric value to compare against.

    Returns:
    - A pandas DataFrame containing only the rows where the column's value is equal to or greater than the specified value.
    """
    import re

    if value is pd.NA or value is pd.NaT:
        return df[df[column].isna()]

    def extract_numeric(val):
        """Extract the first numeric value from a string, if present."""
        if pd.isna(val):
            return None
        match = re.match(r"\d+", str(val))
        return float(match.group()) if match else None

    def is_column_numeric(col):
        return pd.api.types.is_numeric_dtype(col)

    col = df[column]
    if is_column_numeric(col):
        return df[col >= value].copy()

    numeric_values = col.apply(extract_numeric)
    df_filter = df[numeric_values >= value].copy()

    return df_filter


def filter_rows_by_column_strictly_higher_than_numeric_value(
    df: pd.DataFrame, column: str, value: Any = None
) -> pd.DataFrame:
    """
    Filters rows in a DataFrame where the specified column's value is strictly greater than the given value.

    Parameters:
    - df: The pandas DataFrame to filter.
    - column: The name of the column to apply the filter on.
    - value: The numeric value to compare against.

    Returns:
    - A pandas DataFrame containing only the rows where the column's value is strictly greater than the specified value.
    """
    import re

    if value is pd.NA or value is pd.NaT:
        return df[df[column].isna()]

    def extract_numeric(val):
        """Extract the first numeric value from a string, if present."""
        if pd.isna(val):
            return None
        match = re.match(r"\d+", str(val))
        return float(match.group()) if match else None

    def is_column_numeric(col):
        return pd.api.types.is_numeric_dtype(col)

    col = df[column]
    if is_column_numeric(col):
        return df[col > value].copy()

    numeric_values = col.apply(extract_numeric)
    df_filter = df[numeric_values > value].copy()

    return df_filter


def filter_rows_that_contain_column_value(
    df: pd.DataFrame, column: str, value: Any = None
) -> pd.DataFrame:
    """
    Obtains a new dataframe containing the rows that have a certain value in a column

    Parameters:
    - df: The pandas DataFrame
    - column: The name of the column to search
    - value: The value to check in the column

    Returns:
    - a pandas DataFrames containing only the rows that match exactly the value in the given column

    """
    threshold = 75

    def _round_was_useful(original_len: int, result_len: int) -> bool:
        return 0 < result_len < original_len

    def _best_fuzzy_match(
        series: pd.Series, target: str, threshold: int = 90
    ) -> Any | None:
        unique_vals = series.dropna().unique()
        best_val, best_score = None, 0
        for v in unique_vals:
            score = fuzz.ratio(str(v).lower(), target.lower())
            if score > best_score:
                best_val, best_score = v, score
        return best_val if best_score >= threshold else None

    original_len = len(df)

    # ---- round 1: exacto / simple contains ---------------------------------

    if value is pd.NA or value is pd.NaT:
        return df[df[column].isna()]

    else:
        df_filter = df[df[column] == value]

        if _round_was_useful(original_len, len(df_filter)):
            return df_filter

        else:

            df_filter = df.dropna()

            df_filter = df_filter[
                df_filter[column].astype(str).str.contains("{} ".format(value))
            ]

            if _round_was_useful(original_len, len(df_filter)):
                return df_filter

    # ---- round 2: fuzzy ----------------------------------------------------
    if (
        pd.api.types.is_string_dtype(df[column])
        and isinstance(value, str)
        and value != ""
    ):
        best_match = _best_fuzzy_match(df[column], value, threshold)
        if best_match is not None:
            fuzzy = df[df[column] == best_match]
            if _round_was_useful(original_len, len(fuzzy)):
                return fuzzy

    # ---- no funcionó ----
    return df


def filter_rows_that_do_not_contain_column_value(
    df: pd.DataFrame, column: str, value: Any = None
) -> pd.DataFrame:
    """
    Obtains a new dataframe containing the rows that do NOT have a certain value in a column

    Parameters:
    - df: The pandas DataFrame
    - column: The name of the column to search
    - value: The value to check in the column

    Returns:
    - a pandas DataFrames containing only the rows that do not have said value in the given column

    """

    threshold = 75

    def _round_was_useful(original_len: int, result_len: int) -> bool:
        return 0 < result_len < original_len

    def _best_fuzzy_match(
        series: pd.Series, target: str, threshold: int = 90
    ) -> Any | None:
        unique_vals = series.dropna().unique()
        best_val, best_score = None, 0
        for v in unique_vals:
            score = fuzz.ratio(str(v).lower(), target.lower())
            if score > best_score:
                best_val, best_score = v, score
        return best_val if best_score >= threshold else None

    original_len = len(df)

    # ---- round 1: exacto ----------------------------------------------------
    if pd.isna(value):
        exact = df[df[column].notna()]
    else:
        exact = df[df[column] != value]

    if _round_was_useful(original_len, len(exact)):
        return exact

    # ---- round 2: fuzzy ----------------------------------------------------
    if (
        pd.api.types.is_string_dtype(df[column])
        and isinstance(value, str)
        and value != ""
    ):
        best_match = _best_fuzzy_match(df[column], value, threshold)
        if best_match is not None:
            fuzzy = df[df[column] != best_match]
            if _round_was_useful(original_len, len(fuzzy)):
                return fuzzy

    # ---- no funcionó ----
    return df


def exists_value_in_column(df: pd.DataFrame, column: str, value) -> bool:
    """
    Checks if there is at least one occurrence of a specific value in a given column of a DataFrame.

    Parameters:
    - df: The pandas DataFrame.
    - column: The name of the column to search.
    - value: The value to check in the column.

    Returns:
    - True if the value is found at least once in the column, False otherwise.
    """
    if value is pd.NA or value is pd.NaT:
        return df[column].isna().any()

    if (df[column] == value).any():
        return (df[column] == value).any()
    try:
        if (df[column] == df[column].astype(int)).all():
            return (df[column] == int(value)).any()
    except Exception:
        pass

    return (df[column].str.contains("{}".format(value))).any()


def count_elements_equal_to_value_in_column(
    df: pd.DataFrame, column: str, value: Any = None
) -> int:
    """
    Counts the number of occurrences of a specific value within a given column of a DataFrame.

    Parameters:
    - df: The pandas DataFrame.
    - column: The name of the column to search.
    - value: The value to count in the column.

    Returns:
    - An integer representing the number of times the value appears in the column.
    """

    # Maybe the system is trying to filter with value in a 1-column df
    if isinstance(df, pd.Series):
        return (df == column).sum()

    return (df[column] == value).sum()


def count_elements_containing_value_in_column(
    df: pd.DataFrame, column: str, value: Any = None
) -> int:
    """
    Counts the number of occurrences in cells at least containing the value within a given column of a DataFrame.

    Parameters:
    - df: The pandas DataFrame.
    - column: The name of the column to search.
    - value: The value to count in the column.

    Returns:
    - An integer representing the number of times the value appears in the column.
    """
    if isinstance(df, pd.Series):
        return (df.str.contains(value)).sum()

    return (df[column].str.contains(value)).sum()


def find_n_most_frequent_elements_in_column_subset(
    df: pd.DataFrame, target_column: str, subset_column: str, filter_value, n: int
) -> list:
    """
    Identifies the 'n' most frequently occurring elements within a specified column
    of a DataFrame, considering only the subset of rows where another column equals a given value.

    Parameters:
    - df: The pandas DataFrame.
    - target_column: The column in which to find the most frequent elements (e.g., 'age').
    - subset_column: The column used to define the subset (e.g., 'gender').
    - filter_value: The value to filter the subset column by (e.g., 'male').
    - n: The number of top frequent elements to return.

    Returns:
    - A list containing the 'n' most frequent elements found in the target column for the specified subset.
    """
    subset_df = df[df[subset_column] == filter_value]
    return subset_df[target_column].value_counts().head(n).index.tolist()


def find_most_frequent_element_in_column_subset(
    df: pd.DataFrame, target_column: str, subset_column: str, filter_condition
):
    """
    Identifies the most frequently occurring element within a specified column of a DataFrame,
    considering only the subset of rows defined by a condition on another column.

    The filter_condition parameter can be:
      - A callable that takes a value from the subset column and returns True/False.
      - A string such as "less than 40" or "greater than 30" to apply a comparison.
      - Or any other value for equality filtering.

    Parameters:
    - df: The pandas DataFrame.
    - target_column: The column to determine the most frequent element (e.g., 'satisfaction_level').
    - subset_column: The column on which to base the filtering (e.g., 'age').
    - filter_condition: The condition (or value) used to filter the subset column.

    Returns:
    - The most frequent element in the target column for the filtered subset. Returns None if the subset is empty.
    """
    # Determine the subset based on the type of filter_condition.
    if callable(filter_condition):
        subset_df = df[df[subset_column].apply(filter_condition)]
    elif isinstance(filter_condition, str):
        cond = filter_condition.lower().strip()
        if cond.startswith("less than"):
            try:
                threshold = float(cond.replace("less than", "").strip())
                subset_df = df[df[subset_column] < threshold]
            except ValueError:
                subset_df = df[df[subset_column] == filter_condition]
        elif cond.startswith("greater than"):
            try:
                threshold = float(cond.replace("greater than", "").strip())
                subset_df = df[df[subset_column] > threshold]
            except ValueError:
                subset_df = df[df[subset_column] == filter_condition]
        else:
            subset_df = df[df[subset_column] == filter_condition]
    else:
        subset_df = df[df[subset_column] == filter_condition]

    if subset_df.empty:
        return None
    return subset_df[target_column].value_counts().idxmax()


def find_most_frequent_element_in_column(df: pd.DataFrame, column: str = None):
    """
    Identifies the most frequently occurring element within a specified column of a DataFrame.

    Parameters:
    - df: The pandas DataFrame.
    - column: The name of the column to search.

    Returns:
    - The element that appears most often in the column.
    """

    if column is None and len(df.columns) == 1:
        return df[df.columns[0]].value_counts().idxmax()

    else:
        return df[column].value_counts().idxmax()


def find_n_most_frequent_elements_in_column(
    df: pd.DataFrame, column: str, n: int
) -> list:
    """
    Identifies the 'n' most frequently occurring elements within a specified column of a DataFrame.

    Parameters:
    - df: The pandas DataFrame.
    - column: The name of the column to analyze.
    - n: The number of top frequent elements to return.

    Returns:
    - A list containing the 'n' most frequent elements found in the column.
    """
    return df[column].value_counts().head(n).index.tolist()
