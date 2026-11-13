import pandas as pd

model_path = "model.pkl"
data_path = "data.json"

import pickle

with open(model_path, "rb") as file:
    model = pickle.load(file)

data = pd.read_json(data_path)
out = model.predict(data)
print(out)

