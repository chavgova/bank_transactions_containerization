import datetime
import tempfile

import mock
from pyspark.testing.utils import assertDataFrameEqual
from pyspark.sql import DataFrame
from pyspark.errors import AnalysisException
from src.data_preprocessing import _get_data_after, get_preprocessed_data, load_raw_data
from configs.configs import PathsConfig, RunConfig
import pytest


@pytest.mark.parametrize(
    "sample_rate", [0.0, 0.25, 1.0]
)  # testing multiple sample rates with one test function
def test_preprocessing_uses_configured_sampling(sample_rate):
    start_date = datetime.date(2021, 1, 2)

    source = mock.Mock(spec=DataFrame)
    sampled = mock.Mock(spec=DataFrame)
    source.sample.return_value = sampled

    with mock.patch(
        "src.data_preprocessing._get_data_after", return_value=source
    ) as reader:
        with mock.patch.object(RunConfig, "sample_rate", sample_rate):
            result = get_preprocessed_data(start_date)

    reader.assert_called_once_with(start_date)
    source.sample.assert_called_once_with(sample_rate)
    assert result is sampled


def test_preprocessing_propagates_read_failure():  # making sure an error is raised if data cannot be read
    with mock.patch(
        "src.data_preprocessing._get_data_after",
        side_effect=RuntimeError("read failed"),
    ):
        with pytest.raises(RuntimeError, match="read failed"):
            get_preprocessed_data(datetime.date(2021, 1, 2))


@pytest.mark.parametrize("empty", [False, True])
def test_load_raw_data_transfers_source_rows(tmp_path, make_transactions, empty):
    # testing both no rows and existing rows in data
    rows = (
        [] if empty else [(datetime.datetime(2021, 1, 2), "card", "food", 12.5, False)]
    )

    expected = make_transactions(rows)
    source_path = str(tmp_path / "raw")
    expected.write.parquet(source_path)

    with mock.patch.object(PathsConfig, "raw_data_path", source_path):
        with mock.patch("src.data_preprocessing.write_data") as writer:
            load_raw_data()

    writer.assert_called_once()

    actual_data, actual_table = writer.call_args.args

    assert actual_table == "raw_transactions"
    assertDataFrameEqual(actual_data, expected, ignoreColumnOrder=True)


def test_load_raw_data_missing_source_does_not_write(tmp_path):
    # making sure if data is missing, no dataset is created
    with mock.patch.object(PathsConfig, "raw_data_path", str(tmp_path / "missing")):
        with mock.patch("src.data_preprocessing.write_data") as writer:
            with pytest.raises(AnalysisException):
                load_raw_data()

    writer.assert_not_called()
