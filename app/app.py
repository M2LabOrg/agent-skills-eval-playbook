"""Toy Flask service exposing the turbine monitoring functions in
turbine_monitor.py. This app is intentionally minimal — its purpose is to
give the python-code-review skill (see .agents/skills/python-code-review/)
real files to review, not to be a production monitoring system.
"""
from flask import Flask, request, jsonify

from turbine_monitor import compute_average_power, flag_anomalies, classify_condition

app = Flask(__name__)


@app.route("/readings/summary", methods=["POST"])
def readings_summary():
    """Accept a batch of turbine sensor readings and return average power
    output plus any anomalies against safe operating thresholds."""
    readings = request.get_json(force=True).get("readings", [])
    avg_power = compute_average_power(readings)
    anomalies = flag_anomalies(readings)
    return jsonify({"average_power_kw": avg_power, "anomalies": anomalies})


@app.route("/readings/condition", methods=["POST"])
def readings_condition():
    """Classify a single vibration reading as nominal, watch, or alarm."""
    vibration = request.get_json(force=True).get("vibration_mm_s")
    return jsonify({"condition": classify_condition(vibration)})


if __name__ == "__main__":
    app.run(debug=True)
