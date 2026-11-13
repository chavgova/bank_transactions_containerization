import pickle
import tempfile

import mock
import pandas as pd

from src.model_training import Model


def test_model_get_x_y():
    cases = [
        {
            "data": pd.DataFrame({"fraud": [1, 0, 0, 1], "amount": [1, 1, 1, 1]}),
            "expected_x": pd.DataFrame({"amount": [1, 1, 1, 1]}),
            "expected_y": pd.Series([1, 0, 0, 1], copy=False, name="fraud"),
        }
    ]

    for case in cases:
        out_x, out_y = Model._get_x_y(case["data"])
        pd.testing.assert_frame_equal(out_x, case["expected_x"])
        pd.testing.assert_series_equal(out_y, case["expected_y"])


def test_model_save_model():
    class MockModelConfig:
        model_name = "donono"

    class MockRunConfig:
        mlflow_tracking_uri: str = "http://localhost:8080"
        experiment_name: str = "Alpha"

    with tempfile.TemporaryDirectory() as tmpdir:

        class MockPathsConfig:
            model_path = tmpdir + "/"

        with mock.patch("src.model_training.PathsConfig", MockPathsConfig):
            with mock.patch("src.model_training.ModelConfig", MockModelConfig):
                model = Model()
                model._model = "foo"
                model.save_model()

                with open(f"{tmpdir}/donono.pkl", "rb") as f:
                    model = pickle.load(f)
                    assert model == "foo"
