import logging
from enum import Enum
from typing import TypedDict, Optional, Callable, Mapping

import pandas as pd


_log = logging.getLogger(__name__)


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


def map_values(
    series: pd.Series,
    mapping: Mapping[str, Enum | str | None],
    description: str = "values",
) -> pd.Series:
    """
    Map the values of a pandas Series to standard values.

    Parameters:
    - series: The Series whose values need to be mapped.
    - mapping: A dictionary where keys are the uppercase original values and values are the
      standard values (Enum members or strings). None means the value has no standard equivalent.
    - description: Description of the values, used in the log of the unmapped values.

    Returns:
    - A new Series with the standard values (Enum members are converted to their value).
      Empty and unmapped values become None; unmapped values are logged as warnings.
    """
    keys = series.map(lambda v: v.strip().upper() if isinstance(v, str) else None)

    unmapped = sorted({k for k in keys.dropna() if k and k not in mapping})
    if unmapped:
        _log.warning("Unmapped %s: %s", description, unmapped)

    def standard_value(key: str | None) -> str | None:
        value = mapping.get(key) if key else None
        return value.value if isinstance(value, Enum) else value

    return keys.map(standard_value).astype(object)
