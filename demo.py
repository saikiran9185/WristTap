"""WristTap live demo: 3D forearm + hand, taps, squeezes, simple gestures and an air mouse.

  ./demo.sh            # band on USB
  ./demo.sh --ble      # band over Bluetooth (power bank, no cable)
  ./demo.sh --wifi     # band over Wi-Fi (Mac on the same network as the band)
  ./demo.sh --sim      # fake band, to rehearse Show mode without wearing it

Press S on the page (or the Show button) for the guided recording mode.

Opens http://localhost:8791 in Safari. The air mouse needs Accessibility permission for your
terminal app (System Settings > Privacy & Security > Accessibility) the first time.
"""
import argparse
import json
import math
import os
import queue
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

import wristtap

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8791
ACC = 4096.0      # LSB per g   (+-8 g)
GYR = 32.8        # LSB per dps (+-1000 dps)

settings = {      # changed live from the page
    "mouse": False, "sens": 14.0, "dead": 4.0,
    "mx": "gz", "my": "gy", "mx_sign": -1, "my_sign": -1, "imu": 2,
    "tap_thr": 150, "fsr_thr": 900, "flick_dps": 260,
    # false-trigger filters (tuned on the /config page; 0 = off)
    "tap_thr_d": [150, 150, 150, 150],   # per-disc tap threshold
    "one_disc": True,                    # one tap = one disc: only the strongest disc in a moment counts
    "bump_discs": 3,                     # this many discs spiking together = a bump, not a tap
    "echo_ms": 120,                      # after a tap, other discs are ignored this long
    "tap_motion_dps": 0.0,               # ignore taps while the hand turns faster than this
    "tap_lock_ms": 0,                    # ignore taps this long after a flick or squeeze
    "flick_lock_ms": 300,                # ignore flicks this long after a tap
    "fsr_thr_d": [900, 900],             # per-FSR squeeze threshold
    "fsr_hyst": 0.7,                     # squeeze ends below threshold x this (stops flicker)
    "double_ms": 400,
    "return_ms": 700,                    # after a flick/roll, the opposite direction is the hand coming back: ignored this long
    "rearm": 0.35,                       # a new flick needs the hand to slow below this share of flick strength first
    "smooth_hz": 1.2,                    # angle smoothing when still (lower = smoother); fast moves stay instant
    "roll_sign": 1,                      # learned on /config: + = wrist roll to the right (clockwise)
    "mode": "demo",                      # demo = show only | present = slides | ui = control real apps
}
CALIB = os.path.join(HERE, "calib.json")    # written by calibrate.py: disc places, IMU axes/signs/zeros, mouse axes
REC = {"proc": None, "file": None, "t0": 0.0}     # full-screen recording (screencapture -v), started from the pages
clients = []
clients_lock = threading.Lock()


class Imu:
    """Tilt from gravity (roll/pitch) + gyro-integrated yaw (bias learned while still)."""

    def __init__(self):
        self.roll = self.pitch = self.yaw = 0.0
        self.bias = np.zeros(3)
        self.still_n = 0
        self.ok = False

    def update(self, m, dt):
        if not m.any():
            self.ok = False
            return
        self.ok = True
        a = m[:, :3].mean(0) / ACC
        g = m[:, 3:].mean(0) / GYR
        r = math.degrees(math.atan2(a[1], a[2]))
        p = math.degrees(math.atan2(-a[0], math.hypot(a[1], a[2])))
        k = 0.15                                   # complementary filter: gyro short-term, gravity long-term
        # blend on the short way round the circle: +179 and -179 are 2 degrees apart, not 358
        pred = self.roll + (g[0] - self.bias[0]) * dt
        self.roll = (pred + k * ((r - pred + 180) % 360 - 180) + 180) % 360 - 180
        self.pitch = (1 - k) * (self.pitch + (g[1] - self.bias[1]) * dt) + k * p
        if np.linalg.norm(g - self.bias) < 3:      # still: slowly learn the gyro bias
            self.bias = 0.98 * self.bias + 0.02 * g
        self.yaw += (g[2] - self.bias[2]) * dt
        self.yaw *= 0.999                          # gentle pull back to centre (no magnetometer)
        return g - self.bias


