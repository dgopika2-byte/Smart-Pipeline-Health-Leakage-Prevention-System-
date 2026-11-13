from pathlib import Path
import joblib
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "leakage_model.pkl"

def predict_leakage(pressure, flow, vibration, water_level):
    bundle = joblib.load(MODEL_PATH)
    frame = pd.DataFrame([[pressure, flow, vibration, water_level]], columns=bundle["features"])
    probability = float(bundle["model"].predict_proba(frame)[0][1])
    label = "High Leakage Risk" if probability >= 0.61 else "Possible Leakage" if probability >= 0.31 else "Normal"
    return {"label": label, "risk": round(probability * 100)}
