import pickle
import tempfile

import mock
import pandas as pd

from src.model_training import Model
import numpy as np
import pytest
from configs.configs import ModelConfig, PathsConfig, RunConfig


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


def test_training_evaluates_data_and_saves_fitted_model(tmp_path):
    amounts = [float(value) for value in range(10)]

    data = pd.DataFrame({"amount": amounts, "fraud": [False, True] * 5})
    expected_x = pd.DataFrame({"amount": amounts})
    expected_y = pd.Series([False, True] * 5, name="fraud")
    expected_scores = {"test_f1": np.array([0.2, 0.4, 0.6, 0.8, 1.0])}

    classifier = mock.Mock()
    classifier.fit.return_value = "fitted-model"

    with (  # mocking sources of randomness
        mock.patch(
            "src.model_training.RandomForestClassifier", return_value=classifier
        ) as factory,
        mock.patch(
            "src.model_training.cross_validate", return_value=expected_scores
        ) as validate,
        mock.patch.object(PathsConfig, "model_path", str(tmp_path) + "/"),
    ):
        model = Model()
        model.train_model(data)

        actual_scores = model.get_cv_scores(data)
        model.save_model()

    factory.assert_called_once_with(
        max_depth=ModelConfig.max_depth, class_weight=ModelConfig.class_weight
    )
    validate.assert_called_once()
    bla, validation_x, validation_y = validate.call_args.args

    # testing it uses the right data
    pd.testing.assert_frame_equal(validation_x, expected_x)
    pd.testing.assert_series_equal(validation_y, expected_y)
    classifier.fit.assert_called_once()
    training_x, training_y = classifier.fit.call_args.args

    pd.testing.assert_frame_equal(training_x, expected_x)
    pd.testing.assert_series_equal(training_y, expected_y)

    assert set(actual_scores) == set(expected_scores)
    np.testing.assert_array_equal(actual_scores["test_f1"], expected_scores["test_f1"])

    model_path = tmp_path / f"{ModelConfig.model_name}.pkl"

    with model_path.open("rb") as file:
        assert pickle.load(file) == "fitted-model"


def test_training_requires_fraud_target():
    # making sure a model is not trained if there are no labels
    data = pd.DataFrame({"amount": [10.0, 20.0]})

    with (
        mock.patch(
            "src.model_training.RandomForestClassifier",
        ) as factory,
        mock.patch(
            "src.model_training.cross_validate",
        ) as validate,
    ):
        model = Model()

        with pytest.raises(KeyError, match="fraud"):
            model.train_model(data)

    factory.assert_not_called()
    validate.assert_not_called()


def test_untrained_model_doesnt_log_results():
    # making sure an untrained model doesnt log results
    with mock.patch("src.model_training.mlflow") as tracking:
        tracking.get_experiment_by_name.return_value = None

        model = Model()

        with pytest.raises(AssertionError, match="not trained"):
            model.log_model_to_mlflow()

    tracking.log_dict.assert_not_called()
    tracking.log_metric.assert_not_called()
    tracking.log_artifact.assert_not_called()