class OneEuro:
    """Adaptive smoothing: strong when the value is still, light when it moves fast (no lag on real motion).
    wrap=True treats the value as an angle in -180..180."""

    def __init__(self, wrap=False):
        self.x = self.dx = None
        self.wrap = wrap

    def __call__(self, x, dt, min_hz, beta=0.015, d_hz=1.0):
        if self.x is None or dt <= 0:
            self.x, self.dx = x, 0.0
            return x
        a = lambda hz: 1.0 / (1.0 + 1.0 / (2 * math.pi * hz * dt))
        d = x - self.x
        if self.wrap:
            d = (d + 180) % 360 - 180
        self.dx += a(d_hz) * (d / dt - self.dx)
        self.x += a(min_hz + beta * abs(self.dx)) * d
        if self.wrap:
            self.x = (self.x + 180) % 360 - 180
        return self.x


DRAG = {"on": False}


def mouse_move(dx, dy):
    import Quartz
    pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    b = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    x = min(max(pos.x + dx, 0), b.size.width - 1)
    y = min(max(pos.y + dy, 0), b.size.height - 1)
    kind = Quartz.kCGEventLeftMouseDragged if DRAG["on"] else Quartz.kCGEventMouseMoved
    ev = Quartz.CGEventCreateMouseEvent(None, kind, (x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)


def mouse_click(count=1):
    """count=2 marks the clicks as a double-click, so apps open/select as they would with a real mouse."""
    import Quartz
    pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    for n in range(1, count + 1):
        for t in (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp):
            ev = Quartz.CGEventCreateMouseEvent(None, t, pos, Quartz.kCGMouseButtonLeft)
            Quartz.CGEventSetIntegerValueField(ev, Quartz.kCGMouseEventClickState, n)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)


def mouse_button(down):
    """Squeeze-and-hold = press and hold the mouse button (drag)."""
    import Quartz
    pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    t = Quartz.kCGEventLeftMouseDown if down else Quartz.kCGEventLeftMouseUp
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateMouseEvent(None, t, pos, Quartz.kCGMouseButtonLeft))
    DRAG["on"] = down


def scroll(lines):
    import Quartz
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateScrollWheelEvent(None, Quartz.kCGScrollEventUnitLine, 1, int(lines)))


KEYS = {"right": 124, "left": 123, "b": 11, "space": 49}


def key(name):
    import Quartz
    for down in (True, False):
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateKeyboardEvent(None, KEYS[name], down))


def act(frame, what, fn, *a):
    """Run one OS action and report it (or the error, e.g. missing Accessibility permission)."""
    try:
        fn(*a)
        frame["events"].append({"kind": "action", "what": what})
    except Exception as e:
        frame["events"].append({"kind": "action error", "msg": str(e)[:120]})


class SimBand:
    """Fake band for rehearsing the demo/show mode without wearing anything (./demo.sh --sim)."""

    def __init__(self):
        self.rows = []
        self.lock = threading.Lock()
        self.status = "Simulated band (no hardware)"
        threading.Thread(target=self._run, daemon=True).start()

    @staticmethod
    def _imu(roll, pitch, droll, dpitch, dyaw):
        r, p = math.radians(roll), math.radians(pitch)
        a = [-math.sin(p), math.sin(r) * math.cos(p), math.cos(r) * math.cos(p)]
        return [int(v * ACC) for v in a] + [int(v * GYR) for v in (droll, dpitch, dyaw)]

    def _run(self):
        t0, seq, dt = time.time(), 0, 1 / 500
        while True:
            t = time.time() - t0
            r1, p1 = 30 * math.sin(0.5 * t), 18 * math.sin(0.31 * t)
            r2, p2 = r1 + 10 * math.sin(0.9 * t), p1 + 25 * math.sin(0.7 * t)
            dr1, dp1 = 15 * math.cos(0.5 * t), 5.6 * math.cos(0.31 * t)
            dr2, dp2 = dr1 + 9 * math.cos(0.9 * t), dp1 + 17.5 * math.cos(0.7 * t)
            yaw = 20 * math.cos(0.23 * t)
            if t % 9 < 0.05:                        # a flick every 9 s
                yaw += 420 if int(t / 9) % 2 else -420
            pz = [0, 0, 0, 0]
            if t % 2.5 < 0.02:                      # a tap every 2.5 s, discs in turn
                pz[int(t / 2.5) % 4] = 900
            fsr = [0, 0]
            if t % 7 < 0.8:                         # a squeeze every 7 s
                fsr[int(t / 7) % 2] = 2200
            row = (t,) + tuple(self._imu(r1, p1, dr1, dp1, yaw)) + tuple(self._imu(r2, p2, dr2, dp2, yaw)) \
                + tuple(pz) + tuple(fsr) + (seq & 0xFFFF,)
            with self.lock:
                self.rows.append(row)
                if len(self.rows) > 200000:
                    del self.rows[:100000]
            seq += 1
            time.sleep(dt)

    def close(self):
        pass


