import cv2
import numpy as np
import time
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--stream", type=str, default="http://192.168.3.104:8080/video")
parser.add_argument("--save_frame", type=str, default="../fusion/latest_frame.jpg")
parser.add_argument("--min_area", type=int, default=60)
parser.add_argument("--max_area", type=int, default=5000)
args = parser.parse_args()

STREAM_URL = args.stream
SAVE_PATH = os.path.join(os.path.dirname(__file__), args.save_frame)
MIN_AREA = args.min_area
MAX_AREA = args.max_area

cap = cv2.VideoCapture(STREAM_URL)  # or 0 for local webcam

if not cap.isOpened():
    print("Failed to open stream. Try phone camera or webcam. URL:", STREAM_URL)
    exit(1)

# simple background subtractor to resist light flicker
bs = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50, detectShadows=False)

particle_counts = []

while True:
    ret, frame = cap.read()
    if not ret:
        print("Frame not received; retrying...")
        time.sleep(0.5)
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (7,7), 0)
    fg = bs.apply(blur)

    # threshold and morphological clean-up
    _, th = cv2.threshold(fg, 127, 255, cv2.THRESH_BINARY)
    kernel = np.ones((3,3), np.uint8)
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    blobs = []
    for c in contours:
        area = cv2.contourArea(c)
        if MIN_AREA <= area <= MAX_AREA:
            x,y,w,h = cv2.boundingRect(c)
            blobs.append((x,y,w,h,area))
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

    count = len(blobs)
    particle_counts.append(count)
    if len(particle_counts) > 300:
        particle_counts.pop(0)

    # overlay
    cv2.putText(frame, f"Particles: {count}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    # small graph of recent counts
    h,w,_ = frame.shape
    graph = np.zeros((100, w, 3), dtype=np.uint8)
    if len(particle_counts) > 1:
        maxc = max(1,max(particle_counts))
        pts = [(int(i* w/len(particle_counts)), 100 - int((c/maxc)*90)) for i,c in enumerate(particle_counts)]
        for i in range(1, len(pts)):
            cv2.line(graph, pts[i-1], pts[i], (255,255,255), 1)
    # stack graph under frame
    display = np.vstack((frame, graph))

    # save latest frame for dashboard
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    cv2.imwrite(SAVE_PATH, display)

    cv2.imshow("Optical Detection", display)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
