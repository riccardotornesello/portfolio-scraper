from enum import Enum
from dataclasses import dataclass

import pandas as pd


class ColumnType(str, Enum):
    STRING = "string"
    NUMERIC = "numeric"


@dataclass
class Column:
    source: str | None = None
    col_type: ColumnType = ColumnType.STRING


def prepare_dataframe(
    df: pd.DataFrame,
    columns: dict[str, Column],
    index_col: str | None = None,
) -> pd.DataFrame:
    # Rename columns to standard names if source is specified
    df = df.rename(
        columns={v.source: k for k, v in columns.items() if v.source is not None}
    )

    # Keep only the columns we care about
    df = df.reindex(columns=columns.keys())

    # Convert numeric columns to numeric types, coercing errors to NaN
    numeric_columns = [
        col
        for col, col_info in columns.items()
        if col_info.col_type == ColumnType.NUMERIC
    ]
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

    # Convert text to uppercase
    string_columns = [
        col
        for col, col_info in columns.items()
        if col_info.col_type == ColumnType.STRING
        and df[col].dtype in [object, "string"]
    ]
    df[string_columns] = df[string_columns].apply(lambda x: x.str.upper())

    # Set index if specified
    if index_col:
        df = df.set_index(index_col)

    return df
