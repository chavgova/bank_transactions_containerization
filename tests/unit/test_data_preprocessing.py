import datetime
import tempfile

import mock
from pyspark.testing.utils import assertDataFrameEqual

from src.data_preprocessing import _get_data_after, get_preprocessed_data


def test_get_data_after(spark_fixture):
    data = spark_fixture.createDataFrame(
        [
            {
                "amount": 1,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(2020, 1, 1, 1, 1),
            },
            {
                "amount": 2,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(2021, 1, 1, 1, 1),
            },
            {
                "amount": 3,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(2021, 2, 1, 1, 1),
            },
            {
                "amount": 4,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(
                    2021,
                    1,
                    2,
                ),
            },
        ]
    )
    expected = spark_fixture.createDataFrame(
        [
            {
                "amount": 2,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(2021, 1, 1, 1, 1),
            },
            {
                "amount": 3,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(2021, 2, 1, 1, 1),
            },
            {
                "amount": 4,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(
                    2021,
                    1,
                    2,
                ),
            },
        ]
    )

    with tempfile.TemporaryDirectory() as tmpdir:

        class MockPathsConfig:
            raw_data_path = tmpdir + "/donono"

        with mock.patch("src.data_preprocessing.PathsConfig", MockPathsConfig):
            data.write.parquet(MockPathsConfig.raw_data_path)

            out = _get_data_after(datetime.date(2021, 1, 1))
            assertDataFrameEqual(out, expected, ignoreColumnOrder=True)


def test_get_preprocessed_data(spark_fixture):
    # Am I actually testing something with this test, or am I being lazy trying to increase my coverage?
    data = spark_fixture.createDataFrame(
        [
            {
                "amount": 1,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(2020, 1, 1, 1, 1),
            },
            {
                "amount": 2,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(2021, 1, 1, 1, 1),
            },
            {
                "amount": 3,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(2021, 2, 1, 1, 1),
            },
            {
                "amount": 4,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(
                    2021,
                    1,
                    2,
                ),
            },
        ]
    )
    expected = spark_fixture.createDataFrame(
        [
            {
                "amount": 2,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(2021, 1, 1, 1, 1),
            },
            {
                "amount": 3,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(2021, 2, 1, 1, 1),
            },
            {
                "amount": 4,
                "payment_type": 1,
                "category": 1,
                "fraud": 1,
                "chck_date": datetime.datetime(
                    2021,
                    1,
                    2,
                ),
            },
        ]
    )

    with tempfile.TemporaryDirectory() as tmpdir:

        class MockPathsConfig:
            raw_data_path = tmpdir + "/donono"

        with mock.patch("src.data_preprocessing.PathsConfig", MockPathsConfig):
            data.write.parquet(MockPathsConfig.raw_data_path)

            out = get_preprocessed_data(datetime.date(2021, 1, 1))
            assertDataFrameEqual(out, expected, ignoreColumnOrder=True)
