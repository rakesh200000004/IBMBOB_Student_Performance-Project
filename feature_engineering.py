"""
feature_engineering.py
-----------------------
Reusable feature-engineering module for the Student Performance project.
Call engineer_features(df) after load_data() to add derived columns used by
the notebook, dashboard, and ML pipeline.
"""

import pandas as pd


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived feature columns to the student performance DataFrame.

    The function works on a **copy** of the input DataFrame and does not
    modify the original in-place.

    New columns added
    -----------------
    average_score : float
        Mean of math_score, reading_score, and writing_score, rounded to
        2 decimal places.
    total_score : int
        Sum of math_score, reading_score, and writing_score.
    score_group : str
        Categorical label derived from average_score:
        - "Low"    if average_score < 50
        - "Medium" if 50 <= average_score < 70
        - "High"   if average_score >= 70

    Note
    ----
    The three subject score columns (math_score, reading_score, writing_score)
    are intentionally left in the returned DataFrame for EDA purposes, but they
    must **never** be used as input features in an ML model — doing so would
    constitute data leakage, as average_score is a direct linear combination of
    those columns.

    Parameters
    ----------
    df : pd.DataFrame
        Clean DataFrame returned by ``load_data()``.

    Returns
    -------
    pd.DataFrame
        New DataFrame (copy) with three additional columns.
    """
    out = df.copy()

    out["average_score"] = (
        (out["math_score"] + out["reading_score"] + out["writing_score"]) / 3
    ).round(2)

    out["total_score"] = out["math_score"] + out["reading_score"] + out["writing_score"]

    out["score_group"] = pd.cut(
        out["average_score"],
        bins=[-1, 49.999, 69.999, 100],
        labels=["Low", "Medium", "High"],
    ).astype(str)

    return out
