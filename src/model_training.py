import pickle
import tempfile

import mlflow
import pandas as pd
from sklearn.model_selection import cross_validate
from sklearn.ensemble import RandomForestClassifier

from configs.configs import ModelConfig, RunConfig, PathsConfig


class Model:
    def __init__(self):
        self._model = None
        self._cv_scores = None

    @staticmethod
    def _get_model_object() -> RandomForestClassifier:
        return RandomForestClassifier(
            max_depth=ModelConfig.max_depth, class_weight=ModelConfig.class_weight
        )

    @staticmethod
    def _get_x_y(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        return data.drop("fraud", axis=1), data["fraud"]

    def train_model(self, data: pd.DataFrame) -> None:
        x, y = self._get_x_y(data)
        classifier = self._get_model_object()
        self._cv_scores = cross_validate(
            classifier,
            x,
            y,
            cv=RunConfig.num_folds,
            return_train_score=True,
            n_jobs=-1,
            scoring=["precision", "recall", "f1"],
        )
        self._model = classifier.fit(x, y)

    def get_cv_scores(self, data: pd.DataFrame) -> dict[str, float]:
        return self._cv_scores

    def save_model(self):
        with open(f"{PathsConfig.model_path}{ModelConfig.model_name}.pkl", "wb") as f:
            pickle.dump(self._model, f)

    def log_model_to_mlflow(self):
        # note: We will use the Tracking Server version of MLFLow. Basically, it is a MLFlow API.
        mlflow.set_tracking_uri(RunConfig.mlflow_tracking_uri)

        # note: In MLFlow, there are "experiments". Which holds info about experiments of the same group, and the outputs like the model.
        if experiment := mlflow.get_experiment_by_name(RunConfig.experiment_name):
            mlflow_experiment_id = experiment.experiment_id
        else:
            # note: If the experiment is already there, we want to use it.
            mlflow_experiment_id = mlflow.create_experiment(RunConfig.experiment_name)

        # note: One level below of experiments, there are runs. Each experiment has one or more runs. Runs are basically
        # note: The "run" of your experiment pipeline. It can have different models, hparams, feats, etc.
        with mlflow.start_run(experiment_id=mlflow_experiment_id):
            assert self._cv_scores is not None, (
                "The model is not trained and there are no experiment results."
            )
            # note: You can log any kind of data in MLFlow Run. Some can be visualized directly in MLFlow.
            mlflow.log_dict(self._cv_scores, "cv_scores.json")
            mlflow.log_metric("test_f1_mean", self._cv_scores["test_f1"].mean())
            mlflow.log_metric("test_f1_std", self._cv_scores["test_f1"].std())
            with tempfile.NamedTemporaryFile("wb") as temp_file:
                with open(temp_file.name + ".pkl", "wb") as f:
                    pickle.dump(self._model, f)
                # note: In here, I "log" my model as an "Artifact". Which is kind of catch-all phrase of a file.
                mlflow.log_artifact(
                    temp_file.name + ".pkl", f"{ModelConfig.model_name}.pkl"
                )
