"""
app.py

Flask backend for the Brent oil price change point dashboard (Task 3).

Deliberately has NO PyMC/ArviZ dependency - all modeling happens in
notebooks/change_point_model.ipynb, which calls export_results_for_dashboard()
to write static files into data/processed/. This app just reads and serves
those files. That split matters: PyMC needs native compilation and can
take minutes to sample, which is not something an HTTP request should ever
trigger.

Run with: python app.py
Then: http://localhost:5000/api/prices
"""

from pathlib import Path
import json

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow the React frontend (different port) to call this API

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


def _load_json(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


@app.route("/api/prices")
def get_prices():
    """Historical price data, with optional date range filtering.

    Query params:
        start (YYYY-MM-DD, optional)
        end   (YYYY-MM-DD, optional)
    """
    path = DATA_DIR / "prices.csv"
    if not path.exists():
        return jsonify({"error": "prices.csv not found - run export_results_for_dashboard() first"}), 404

    df = pd.read_csv(path, parse_dates=["Date"])

    start = request.args.get("start")
    end = request.args.get("end")
    if start:
        df = df[df["Date"] >= pd.Timestamp(start)]
    if end:
        df = df[df["Date"] <= pd.Timestamp(end)]

    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    records = df.to_dict(orient="records")
    # NaN isn't valid JSON. pandas casts None back to NaN if replaced at the
    # DataFrame level (dtype preservation), so clean it up per-record instead.
    for record in records:
        for key, value in record.items():
            if isinstance(value, float) and pd.isna(value):
                record[key] = None
    return jsonify(records)


@app.route("/api/changepoints/global")
def get_global_changepoint():
    """The single global change-point model's result."""
    data = _load_json("global_changepoint.json")
    if data is None:
        return jsonify({"error": "global_changepoint.json not found"}), 404
    return jsonify(data)


@app.route("/api/changepoints/events")
def get_event_changepoints():
    """Per-event windowed change-point results (the summary table)."""
    data = _load_json("event_changepoints.json")
    if data is None:
        return jsonify({"error": "event_changepoints.json not found"}), 404
    return jsonify(data)


@app.route("/api/events")
def get_events():
    """The full researched events dataset (all 16 events, not just the 4 modeled)."""
    data = _load_json("events.json")
    if data is None:
        return jsonify({"error": "events.json not found"}), 404
    return jsonify(data)


@app.route("/api/volatility")
def get_volatility():
    """Log-return volatility (std dev) by time period - the 'performance
    metrics' / 'key indicators' data Task 3 asks the dashboard to display.
    """
    data = _load_json("volatility.json")
    if data is None:
        return jsonify({"error": "volatility.json not found"}), 404
    return jsonify(data)


@app.route("/api/health")
def health():
    """Quick check that the export files exist and this API is usable."""
    files = ["prices.csv", "global_changepoint.json", "event_changepoints.json", "events.json", "volatility.json"]
    status = {f: (DATA_DIR / f).exists() for f in files}
    return jsonify({"data_dir": str(DATA_DIR), "files": status})


if __name__ == "__main__":
    app.run(debug=True, port=5000)