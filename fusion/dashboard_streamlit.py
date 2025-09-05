# fusion/dashboard_streamlit.py
import streamlit as st
import time, json, os
from PIL import Image
import pandas as pd

st.set_page_config(layout="wide", page_title="Microplastics Detector Dashboard")
st.title("Microplastics Detector — Live Dashboard")

# file paths
FRAME_PATH = "fusion/latest_frame.jpg"
ARDUINO_JSON = "fusion/arduino_data.json"
METRICS_JSON = "fusion/latest_metrics.json"

col1, col2 = st.columns([2,1])

with col1:
    st.subheader("Live Camera Feed (with detection)")
    img_slot = st.empty()
    st.subheader("Optical Particle Count (recent)")
    opt_chart = st.line_chart([], height=200)

with col2:
    st.subheader("Electrode Resistance (recent)")
    elec_chart = st.line_chart([], height=200)
    st.subheader("Fused Estimation")
    metrics_box = st.empty()
    st.write(" ")

# histories
opt_hist = []
elec_hist = []
time_hist = []

def load_arduino_json():
    if not os.path.exists(ARDUINO_JSON):
        return None
    try:
        with open(ARDUINO_JSON,'r') as f:
            return json.load(f)
    except:
        return None

def load_metrics():
    if not os.path.exists(METRICS_JSON):
        return None
    try:
        with open(METRICS_JSON,'r') as f:
            return json.load(f)
    except:
        return None

while True:
    # update frame
    if os.path.exists(FRAME_PATH):
        try:
            img = Image.open(FRAME_PATH)
            img_slot.image(img, use_column_width=True)
        except:
            pass

    data = load_arduino_json()
    metrics = load_metrics()
    if data:
        elec = data.get('elec', [])
        t = data.get('t', [])
        # take last 200
        if elec:
            elec_hist = elec[-200:]
            time_hist = t[-200:]
            elec_chart.add_rows(pd.DataFrame({"Electrode": elec_hist}))
    if metrics:
        # optical count is provided by fusion engine
        combined = metrics.get("combined_particles_est", 0)
        density = metrics.get("density_particles_per_ml", 0)
        metrics_box.metric("Estimated particles (total)", f"{combined:.1f}")
        metrics_box.metric("Density (particles/ml)", f"{density:.4f}")

    # Sleep little
    time.sleep(0.6)
