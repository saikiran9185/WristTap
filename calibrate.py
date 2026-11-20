"""Spoken calibration: learns how the band is actually worn, saves calib.json.

Run while the demo reader is running (./demo.sh --ble --no-open, or USB):
    ~/Projects/PhoneStereo/.venv/bin/python calibrate.py          # everything
    ... calibrate.py discs | arm | mouse                           # one part

discs : which disc sits on top / palm side / thumb side / little-finger side
arm   : for each motion sensor, which axis is roll and which is up/down, the signs, and the level pose
mouse : which turning axis moves the cursor right and up
"""
import json
import subprocess
import sys
import threading
import time
import urllib.request

URL = "http://localhost:8791"
frames = []
lock = threading.Lock()


def reader():
    with urllib.request.urlopen(URL + "/stream", timeout=120) as r:
        for line in r:
            if line.startswith(b"data:"):
                m = json.loads(line[5:])
                if "imu" in m:
                    m["_t"] = time.time()
                    with lock:
                        frames.append(m)
                        del frames[:-3000]


def say(text, wait=True):
    print(">>", text, flush=True)
    (subprocess.run if wait else subprocess.Popen)(["say", text])


def capture(sec):
    t0 = time.time()
    time.sleep(sec)
    with lock:
        return [f for f in frames if f["_t"] >= t0]


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def angles(fr, k):
    ok = [f["imu"][k] for f in fr if f["imu"][k]["ok"]]
    return {a: mean([o[a] for o in ok]) for a in ("roll", "pitch", "yaw")}, len(ok)


def post(obj):
    req = urllib.request.Request(URL + "/calib", data=json.dumps(obj).encode(), method="POST")
    return json.load(urllib.request.urlopen(req))


# ---------------- discs ----------------
PLACES = [("top", "the disc on TOP of your wrist, the back of the wrist"),
          ("palm", "the disc UNDER your wrist, on the palm side"),
          ("thumb", "the disc on the THUMB side"),
          ("pinky", "the disc on the LITTLE FINGER side")]


def cal_discs():
    found = {}
    for place, words in PLACES:
        for attempt in range(3):
            say(f"Tap {words}. Tap it three times, firmly.")
            fr = capture(4)
            score = [0, 0, 0, 0]
            for f in fr:
                for ev in f.get("events", []):
                    if ev.get("disc") is not None:
                        score[ev["disc"]] += 1
            best = max(range(4), key=lambda k: score[k])
            if score[best] >= 1 and score[best] >= 2 * sorted(score)[-2]:
                found[place] = best
                print(f"   {place}: disc P{best}   (taps seen per disc: {score})")
                say(f"Got it. That is P {best}.")
                break
            say("I could not tell which disc that was. Again, a bit harder.")
            print(f"   unclear, taps seen per disc: {score}")
    if len(set(found.values())) < len(found):
        say("Two places gave the same disc. Check the result on screen.")
        print("   WARNING: same disc for two places:", found)
    return found


# ---------------- arm (both motion sensors) ----------------
def hold(text, sec=3):
    say(text)
    time.sleep(1.5)                 # time to get into the pose
    say("Hold still.", wait=False)
    return capture(sec)


def axis_change(base, now, exclude=None):
    """Which of roll/pitch changed most, and in which direction."""
    cands = [a for a in ("roll", "pitch") if a != exclude]
    d = {a: now[a] - base[a] for a in cands}
    a = max(d, key=lambda k: abs(d[k]))
    return a, (1 if d[a] > 0 else -1), d


