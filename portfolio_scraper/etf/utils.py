import pandas as pd
from typing import TypedDict, Optional, Callable


class CsvSettings(TypedDict):
    separator: str
    thousands: str
    decimal: str


class ColumnProcessing(TypedDict):
    formatter: Optional[Callable[[pd.Series], pd.Series]]


def rename_pandas_columns(
    df: pd.DataFrame,
    columns_mapping: dict[str, str],
    keep_unmapped: bool = False,
    reverse_mapping: bool = False,
) -> pd.DataFrame:
    """
    Rename columns in a pandas DataFrame based on a provided mapping.

    Parameters:
    - df: The input DataFrame whose columns need to be renamed.
    - columns_mapping: A dictionary where keys are the current column names and values are the new column names.
    - keep_unmapped: If True, keeps columns that are not in the mapping; if False, drops them.
    - reverse_mapping: If True, reverses the mapping before applying it.

    Returns:
    - A new DataFrame with renamed columns.
    """
    if reverse_mapping:
        columns_mapping = {v: k for k, v in columns_mapping.items()}

    # If keep_unmapped is False, drop columns that are not in the mapping
    if not keep_unmapped:
        df = df[list(columns_mapping.keys())]  # Keep only the useful columns

    # Rename columns based on the provided mapping
    df = df.rename(columns=columns_mapping)

    return df


def process_dataframe(
    df: pd.DataFrame,
    columns_processing: dict[str, ColumnProcessing],
) -> pd.DataFrame:
    """
    Process a pandas DataFrame based on provided column processing instructions.

    Parameters:
    - df: The input DataFrame to be processed.
    - columns_processing: A dictionary where keys are column names and values are ColumnProcessing dicts containing processing instructions.

    Returns:
    - A new DataFrame with processed columns.
    """
    for col, processing in columns_processing.items():
        if col in df.columns and processing.get("formatter"):
            df[col] = df[col].apply(processing["formatter"])

    return df
