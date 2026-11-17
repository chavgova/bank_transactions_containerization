import pytest
from pyspark.sql import SparkSession
import os
from contextlib import closing
import mock
import mysql.connector


@pytest.fixture(scope="session")
def spark_fixture():
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("pipeline-tests")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
    yield spark
    spark.stop()


@pytest.fixture
def make_transactions(spark_fixture):
    def make(rows):
        return spark_fixture.createDataFrame(
            rows,
            """
            chck_date TIMESTAMP,
            payment_type STRING,
            category STRING,
            amount DOUBLE,
            fraud BOOLEAN
            """,
        )

    return make


@pytest.fixture
def make_features(spark_fixture):
    def make(rows):
        return spark_fixture.createDataFrame(
            rows,
            """
            amount DOUBLE,
            fraud BOOLEAN,
            z_score DOUBLE,
            z_score_by_category DOUBLE,
            enc_category ARRAY<DOUBLE>,
            enc_payment_type ARRAY<DOUBLE>,
            is_large_transaction BOOLEAN
            """,
        )

    return make


@pytest.fixture
def mysql_fixture():
    class MockDatabaseConfig:
        host = os.getenv("TEST_MYSQL_HOST", "127.0.0.1")
        port = int(os.getenv("TEST_MYSQL_PORT", "3307"))
        database = "bank_test"
        user = "bank_test"
        password = "test_password"

    with mock.patch("src.sql_database.DatabaseConfig", MockDatabaseConfig):
        with closing(
            mysql.connector.connect(
                host=MockDatabaseConfig.host,
                port=MockDatabaseConfig.port,
                database=MockDatabaseConfig.database,
                user=MockDatabaseConfig.user,
                password=MockDatabaseConfig.password,
                autocommit=True,
            )
        ) as connection:

            def clear_tables():
                with closing(connection.cursor()) as cursor:
                    for table in (
                        "raw_transactions",
                        "preprocessed_transactions",
                        "transaction_features",
                    ):
                        cursor.execute(f"DELETE FROM {table}")

            clear_tables()

            try:
                yield connection
            finally:
                clear_tables()