def cal_arm():
    out = [{}, {}]
    fr = hold("Put your forearm flat on the table, palm down, hand straight and relaxed.")
    base = [angles(fr, 0)[0], angles(fr, 1)[0]]
    n = [angles(fr, 0)[1], angles(fr, 1)[1]]
    for k in (0, 1):
        if n[k] == 0:
            say(f"Motion sensor {k + 1} is not sending. Fix it, then run the arm part again.")
            return None
    print(f"   level pose: forearm {base[0]}, hand {base[1]}")

    fr = hold("Now turn your palm UP, all the way, and keep it there.")
    up = [angles(fr, 0)[0], angles(fr, 1)[0]]
    roll_src = []
    for k in (0, 1):
        a, sgn, d = axis_change(base[k], up[k])
        out[k]["roll"] = {"src": a, "sign": sgn, "zero": round(base[k][a], 1)}
        roll_src.append(a)
        print(f"   sensor {k + 1} roll  = {'+' if sgn > 0 else '-'}{a}   (change {d})")

    fr = hold("Palm down again, flat. Now bend only your WRIST, so the hand points UP. Keep the forearm on the table.")
    bent = angles(fr, 1)[0]
    a, sgn, d = axis_change(base[1], bent, exclude=roll_src[1])
    out[1]["pitch"] = {"src": a, "sign": sgn, "zero": round(base[1][a], 1)}
    print(f"   sensor 2 up/down = {'+' if sgn > 0 else '-'}{a}   (change {d})")

    fr = hold("Hand straight again. Now LIFT your forearm up from the elbow, keeping the elbow on the table.")
    lift = angles(fr, 0)[0]
    a, sgn, d = axis_change(base[0], lift, exclude=roll_src[0])
    out[0]["pitch"] = {"src": a, "sign": sgn, "zero": round(base[0][a], 1)}
    print(f"   sensor 1 up/down = {'+' if sgn > 0 else '-'}{a}   (change {d})")

    say("Forearm flat again. Get ready to slide your whole arm to the RIGHT along the table.")
    time.sleep(1)
    with lock:
        y0 = [mean([f["imu"][k]["yaw"] for f in frames[-20:] if f["imu"][k]["ok"]]) for k in (0, 1)]
    say("Slide right now, slowly, and stop.", wait=False)
    fr = capture(3)
    for k in (0, 1):
        dy = mean([f["imu"][k]["yaw"] for f in fr[-15:] if f["imu"][k]["ok"]]) - y0[k]
        out[k]["yaw"] = {"sign": 1 if dy > 0 else -1}
        print(f"   sensor {k + 1} swing right = {'+' if dy > 0 else '-'}yaw   (change {dy:.1f})")
    return out


# ---------------- air mouse ----------------
def dominant(fr, k):
    g = [f["gyro"][k] for f in fr if f.get("gyro") and f["gyro"][k]]
    if not g:
        return None, 0, [0, 0, 0]
    tot = [sum(v[i] for v in g) for i in range(3)]
    i = max(range(3), key=lambda j: abs(tot[j]))
    return "g" + "xyz"[i], (1 if tot[i] > 0 else -1), tot


def cal_mouse():
    say("Air mouse. Hold your hand in the air like holding a mouse.")
    time.sleep(1.5)
    # one move and hold (no return), so the summed turning speed keeps its sign
    say("Turn your hand to the RIGHT, like moving a mouse right, and stop there.", wait=False)
    fr = capture(3)
    ax, sgn, tot = dominant(fr, 1)
    say("Back to the middle.")
    time.sleep(1.5)
    say("Now tilt your hand UP, and stop there.", wait=False)
    fr2 = capture(3)
    ay, sgy, toty = dominant(fr2, 1)
    if not ax or not ay:
        say("No hand motion data. Is motion sensor 2 working?")
        return None
    if ay == ax:  # must be different axes
        _, _, t2 = dominant(fr2, 1)
        order = sorted(range(3), key=lambda j: -abs(t2[j]))
        ay = "g" + "xyz"[next(j for j in order if "g" + "xyz"[j] != ax)]
    m = {"mx": ax, "mx_sign": sgn, "my": ay, "my_sign": -sgy}   # screen y grows downward
    print(f"   cursor right = {'+' if sgn > 0 else '-'}{ax}, cursor up = {'+' if sgy > 0 else '-'}{ay}  ({tot}, {toty})")
    return m


def main():
    parts = sys.argv[1:] or ["discs", "arm", "mouse"]
    threading.Thread(target=reader, daemon=True).start()
    time.sleep(1.5)
    with lock:
        if not frames:
            sys.exit("No data from the demo reader. Start it first: ./demo.sh --ble --no-open")
    say("Calibration. Wear the band and sit at the table.")
    res = {}
    if "discs" in parts:
        d = cal_discs()
        if d:
            res["discs"] = d
    if "arm" in parts:
        a = cal_arm()
        if a:
            res["imu"] = a
    if "mouse" in parts:
        m = cal_mouse()
        if m:
            res["mouse"] = m
    if res:
        saved = post(res)
        print("\nSaved calib.json:\n" + json.dumps(saved, indent=2))
        say("Calibration saved. Refresh the demo page.")


if __name__ == "__main__":
    main()
