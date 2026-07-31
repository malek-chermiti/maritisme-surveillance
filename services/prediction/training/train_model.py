import pandas as pd
import pickle
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

FEATURE_COLUMNS = [
    "lat_t", "lon_t", "speed_t", "heading_t",
    "lat_t5", "lon_t5", "speed_t5", "heading_t5",
    "lat_t10", "lon_t10", "speed_t10", "heading_t10"
]
TARGET_COLUMNS = ["label_lat_t30", "label_lon_t30", "label_anomaly_score"]

df = pd.read_csv("dataset_training.csv")

X = df[FEATURE_COLUMNS]
y = df[TARGET_COLUMNS]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred, multioutput="raw_values")
print("MAE par sortie :")
print(f"  lat_t30      : {mae[0]:.6f}")
print(f"  lon_t30      : {mae[1]:.6f}")
print(f"  anomaly_score: {mae[2]:.4f}")

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Modèle sauvegardé : model.pkl")