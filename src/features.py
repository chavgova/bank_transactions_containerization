import typing

import pandas as pd

from configs.configs import RunConfig

from pyspark.sql import DataFrame
import pyspark.sql.functions as F
from sklearn.preprocessing import OneHotEncoder
from pyspark.ml.functions import vector_to_array
from pyspark.ml.feature import OneHotEncoder, StringIndexer


def _get_encoded_features(data: DataFrame, col_name: str) -> DataFrame:
    """
    Returns one-hot encoded features for col_name.

    :return: Data with one-Hot encoded column named "col_name+_idx".
    """
    data = (
        StringIndexer(
            inputCol=col_name,
            outputCol="idx_" + col_name,
        )
        .fit(data)
        .transform(data)
    )
    # This is an example why we need the same implementation in training and inference. Check dropLast in the signature.
    data = (
        OneHotEncoder(
            inputCol="idx_" + col_name,
            outputCol="enc_" + col_name,
        )
        .fit(data)
        .transform(data)
    )
    data = data.withColumn("enc_" + col_name, vector_to_array(F.col("enc_" + col_name)))
    data = data.drop(
        F.col(col_name),
        F.col("idx_" + col_name),
    )
    return data


def _get_z_score(data: DataFrame, group_by_cols: typing.List[str] = []) -> DataFrame:
    f"""
    Calculates z-score on the "amount".

    If group_by_cols is passed with non-empty list, it calculates z-score by grouping the grouping_cols. If not,
    it calculates z-score taking the whole amount col as sample set.
    
    :return: data with added "z_score" column if group_cols is empty or "z_score_{group_by_cols} if not.
    """
    stats = data.groupby(group_by_cols).agg(
        F.mean("amount").alias("mean"),
        F.stddev("amount").alias("std"),
        # Another example why training and inference code must be the exact same implementation:
        # https://en.wikipedia.org/wiki/Unbiased_estimation_of_standard_deviation
        # F.stddev_pop("amount").alias("std"),
    )
    data = data.join(stats, on=group_by_cols if group_by_cols else None)
    z_score_col_name = (
        f"z_score_by_{'_'.join(group_by_cols)}" if group_by_cols else "z_score"
    )
    data = data.withColumn(
        z_score_col_name, (F.col("amount") - F.col("mean")) / F.col("std")
    )
    data = data.drop("mean", "std")
    return data


def get_features(data: DataFrame) -> DataFrame:
    data = _get_z_score(data)
    data = _get_z_score(data, ["category"])
    for col_name in ["category", "payment_type"]:
        data = _get_encoded_features(data, col_name)
    data = data.withColumn(
        "is_large_transaction",
        F.col("amount") > RunConfig.threshold_in_eur_to_consider_large_transactions,
    )
    data = data.drop(F.col("chck_date"))
    return data


def get_nested_column_extended(data: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """
    For the column name given in the data, expands the list elements of the column into separate columns.

    WARNING: Drops the col_name

    Example:

    input:

        +--------+
        |   A    |
        +--------+
        | [1, 2] |
        | [3, 4] |
        +--------+

    Output:

        +-----+-----+
        | A_0 | A_1 |
        +-----+-----+
        |   1 |   2 |
        |   3 |   4 |
        +-----+-----+

    :param data: Data that has list as elements in col_name
    :param col_name: The column with list elements
    :return: Data returned with list elements as separate columns
    """
    expanded_col = pd.DataFrame(
        data[col_name].tolist(),
        columns=[col_name + "_" + str(i) for i in range(len(data[col_name][0]))],
    )
    data = data.drop(col_name, axis=1)
    return pd.concat([data, expanded_col], axis=1)
