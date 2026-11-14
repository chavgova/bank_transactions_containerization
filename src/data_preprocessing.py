from datetime import date

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql import DataFrame

from configs.configs import PathsConfig, RunConfig
from src.sql_database import read_data, write_data


def load_raw_data() -> None:
    # copies the raw parquet dataset into mysql
    spark = SparkSession.builder.master("local[2]").getOrCreate()

    data = spark.read.parquet(PathsConfig.raw_data_path)

    write_data(data, "raw_transactions")

def _get_data_after(start_date: date) -> DataFrame:
    """
    Will read and return the data after (including) start_date.

    See also: data_processing.data_processing()

    :param start_date: The date data should be started to read from.
    :return: All data including and after the start_date
    """
    # reads transactions on and after the date from mysql
    return read_data( "raw_transactions", start_date=start_date) 


def get_preprocessed_data(start_date: date) -> DataFrame:
    """
    Preprocessing step.

    Will read and pre-process the data starting from start_date. All the data from (including) start_date to later time
    will be preprocessed. The date will be got from the chck_date.

    Example:

        +-----+------------+---------------+
        | Row | chck_date  | will_process? |
        +-----+------------+---------------+
        |   1 | 2025-01-01 | No            |
        |   2 | 2025-01-01 | No            |
        |   3 | 2025-01-02 | Yes           |
        |   4 | 2025-01-02 | Yes           |
        |   5 | 2025-01-03 | Yes           |
        |   6 | 2024-12-30 | No            |
        |   7 | 2099-01-01 | Yes           |
        +-----+------------+---------------+

    :param start_date: The date the preprocessing should start with. This step will process all the data starting
    (including) this date, and follow up with the later dates.
    :return: Preprocessed data
    """
    data = _get_data_after(start_date)
    # Remember the lazy execution:
    # - This will actually (should) help with reading even fewer data.
    data = data.sample(
        RunConfig.sample_rate
    )  # Not making this a func. as it is a simple one-liner.
    # I don't have to deal with string encoding like .csv here, as Parquet encodes string properly.
    return data