def broadcast(obj):
    data = ("data: " + json.dumps(obj) + "\n\n").encode()
    with clients_lock:
        for q in list(clients):
            try:
                q.put_nowait(data)
            except queue.Full:
                pass


def engine(band):
    imus = [Imu(), Imu()]
    n_seen = 0
    last_tap = [0.0] * 4
    last_flick = 0.0
    last_squeeze = 0.0
    smo = [[OneEuro(True), OneEuro(True), OneEuro(True)] for _ in range(2)]
    flick_armed = True
    last_kind, last_ax = "", -1
    fsr_on = [False, False]
    taps_recent = []
    t_prev = time.time()
    last_new = 0.0
    while True:
        time.sleep(1 / 40)
        now = time.time()
        dt = now - t_prev
        t_prev = now
        with band.lock:                       # copy only what's new (the list can hold 200k rows)
            total = len(band.rows)
            if total < n_seen:                # the reader trimmed old rows
                n_seen = max(0, total - 20)
            new = band.rows[n_seen:]
            rows = band.rows[-600:]
        n_seen = total
        frame = {"status": band.status, "rate": 0, "events": [], "mouse": settings["mouse"], "rec": rec_state()}
        recent = [r for r in rows if r[0] >= rows[-1][0] - 1.0] if rows else []
        frame["rate"] = len(recent)
        if not new:
            if now - last_new > 0.5:              # band unplugged / silent: say so
                frame["rate"] = 0
                frame["imu"] = [{"ok": False, "roll": 0, "pitch": 0, "yaw": 0}] * 2
            broadcast(frame)
            continue
        last_new = now
        arr = np.array([r[1:-1] for r in new], float)
        imu1, imu2, pz, fsr = arr[:, 0:6], arr[:, 6:12], arr[:, 12:16], arr[:, 16:18]
        g1 = imus[0].update(imu1, dt)
        g2 = imus[1].update(imu2, dt)
        frame["imu"] = [{"ok": i.ok,
                         "roll": round(smo[j][0](i.roll, dt, settings["smooth_hz"]), 2),
                         "pitch": round(smo[j][1](i.pitch, dt, settings["smooth_hz"]), 2),
                         "yaw": round(smo[j][2](i.yaw, dt, settings["smooth_hz"]), 2)} for j, i in enumerate(imus)]
        frame["bend"] = imus[1].pitch - imus[0].pitch if imus[0].ok and imus[1].ok else None
        frame["gyro"] = [[round(float(v), 1) for v in g] if g is not None else None for g in (g1, g2)]
        peaks = pz.max(0)
        frame["piezo"] = [int(v) for v in peaks]
        frame["fsr"] = [int(v) for v in fsr.mean(0)]

        gsrc = arr[:, 9:12] if imus[1].ok else arr[:, 3:6]
        gmax = float(np.abs(gsrc / GYR).max()) if len(gsrc) else 0.0
        frame["gmax"] = round(gmax)
        S = settings

        def reject(why, **kw):
            frame["events"].append({"kind": "ignored", "why": why, **kw})

        # ---- taps ----
        thr = np.array(S["tap_thr_d"], float)
        over = [k for k in range(4) if peaks[k] > thr[k]]
        if over:
            rel = peaks / thr
            if S["bump_discs"] and len(over) >= S["bump_discs"]:
                reject("bump: %d discs at once" % len(over), discs=over)
                over = []
            elif S["one_disc"] and len(over) > 1:
                best = max(over, key=lambda k: rel[k])
                for k in over:
                    if k != best:
                        reject("weaker than disc %d" % best, disc=k)
                over = [best]
        for k in over:
            if now - last_tap[k] <= 0.25:
                continue
            if S["echo_ms"] and now - max(last_tap[j] for j in range(4) if j != k) < S["echo_ms"] / 1000:
                reject("echo of another disc", disc=k)
                continue
            if S["tap_motion_dps"] and gmax > S["tap_motion_dps"]:
                reject("hand moving fast (%d deg/s)" % gmax, disc=k)
                continue
            if S["tap_lock_ms"] and now - max(last_flick, last_squeeze) < S["tap_lock_ms"] / 1000:
                reject("just after a flick/squeeze", disc=k)
                continue
            last_tap[k] = now
            taps_recent = [t for t in taps_recent if now - t < S["double_ms"] / 1000] + [now]
            name = "double tap" if len(taps_recent) >= 2 else "tap"
            frame["events"].append({"kind": name, "disc": k, "v": int(peaks[k])})
            if S["mode"] == "ui" or S["mouse"]:
                act(frame, "double-click" if name == "double tap" else "click", mouse_click, 2 if name == "double tap" else 1)
            elif S["mode"] == "present" and name == "double tap":
                act(frame, "black screen (B)", key, "b")
        # ---- squeeze (rising edge, with hysteresis) ----
        fm = fsr.mean(0)
        for k in range(2):
            t_on = S["fsr_thr_d"][k]
            on = fm[k] > t_on if not fsr_on[k] else fm[k] > t_on * S["fsr_hyst"]
            if on and not fsr_on[k]:
                frame["events"].append({"kind": "squeeze", "fsr": k, "v": int(fm[k])})
                last_squeeze = now
                if S["mode"] == "ui" and not DRAG["on"]:
                    act(frame, "drag: grab", mouse_button, True)
            if fsr_on[k] and not on and S["mode"] == "ui" and DRAG["on"]:
                act(frame, "drag: drop", mouse_button, False)
            fsr_on[k] = on
        # ---- flick (fast hand rotation) ----
        if len(gsrc):
            # 40 ms moving average removes single-sample spikes (a loose wire or a knock) before looking for a flick
            raw = gsrc / GYR
            k4 = min(4, len(raw))
            sm = np.vstack([np.convolve(raw[:, c], np.ones(k4) / k4, mode="valid") for c in range(3)]).T
            top = float(np.abs(sm).max())
            if not flick_armed and top < S["flick_dps"] * S["rearm"] and now - last_flick > 0.25:
                flick_armed = True                     # hand has slowed down: ready for the next flick
            if flick_armed and top > S["flick_dps"]:
                ax = int(np.argmax(np.abs(sm).max(0)))
                v = sm[np.argmax(np.abs(sm[:, ax])), ax]
                # directions come from the Settings page (air-mouse learn = which way is right / up; roll learn)
                ix = "xyz".index(S["mx"][1]); iy = "xyz".index(S["my"][1])
                if ax == ix:
                    kind = "flick right" if v * S["mx_sign"] > 0 else "flick left"
                elif ax == iy:
                    kind = "flick up" if v * S["my_sign"] < 0 else "flick down"     # my_sign is screen-down
                else:
                    kind = "roll right" if v * S["roll_sign"] > 0 else "roll left"
                flick_armed = False
                if ax == last_ax and kind != last_kind and now - last_flick < S["return_ms"] / 1000:
                    reject("hand coming back after " + last_kind, flick=kind)
                    last_flick = now                    # keep the window open while the hand settles
                elif S["flick_lock_ms"] and now - max(last_tap) < S["flick_lock_ms"] / 1000:
                    reject("flick right after a tap", flick=kind)
                else:
                    last_flick, last_kind, last_ax = now, kind, ax
                    frame["events"].append({"kind": kind, "dps": int(abs(v))})
                    if S["mode"] == "present" and kind in ("flick right", "flick left"):
                        act(frame, "next slide" if kind == "flick right" else "previous slide", key, "right" if kind == "flick right" else "left")
                    elif S["mode"] == "ui" and kind.startswith("roll "):
                        act(frame, "scroll " + ("down" if kind == "roll right" else "up"), scroll, -5 if kind == "roll right" else 5)
        # air mouse
        src = g2 if settings["imu"] == 2 else g1
        if (settings["mouse"] or settings["mode"] == "ui") and src is not None:
            ix = "xyz".index(settings["mx"][1]); iy = "xyz".index(settings["my"][1])
            vx, vy = src[ix] * settings["mx_sign"], src[iy] * settings["my_sign"]
            dead = settings["dead"]
            vx = 0 if abs(vx) < dead else vx - math.copysign(dead, vx)
            vy = 0 if abs(vy) < dead else vy - math.copysign(dead, vy)
            if vx or vy:
                try:
                    mouse_move(vx * settings["sens"] * dt, vy * settings["sens"] * dt)
                except Exception as e:
                    frame["events"].append({"kind": "mouse error", "msg": str(e)})
        broadcast(frame)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/calib"):
            try:
                return self._json(json.load(open(CALIB)))
            except (OSError, ValueError):
                return self._json({})
        if self.path.startswith("/stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")   # setup.html opened as a file reads this live
            self.end_headers()
            q = queue.Queue(maxsize=200)
            with clients_lock:
                clients.append(q)
            try:
                self.wfile.write(("data: " + json.dumps({"settings": settings}) + "\n\n").encode())
                while True:
                    self.wfile.write(q.get())
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with clients_lock:
                    clients.remove(q)
            return
        page = "test.html" if self.path.startswith("/test") else "config.html" if self.path.startswith("/config") else "play.html" if self.path.startswith("/play") else "setup.html" if self.path.startswith("/setup") else "demo.html"
        body = open(os.path.join(HERE, page), "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        if self.path.startswith("/record"):           # {"action": "start"|"stop", "audio": bool}
            try:
                upd = json.loads(self.rfile.read(n) or b"{}")
            except ValueError:
                upd = {}
            if upd.get("action") == "start":
                rec_start(bool(upd.get("audio")))
            elif upd.get("action") == "stop":
                rec_stop()
            return self._json(rec_state())
        if self.path.startswith("/calib"):            # merge into calib.json, apply mouse axes now
            try:
                upd = json.loads(self.rfile.read(n) or b"{}")
                try:
                    cur = json.load(open(CALIB))
                except (OSError, ValueError):
                    cur = {}
                cur.update(upd)
                json.dump(cur, open(CALIB, "w"), indent=2)
                apply_calib(cur)
                broadcast({"calib": cur})                # every open page picks up the new settings now
            except (ValueError, TypeError):
                cur = {}
            return self._json(cur)
        try:
            upd = json.loads(self.rfile.read(n) or b"{}")
            if "tap_thr" in upd:
                upd["tap_thr_d"] = [upd["tap_thr"]] * 4
            if "fsr_thr" in upd:
                upd["fsr_thr_d"] = [upd["fsr_thr"]] * 2
            for k, v in upd.items():
                if k in settings:
                    settings[k] = type(settings[k])(v)
        except (ValueError, TypeError):
            pass
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(settings).encode())


