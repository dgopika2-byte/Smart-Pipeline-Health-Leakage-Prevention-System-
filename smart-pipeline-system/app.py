from datetime import datetime, timedelta
import csv
import json
import os
import random
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "pipeline.db"
CSV_PATH = DATA_DIR / "sensor_data.csv"

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

SIMULATION_PROFILES = {
    "normal": {"pressure": 5.8, "flow": 42.0, "vibration": 0.18, "water_level": 78.0},
    "small": {"pressure": 4.1, "flow": 50.0, "vibration": 0.68, "water_level": 71.0},
    "major": {"pressure": 2.2, "flow": 64.0, "vibration": 1.35, "water_level": 58.0},
    "high": {"pressure": 2.8, "flow": 61.0, "vibration": 1.2, "water_level": 61.0},
}


def ensure_data_store():
    DATA_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                pressure REAL NOT NULL,
                flow REAL NOT NULL,
                vibration REAL NOT NULL,
                water_level REAL NOT NULL,
                risk REAL NOT NULL,
                status TEXT NOT NULL,
                ai_result TEXT NOT NULL,
                action TEXT NOT NULL
            )"""
        )
        connection.commit()
    if not CSV_PATH.exists():
        CSV_PATH.write_text("timestamp,pressure,flow,vibration,water_level,risk,status\n", encoding="utf-8")
    with sqlite3.connect(DB_PATH) as connection:
        has_readings = connection.execute("SELECT EXISTS(SELECT 1 FROM readings)").fetchone()[0]
        if not has_readings and CSV_PATH.stat().st_size > 0:
            with CSV_PATH.open(newline="", encoding="utf-8") as file:
                for row in csv.DictReader(file):
                    if not row.get("timestamp"):
                        continue
                    pressure, flow = float(row["pressure"]), float(row["flow"])
                    vibration, water_level = float(row["vibration"]), float(row["water_level"])
                    risk, status, ai_result, action, _ = classify_reading(pressure, flow, vibration, water_level)
                    connection.execute("INSERT INTO readings (timestamp, pressure, flow, vibration, water_level, risk, status, ai_result, action) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                       (row["timestamp"], pressure, flow, vibration, water_level, float(row.get("risk", risk)), row.get("status", status), ai_result, action))
            connection.commit()


def classify_reading(pressure, flow, vibration, water_level):
    pressure_signal = max(0, min(1, (5.8 - pressure) / 4.2))
    flow_signal = max(0, min(1, abs(flow - 42) / 35))
    vibration_signal = max(0, min(1, vibration / 1.8))
    level_signal = max(0, min(1, (78 - water_level) / 45))
    risk = round(min(100, (pressure_signal * 0.38 + flow_signal * 0.22 + vibration_signal * 0.25 + level_signal * 0.15) * 100))
    if risk >= 81:
        status, ai_result, action = "CRITICAL", "High Leakage Risk", "Solenoid valve closed; water supply stopped"
    elif risk >= 61:
        status, ai_result, action = "LEAK DETECTED", "Possible Leakage", "Emergency response activated; valve closed"
    elif risk >= 31:
        status, ai_result, action = "WARNING", "Abnormal", "Operator alert raised; monitoring intensified"
    else:
        status, ai_result, action = "NORMAL", "Normal", "No action required"
    phi = max(0, round(100 - risk * 0.72 - (8 if vibration > 1 else 0)))
    return risk, status, ai_result, action, phi


def make_reading(mode="normal"):
    profile = SIMULATION_PROFILES.get(mode, SIMULATION_PROFILES["normal"])
    pressure = round(random.gauss(profile["pressure"], 0.12), 2)
    flow = round(random.gauss(profile["flow"], 1.4), 2)
    vibration = round(max(0.03, random.gauss(profile["vibration"], 0.05)), 2)
    water_level = round(max(5, min(100, random.gauss(profile["water_level"], 1.2))), 2)
    risk, status, ai_result, action, phi = classify_reading(pressure, flow, vibration, water_level)
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    return {"timestamp": timestamp, "pressure": pressure, "flow": flow, "vibration": vibration, "water_level": water_level,
            "risk": risk, "status": status, "ai_result": ai_result, "action": action, "phi": phi,
            "valve": "CLOSED" if risk >= 61 else "OPEN", "mode": mode}


def save_reading(reading):
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("INSERT INTO readings (timestamp, pressure, flow, vibration, water_level, risk, status, ai_result, action) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (reading["timestamp"], reading["pressure"], reading["flow"], reading["vibration"], reading["water_level"], reading["risk"], reading["status"], reading["ai_result"], reading["action"]))
        connection.commit()
    write_header = not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0
    with CSV_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["timestamp", "pressure", "flow", "vibration", "water_level", "risk", "status"])
        if write_header:
            writer.writeheader()
        writer.writerow({key: reading[key] for key in writer.fieldnames})


def recent_readings(limit=40):
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("SELECT * FROM readings ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in reversed(rows)]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/monitoring")
def monitoring():
    return render_template("monitoring.html")


@app.route("/alerts")
def alerts():
    return render_template("alerts.html")


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/analysis")
def analysis():
    return render_template("analysis.html")


@app.route("/innovation")
def innovation():
    return render_template("innovation.html")


@app.get("/api/state")
def state():
    readings = recent_readings()
    current = readings[-1] if readings else make_reading()
    return jsonify({"current": current, "readings": readings, "updated": current["timestamp"]})


@app.post("/api/simulate")
def simulate():
    payload = request.get_json(silent=True) or {}
    reading = make_reading(payload.get("mode", "normal"))
    save_reading(reading)
    return jsonify(reading)


@app.post("/api/sensor-data")
def sensor_data():
    payload = request.get_json(silent=True) or {}
    required = ["pressure", "flow", "vibration", "water_level"]
    if any(field not in payload for field in required):
        return jsonify({"error": "pressure, flow, vibration, and water_level are required"}), 400
    pressure, flow = float(payload["pressure"]), float(payload["flow"])
    vibration, water_level = float(payload["vibration"]), float(payload["water_level"])
    risk, status, ai_result, action, phi = classify_reading(pressure, flow, vibration, water_level)
    reading = {"timestamp": payload.get("timestamp", datetime.now().astimezone().isoformat(timespec="seconds")), "pressure": pressure, "flow": flow, "vibration": vibration, "water_level": water_level, "risk": risk, "status": status, "ai_result": ai_result, "action": action, "phi": phi, "valve": "CLOSED" if risk >= 61 else "OPEN", "mode": "esp32"}
    save_reading(reading)
    return jsonify(reading), 201


@app.get("/api/report")
def report():
    readings = recent_readings(200)
    current = readings[-1] if readings else make_reading()
    return jsonify({"generated_at": datetime.now().astimezone().isoformat(timespec="seconds"), "current": current, "readings": readings, "events": [row for row in readings if row["status"] != "NORMAL"]})


@app.get("/report/download")
def download_report():
    return send_file(CSV_PATH, as_attachment=True, download_name="pipeline-monitoring-report.csv")


if __name__ == "__main__":
    ensure_data_store()
    app.run(debug=True, host="127.0.0.1", port=5000)
else:
    ensure_data_store()
