"""Spoken tap test for all 4 piezos in one run: "Stop" / "Tap disc N", then a table per disc.
Usage:  python taptest_all.py [rounds]   (default 2)"""
import subprocess, sys, time, statistics, csv
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from wristtap import Band, find_port

ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
WIN, HIGH, SKIP = 4.0, 1000, 1.0

def say(text):
    print(f"[{time.strftime('%H:%M:%S')}] {text}", flush=True)
    subprocess.Popen(["say", "-r", "200", text])

band = Band(find_port()); time.sleep(1.0)
win = []
say("Get ready. Keep still."); time.sleep(3)
for r in range(1, ROUNDS + 1):
    for pz in range(4):
        for kind in ("STILL", "TAP"):
            say(f"Tap disc {pz}" if kind == "TAP" else "Stop")
            a = time.time() + SKIP; time.sleep(WIN)
            win.append((pz, kind, a, time.time() + 1.0))   # +1 s: taps that run late after "Stop"
say("Done"); time.sleep(0.3)
rows, off = band.snapshot(), band.offset
band.close()
with open("taptest_all_last.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["mac_time", "p0", "p1", "p2", "p3"])
    for row in rows: w.writerow([f"{row[0]+off:.4f}"] + list(row[13:17]))

def count(col, a, b):
    v = [row[13 + col] for row in rows if a <= row[0] + off <= b] or [0]
    return sum(x > HIGH for x in v), max(v), statistics.median(v)

print(f"\nReadings above {HIGH} on each disc, per window. The disc being tapped should light up; the others stay low.\n")
print("                    disc0  disc1  disc2  disc3")
for pz, k, a, b in win:
    if k == "STILL": a, b = a, b - 1.0      # still windows: no late-tap extension
    cells = [count(c, a, b)[0] for c in range(4)]
    label = f"TAP disc {pz}" if k == "TAP" else "STILL"
    print(f"  {label:<16}" + "".join(f"{n:>7}" for n in cells))
print("\nStill median (should be low and steady):", "  ".join(
    f"disc{c} {statistics.median([row[13+c] for row in rows]):.0f}" for c in range(4)))
