from src.data_preprocessing import _get_data_after
from src.sql_database import read_data, write_data
import mysql.connector
import pytest
from pyspark.testing.utils import assertDataFrameEqual
import datetime
import json
from collections import Counter
from contextlib import closing


TRANSACTION_COLUMNS = "chck_date, payment_type, category, amount, fraud"


def seed_transactions(connection, table, rows):  # sql helper for adding rows
    with closing(connection.cursor()) as cursor:
        cursor.executemany(
            f"""
            INSERT INTO {table} ({TRANSACTION_COLUMNS})
            VALUES (%s, %s, %s, %s, %s)
            """,
            rows,
        )


def fetch_transactions(connection, table):  # sql helper for getting rows
    with closing(connection.cursor()) as cursor:
        cursor.execute(f"SELECT {TRANSACTION_COLUMNS} FROM {table}")
        return cursor.fetchall()


@pytest.mark.parametrize("table", ["raw_transactions", "preprocessed_transactions"])
def test_read_transactions_preserves_values_and_schema(
    mysql_fixture, make_transactions, table
):
    # making sure the schema is preserved in read operation
    first = (
        datetime.datetime(2021, 1, 2, 12, 30, 0, 123456),
        "coffeeeee",
        "milk",
        -12.5,
        False,
    )

    rows = [
        first,
        (datetime.datetime(2021, 1, 3), "transfer", "travel", 0.0, True),
        first,
        (None, None, None, None, None),
    ]

    seed_transactions(mysql_fixture, table, rows)

    expected = make_transactions(rows)
    actual = read_data(table)

    assert actual.schema == expected.schema
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize(
    "start_date, expected_indices",
    [
        (datetime.date(2021, 1, 1), [0, 1, 2, 3]),
        (datetime.date(2021, 1, 2), [1, 2, 3]),
        (datetime.date(2021, 1, 4), []),
    ],
)
def test_get_data_after_includes_boundary_and_later_rows(
    mysql_fixture, make_transactions, start_date, expected_indices
):
    rows = [
        (
            datetime.datetime(2021, 1, 1, 23, 59, 59),
            "card",
            "adventures",
            10.0,
            False,
        ),  # precise date time
        (datetime.datetime(2021, 1, 2), "card", "adventures", 20.0, True),
        (datetime.datetime(2021, 1, 2, 12), "transfer", "travel", 30.0, False),
        (datetime.datetime(2021, 1, 3), "card", "travel", 40.0, True),
        (None, "card", "adventures", 50.0, False),  # no date
    ]

    seed_transactions(mysql_fixture, "raw_transactions", rows)

    expected = make_transactions([rows[index] for index in expected_indices])

    actual = _get_data_after(start_date)

    assert actual.schema == expected.schema
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize("table", ["raw_transactions", "preprocessed_transactions"])
def test_read_empty_transactions_has_expected_schema(
    mysql_fixture, make_transactions, table
):
    expected = make_transactions([])
    actual = read_data(table)

    assert actual.schema == expected.schema
    assertDataFrameEqual(actual, expected)


def test_read_features_restores_arrays_booleans_and_nulls(mysql_fixture, make_features):
    stored_rows = [
        (25.5, 1, -0.5, 0.5, "[1.0, 0.0]", "[0.0]", 0),
        (-5.0, 0, 0.5, -0.5, "[]", "[1.0]", 1),  # empty array edge case
        (None, None, None, None, None, None, None),  # all none edge case
    ]

    with closing(mysql_fixture.cursor()) as cursor:
        cursor.executemany(
            """
            INSERT INTO transaction_features (
                amount,
                fraud,
                z_score,
                z_score_by_category,
                enc_category,
                enc_payment_type,
                is_large_transaction
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            stored_rows,
        )

    expected = make_features(
        [
            (
                25.5,
                True,
                -0.5,
                0.5,
                [1.0, 0.0],
                [0.0],
                False,
            ),
            (
                -5.0,
                False,
                0.5,
                -0.5,
                [],
                [1.0],
                True,
            ),
            (None, None, None, None, None, None, None),
        ]
    )

    actual = read_data("transaction_features")

    assert actual.schema == expected.schema
    assertDataFrameEqual(actual, expected)


def test_read_empty_features_has_expected_schema(mysql_fixture, make_features):
    expected = make_features([])
    actual = read_data("transaction_features")

    assert actual.schema == expected.schema
    assertDataFrameEqual(actual, expected)


@pytest.mark.parametrize("table", ["raw_transactions", "preprocessed_transactions"])
@pytest.mark.parametrize("row_count", [0, 1, 2, 3])
def test_write_transactions_replaces_existing_rows(
    mysql_fixture, make_transactions, table, row_count
):
    # making sure that the transactions written as new overwrite old ones
    old_rows = [(datetime.datetime(2020, 1, 1), "old", "old", 999.0, False)]

    available_rows = [
        (datetime.datetime(2021, 1, 2), "coffeeeee", "milk", -12.5, False),
        (datetime.datetime(2021, 1, 2), "coffeeeee", "milk", -12.5, False),
        (None, None, None, None, None),
    ]

    expected_rows = available_rows[:row_count]

    seed_transactions(mysql_fixture, table, old_rows)

    write_data(make_transactions(expected_rows), table, batch_size=2)

    actual_rows = fetch_transactions(mysql_fixture, table)

    assert Counter(actual_rows) == Counter(expected_rows)


def test_write_features_preserves_arrays_and_nulls(mysql_fixture, make_features):
    expected_rows = [
        (None, None, None, None, None, None, None),
        (-5.0, False, 0.5, -0.5, [], [1.0], True),
        (25.5, True, -0.5, 0.5, [1.0, 0.0], [0.0], False),
    ]

    write_data(make_features(expected_rows), "transaction_features", batch_size=2)

    with closing(mysql_fixture.cursor()) as cursor:
        cursor.execute(
            """
            SELECT
                amount,
                fraud,
                z_score,
                z_score_by_category,
                enc_category,
                enc_payment_type,
                is_large_transaction
            FROM transaction_features
            ORDER BY amount
            """
        )

        actual_rows = []

        for row in cursor.fetchall():
            values = list(row)

            for index in (4, 5):
                if values[index] is not None:
                    values[index] = json.loads(values[index])

            actual_rows.append(tuple(values))

    assert actual_rows == expected_rows


def test_failed_write_preserves_previous_committed_data(
    mysql_fixture, make_transactions
):
    # making sure that if writing fails, the previous commit is preserved
    old_rows = [(datetime.datetime(2020, 1, 1), "card", "original", 5.0, False)]

    replacement_rows = [
        (datetime.datetime(2021, 1, 1), "card", "cyberpunk 2077", 20.0, False),
        (datetime.datetime(2021, 1, 2), "card", "blabla" * 256, 30.0, True),
    ]

    seed_transactions(mysql_fixture, "raw_transactions", old_rows)

    with pytest.raises(mysql.connector.Error) as error:
        write_data(
            make_transactions(replacement_rows), "raw_transactions", batch_size=1
        )

    assert error.value.errno == 1406

    actual_rows = fetch_transactions(mysql_fixture, "raw_transactions")

    assert Counter(actual_rows) == Counter(old_rows)
