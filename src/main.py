import datetime

from pyspark.sql import SparkSession

from src.model_training import Model
from src.features import get_features, get_nested_column_extended
from configs.configs import PathsConfig
from src.data_preprocessing import get_preprocessed_data, load_raw_data
from src.sql_database import read_data, write_data


def main():  # pragma: no cover
    load_raw_data()  # importing the dataset into mysql

    data = get_preprocessed_data(datetime.date(year=2019, month=6, day=1))
    write_data(data, "preprocessed_transactions")

    # reading preprocessed trx, calc features, storing them in mysql
    data = read_data("preprocessed_transactions")
    data = get_features(data)
    write_data(data, "transaction_features")

    # We keep model training the same without Spark because:
    # 1) SparkML library is a mess. There are other better libraries for out-of-memory or parallel training.
    # 2) It must be one big feature data to not fit 16GB memory by default. If it is that big, maybe use a NN?
    data = read_data("transaction_features").toPandas()
    for col_name in ["enc_category", "enc_payment_type"]:
        data = get_nested_column_extended(data, col_name)

    model = Model()
    model.train_model(data)
    print(model.get_cv_scores(data))
    # note: Here is the main change! We will log our model to MLFlow. Which is basically "storing" it there.
    model.log_model_to_mlflow()


if __name__ == "__main__":  # pragma: no cover
    main()
