
import json, time, os
import numpy as np
from datetime import datetime

# Paths
ARDUINO_JSON = "fusion/arduino_data.json"
LAST_METRICS = "fusion/latest_metrics.json"
OPTICAL_COUNT_FILE = "fusion/optical_count.tmp" 

VOLUME_ML = 100.0   
SPIKE_THRESHOLD = 700  # threshold on elec reading to detect a spike (tune)
SPIKE_MIN_INTERVAL = 0.05  # seconds, debouncing spikes

last_spike_time = 0
last_elec = None
spike_count = 0

def estimate_optical_count():
    if os.path.exists(OPTICAL_COUNT_FILE):
        try:
            with open(OPTICAL_COUNT_FILE,'r') as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def read_arduino_json():
    if not os.path.exists(ARDUINO_JSON):
        return None
    with open(ARDUINO_JSON,'r') as f:
        return json.load(f)

def detect_spikes(elec_series, time_series):
    global last_spike_time
    spikes = 0
    if not elec_series:
        return 0
    for v,t in zip(elec_series, time_series):
        if v >= SPIKE_THRESHOLD:
            if (t - last_spike_time) > SPIKE_MIN_INTERVAL:
                spikes += 1
                last_spike_time = t
    return spikes

def compute_density(optical_count, spikes, volume_ml):
    w_opt = 0.65
    w_elec = 0.35
    combined = (w_opt*optical_count + w_elec*spikes)
    density = combined / volume_ml
    return combined, density

if __name__ == "__main__":
    os.makedirs("fusion", exist_ok=True)
    while True:
        data = read_arduino_json()
        optical_count = estimate_optical_count()
        spikes = 0
        if data:
            elec = data.get("elec", [])
            t = data.get("t", [])
            spikes = detect_spikes(elec, t)
        combined, density = compute_density(optical_count, spikes, VOLUME_ML)
        metrics = {
            "timestamp": datetime.utcnow().isoformat()+"Z",
            "optical_count": optical_count,
            "electrode_spikes": spikes,
            "combined_particles_est": combined,
            "density_particles_per_ml": density
        }
        with open(LAST_METRICS, "w") as f:
            json.dump(metrics, f)
        time.sleep(0.5)
