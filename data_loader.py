"""
data_loader.py
--------------
Reusable data-loading module for the Student Performance project.
All downstream code (notebook, dashboard, report) should import load_data()
from here instead of reading and cleaning the CSV inline.
"""

from pathlib import Path

import pandas as pd

# Default path: StudentsPerformance.csv at the project root, resolved relative
# to this file so it works regardless of the calling directory.
_DEFAULT_CSV = Path(__file__).parent.parent / "StudentsPerformance.csv"

# Canonical column rename map applied immediately after read_csv.
_RENAME_MAP = {
    "race/ethnicity": "race_ethnicity",
    "parental level of education": "parental_level_of_education",
    "test preparation course": "test_preparation_course",
    "math score": "math_score",
    "reading score": "reading_score",
    "writing score": "writing_score",
}


def load_data(csv_path=None) -> pd.DataFrame:
    """Load and validate the Student Performance CSV.

    Parameters
    ----------
    csv_path : str or Path, optional
        Path to the CSV file.  Defaults to ``StudentsPerformance.csv`` at the
        project root.

    Returns
    -------
    pd.DataFrame
        Clean DataFrame with renamed columns, zero missing values, and zero
        duplicate rows.  Score columns are cast to int64 by pandas automatically.

    Raises
    ------
    ValueError
        If any missing values or duplicate rows are found.
    """
    path = Path(csv_path) if csv_path is not None else _DEFAULT_CSV

    df = pd.read_csv(path)

    # Rename columns — handle slash in race/ethnicity and spaces elsewhere.
    df = df.rename(columns=_RENAME_MAP)

    # Validate: no missing values.
    missing = df.isnull().sum().sum()
    if missing > 0:
        raise ValueError(
            f"Dataset contains {missing} missing value(s) after loading. "
            "Check the source CSV."
        )

    # Validate: no duplicate rows.
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        raise ValueError(
            f"Dataset contains {duplicates} duplicate row(s) after loading. "
            "Check the source CSV."
        )

    return df


if __name__ == "__main__":
    df = load_data()
    print("Shape:", df.shape)
    print("\nColumn dtypes:")
    print(df.dtypes)
