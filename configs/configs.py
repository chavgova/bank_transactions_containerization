from dataclasses import dataclass


@dataclass(init=False, frozen=True)
class PathsConfig:
    raw_data_path: str = "data/trx/"  # Raw upstream data.
    preprocessing_data_path: str = "data/intermediate/preprocessing/"
    features_data_path: str = "data/intermediate/features/"

    model_path: str = "models/"  # Model store


@dataclass(init=False, frozen=True)
class RunConfig:
    # The fraction of the entire raw data to be selected at random.
    # For the sake of speed in development, set this to smaller number. In production, always expected to be
    # set to 1.0.
    sample_rate: float = 1.0
    num_folds: int = 5
    threshold_in_eur_to_consider_large_transactions: float = 123.45
    # note: ⚠️ Do not forget to change to
    # note:     Local Run:          "http://localhost:8080"
    # note:     Docker Compose Run: "http://mlflow:8080"
    # note: See docker-compose.yaml notes.
    mlflow_tracking_uri: str = "http://localhost:8080"
    experiment_name: str = "Alpha"


@dataclass(init=False, frozen=True)
class ModelConfig:
    model_name: str = "alpha"
    max_depth: int = 100
    class_weight: str = "balanced"