def rec_start(audio):
    if REC["proc"] and REC["proc"].poll() is None:
        return
    os.makedirs(os.path.join(HERE, "photos"), exist_ok=True)
    name = time.strftime("WristTap_demo_%Y%m%d_%H%M%S.mov")
    REC["file"] = os.path.join(HERE, "photos", name)
    cmd = ["screencapture", "-v", "-x", "-C", "-k"] + (["-g"] if audio else []) + [REC["file"]]
    REC["proc"] = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    REC["t0"] = time.time()


def rec_stop():
    pr = REC["proc"]
    if pr and pr.poll() is None:
        pr.send_signal(2)                      # SIGINT = stop and finish the file cleanly
        try:
            pr.wait(timeout=15)
        except subprocess.TimeoutExpired:
            pr.kill()
    REC["proc"] = None


def rec_state():
    on = bool(REC["proc"] and REC["proc"].poll() is None)
    return {"on": on, "secs": round(time.time() - REC["t0"]) if on else 0,
            "file": os.path.basename(REC["file"]) if REC["file"] else None}


def apply_calib(c):
    for k, v in c.get("settings", {}).items():       # saved filter/threshold settings
        if k in settings and k != "mouse":
            settings[k] = type(settings[k])(v)
    for k in ("mx", "my", "mx_sign", "my_sign", "roll_sign"):
        if k in c.get("mouse", {}):
            settings[k] = type(settings[k])(c["mouse"][k])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port")
    ap.add_argument("--wifi", action="store_true")
    ap.add_argument("--ble", action="store_true")
    ap.add_argument("--sim", action="store_true", help="fake band, for rehearsing")
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()
    try:
        apply_calib(json.load(open(CALIB)))
    except (OSError, ValueError):
        pass
    band = SimBand() if a.sim else wristtap.open_band(a)
    threading.Thread(target=engine, args=(band,), daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"WristTap demo on {url}  (Ctrl+C to stop)")
    if not a.no_open:
        subprocess.Popen(["open", "-a", "Safari", url])
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        rec_stop()
        band.close()
