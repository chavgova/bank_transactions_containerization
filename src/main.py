import datetime

from pyspark.sql import SparkSession

from src.model_training import Model
from src.features import get_features, get_nested_column_extended
from configs.configs import PathsConfig
from src.data_preprocessing import get_preprocessed_data


def main():  # pragma: no cover
    data = get_preprocessed_data(datetime.date(year=2019, month=6, day=1))
    data.write.parquet(PathsConfig.preprocessing_data_path, mode="overwrite")

    spark = SparkSession.builder.master("local[2]").getOrCreate()
    data = spark.read.parquet(PathsConfig.preprocessing_data_path)
    data = get_features(data)
    data.write.parquet(PathsConfig.features_data_path, mode="overwrite")

    # We keep model training the same without Spark because:
    # 1) SparkML library is a mess. There are other better libraries for out-of-memory or parallel training.
    # 2) It must be one big feature data to not fit 16GB memory by default. If it is that big, maybe use a NN?
    data = spark.read.parquet(PathsConfig.features_data_path).toPandas()
    for col_name in ["enc_category", "enc_payment_type"]:
        data = get_nested_column_extended(data, col_name)

    model = Model()
    model.train_model(data)
    print(model.get_cv_scores(data))
    # note: Here is the main change! We will log our model to MLFlow. Which is basically "storing" it there.
    model.log_model_to_mlflow()


if __name__ == "__main__":  # pragma: no cover
    main()
