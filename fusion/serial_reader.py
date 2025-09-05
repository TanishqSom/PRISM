# fusion/serial_reader.py
import serial, time, threading, json, os
from collections import deque

SERIAL_PORT = "COM3"   # Windows: COM3, Linux: /dev/ttyUSB0, Mac: /dev/tty.usbserial-XXXX
BAUD = 115200
OUT_JSON = "fusion/arduino_data.json"

# Use deque to keep last N samples
MAXLEN = 1000
ldr_buf = deque(maxlen=MAXLEN)
elec_buf = deque(maxlen=MAXLEN)
t_buf = deque(maxlen=MAXLEN)

def read_serial():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
        time.sleep(2)
        print("Serial opened on", SERIAL_PORT)
    except Exception as e:
        print("Failed to open serial:", e)
        return

    while True:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            if "ARDUINO_READY" in line:
                continue
            parts = line.split(",")
            if len(parts) >= 2:
                ldr = int(parts[0])
                elec = int(parts[1])
                ts = time.time()
                ldr_buf.append(ldr)
                elec_buf.append(elec)
                t_buf.append(ts)
                # write JSON file for other processes
                payload = {"t": list(t_buf)[-200:], "ldr": list(ldr_buf)[-200:], "elec": list(elec_buf)[-200:]}
                with open(OUT_JSON, "w") as f:
                    json.dump(payload, f)
        except Exception as e:
            print("Serial read error:", e)
            time.sleep(0.1)

if __name__ == "__main__":
    # create folder
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    read_serial()
