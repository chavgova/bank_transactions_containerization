import mock
import mlflow
import numpy as np

from src.model_training import Model


def test_model_training_log_model_to_mlflow():
    class MockModelConfig:
        model_name = "donono"

    class MockRunConfig:
        # note: We definately do not want to use any upstream deployment of MLFlow for our tests.
        # note: That is why we use Docker Compose. Normally what would be an actual server host on the internet, is now
        # note: the hostname of the MLFlow docker container.

        # note: Luck us! By default, if you forward the port, any container is hosted in our "localhost" without doing
        # note: networking tricks. This is if I am using my local to access.
        # note: If I want to access from one container (e.g. nova) to MLflow, all I need to do is to use the service
        # note: name of that. In this case localhost --> mlflow
        mlflow_tracking_uri: str = "http://localhost:8081"
        experiment_name: str = "TextExp"

    # note: Now without changing ANY CODE (which is very important), I can run my application code for test.
    with mock.patch("src.model_training.RunConfig", MockRunConfig):
        with mock.patch("src.model_training.ModelConfig", MockModelConfig):
            model = Model()
            model._model = "foo"
            model._cv_scores = {"test_f1": np.array([0.1, 0.2, 0.3])}
            model.log_model_to_mlflow()

    experiment = mlflow.get_experiment_by_name(MockRunConfig.experiment_name)
    assert experiment

    run_id = mlflow.search_runs(experiment.experiment_id).iloc[0]["run_id"]
    run = mlflow.get_run(run_id)
    artifacts = mlflow.artifacts.list_artifacts(run.info.artifact_uri)
    assert artifacts[0].path in ["artifacts/cv_scores.json", "artifacts/donono.pkl"]
    assert artifacts[1].path in ["artifacts/cv_scores.json", "artifacts/donono.pkl"]


def test_logging_existing_experiment_mlflow():
    # if an experiment exists, a dublicate one should not be created
    class MockModelConfig:
        model_name = "donono"

    class MockRunConfig:
        mlflow_tracking_uri = "http://localhost:8081"
        experiment_name = f"TextExp-1"

    previous_uri = mlflow.get_tracking_uri()
    mlflow.set_tracking_uri(MockRunConfig.mlflow_tracking_uri)

    # experiment exists
    existing_id = mlflow.create_experiment(MockRunConfig.experiment_name)

    with mock.patch("src.model_training.RunConfig", MockRunConfig):
        with mock.patch("src.model_training.ModelConfig", MockModelConfig):
            model = Model()
            model._model = "synthetic-model"
            model._cv_scores = {"test_f1": np.array([0.1, 0.2, 0.3])}
            model.log_model_to_mlflow()

    experiment = mlflow.get_experiment_by_name(MockRunConfig.experiment_name)
    assert experiment is not None

    if existing_id is not None:
        assert experiment.experiment_id == existing_id

    runs = mlflow.search_runs([experiment.experiment_id])
    assert len(runs) == 1
