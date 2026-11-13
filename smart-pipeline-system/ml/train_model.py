from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "sensor_data.csv")
df["leakage"] = (df["risk"] >= 61).astype(int)
features = ["pressure", "flow", "vibration", "water_level"]
model = RandomForestClassifier(n_estimators=80, random_state=42, class_weight="balanced")
model.fit(df[features], df["leakage"])
model_path = ROOT / "models" / "leakage_model.pkl"
model_path.parent.mkdir(exist_ok=True)
joblib.dump({"model": model, "features": features}, model_path)
print(f"Saved model to {model_path}")
