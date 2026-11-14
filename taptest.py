"""Spoken tap test for one piezo: the Mac says "tap" / "stop", then compares tap windows with still windows.
Usage:  python taptest.py [piezo 0-3] [rounds]      (default piezo 0, 5 rounds)"""
import subprocess, sys, time
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from wristtap import Band, find_port

PZ = int(sys.argv[1]) if len(sys.argv) > 1 else 0
ROUNDS = int(sys.argv[2]) if len(sys.argv) > 2 else 5
WIN = 4.0          # seconds per window
COL = 13 + PZ      # row layout: esp_t, imu1*6, imu2*6, piezo*4, fsr*2, seq

def say(text):
    print(f"[{time.strftime('%H:%M:%S')}] {text}", flush=True)
    subprocess.Popen(["say", "-r", "200", text])

band = Band(find_port())
time.sleep(1.0)
windows = []
say("Get ready. Keep still.")
time.sleep(3)
for r in range(1, ROUNDS + 1):
    for kind in ("STILL", "TAP"):
        say("Tap tap tap" if kind == "TAP" else "Stop")
        t0 = time.time() + 1.5          # skip voice delay + reaction time
        time.sleep(WIN)
        windows.append((r, kind, t0, time.time()))
say("Done")
time.sleep(0.3)
rows = band.snapshot()
off = band.offset
band.close()

def peak_values(a, b):
    v = [row[COL] for row in rows if a <= row[0] + off <= b]
    return v

import statistics, csv
with open("taptest_last.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["mac_time", "piezo"])
    for row in rows: w.writerow([f"{row[0]+off:.4f}", row[COL]])
HIGH = 1000
print(f"\nPiezo {PZ}: counting readings above {HIGH} in each window (first 1.5 s skipped for reaction time)\n")
print(" round  window  highest  median  readings>1000")
res = {"STILL": [], "TAP": []}
for r, k, a, b in windows:
    v = peak_values(a, b) or [0]
    n = sum(x > HIGH for x in v)
    res[k].append(n)
    print(f"  {r:>3}   {k:<5}  {max(v):>7}  {statistics.median(v):>6.0f}  {n:>6}")
st, tp = statistics.median(res["STILL"]), statistics.median(res["TAP"])
print(f"\nTypical readings>1000:  STILL {st:.0f}   TAP {tp:.0f}")
if tp > max(3 * st, 5):
    print("VERDICT: real signal. Taps clearly stand out from rest.")
elif st > 5:
    print("VERDICT: noise. Big numbers appear even when still (loose contact or floating input).")
else:
    print("VERDICT: no signal. Taps are not getting through.")
