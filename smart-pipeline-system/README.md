# AquaSentinel: Smart Pipeline Leakage Detection and Prediction System

A Flask prototype for monitoring pipeline telemetry, detecting abnormal conditions, estimating leakage risk, and simulating automatic emergency response. This is a research/demo implementation. It does not claim patent status, complete novelty, or 100% prediction accuracy.

## Stack

- Frontend: HTML5, CSS3, JavaScript, Bootstrap, Chart.js
- Backend: Python and Flask
- Storage: SQLite for runtime readings plus CSV export
- AI/ML path: Pandas, NumPy, scikit-learn Random Forest training script
- Hardware-ready input: ESP32 REST endpoint

## Run in VS Code

Open the project folder in VS Code, then run these commands in the integrated terminal:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python ml\train_model.py
python app.py
```

Open http://127.0.0.1:5000. The first page is a presentation landing screen; select **Open command center** to use the dashboard.

If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process Bypass` for the current terminal, or run `.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.venv\Scripts\python.exe app.py` without activating.

## Prototype workflow

1. Choose Normal condition, Small leakage, Major leakage, or High risk in the dashboard.
2. The backend generates realistic sensor values, stores the reading in SQLite/CSV, classifies the state, calculates risk and PHI, and returns a JSON result.
3. The dashboard, live monitoring route, charts, alert center, and history table update from that result.
4. Major leakage and high-risk conditions simulate a closed solenoid valve and stopped water supply.
5. Use Download CSV to export the current monitoring report.

## REST API for ESP32

Send JSON to `POST /api/sensor-data`:

```json
{
  "pressure": 5.4,
  "flow": 43.2,
  "vibration": 0.22,
  "water_level": 77.5,
  "timestamp": "2026-09-13T08:40:00+00:00"
}
```

Example ESP32 request shape:

```cpp
HTTPClient http;
http.begin("http://YOUR_COMPUTER_IP:5000/api/sensor-data");
http.addHeader("Content-Type", "application/json");
String body = "{\"pressure\":5.4,\"flow\":43.2,\"vibration\":0.22,\"water_level\":77.5}";
int status = http.POST(body);
http.end();
```

For hardware testing, run Flask on the local network with `app.run(host="0.0.0.0", port=5000)` and use the host computer's LAN IP. Add authentication, TLS, validation and rate limiting before connecting a real actuator or public network.

## Project map

- `app.py`: Flask routes, simulation profiles, rule-based prototype scoring, SQLite persistence and REST ingestion.
- `templates/`: dashboard, live monitoring, alerts, history, analysis and innovation views.
- `static/css/style.css`: responsive SIH presentation styling.
- `static/js/script.js`: API calls, simulation controls, charts and tables.
- `ml/train_model.py`: trains and saves `models/leakage_model.pkl` from CSV history.
- `ml/predict.py`: reusable Random Forest inference helper.
- `data/sensor_data.csv`: small seed dataset and export target.

## Architecture

Sensors -> ESP32 -> Flask data processing -> AI/ML analysis -> leakage risk prediction -> decision engine -> simulated valve response -> dashboard and alerts.

The baseline risk calculation is intentionally transparent so judges can understand the demo. A production system would require calibrated sensor data, time-series feature engineering, validation against labeled leakage events, secure device identity, and hardware safety review.
