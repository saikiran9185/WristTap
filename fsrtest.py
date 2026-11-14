"""Spoken press test for both FSRs: "Let go" / "Press sensor N". Usage: python fsrtest.py [rounds]"""
import subprocess, sys, time, statistics
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from wristtap import Band, find_port
ROUNDS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
def say(t):
    print(f"[{time.strftime('%H:%M:%S')}] {t}", flush=True); subprocess.Popen(["say", "-r", "200", t])
band = Band(find_port()); time.sleep(1.0)
win = []
say("Get ready. Hands off the sensors."); time.sleep(3)
for r in range(ROUNDS):
    for k in range(2):
        for kind in ("REST", "PRESS"):
            say(f"Press sensor {k}, hold it" if kind == "PRESS" else "Let go")
            a = time.time() + 1.5; time.sleep(4.0); win.append((k, kind, a, time.time()))
say("Done"); time.sleep(0.3)
rows, off = band.snapshot(), band.offset; band.close()
print("\nMedian reading of each FSR per window (rest should be ~0, pressed 1000-4000):\n")
print("                     FSR0   FSR1")
for k, kind, a, b in win:
    v = [[row[17 + c] for row in rows if a <= row[0] + off <= b] or [0] for c in range(2)]
    label = f"PRESS sensor {k}" if kind == "PRESS" else "REST"
    print(f"  {label:<17}" + "".join(f"{statistics.median(x):>7.0f}" for x in v))
