"""WristTap live demo: 3D forearm + hand, taps, squeezes, simple gestures and an air mouse.

  ./demo.sh            # band on USB
  ./demo.sh --ble      # band over Bluetooth (power bank, no cable)
  ./demo.sh --wifi     # band over Wi-Fi (Mac on the same network as the band)

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
    "present": False,      # presentation mode: gestures press slide keys
    "swap_lr": False,      # flip which flick is "right" (depends on how the hand sensor sits)
}
# Presentation mode: gesture -> (macOS key code, what it does). Works in Keynote, PowerPoint, Google Slides, PDF viewers.
SLIDE_KEYS = {
    "flick right": (124, "next slide"),        # right arrow
    "flick left": (123, "previous slide"),     # left arrow
    "double tap": (124, "next slide"),
    "squeeze": (11, "black screen on / off"),  # B
}
FLICK_LOCK_S = 0.8   # in presentation mode: ignore flicks this long after one (the hand swinging back looks like the opposite flick)
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
        self.roll = (1 - k) * (self.roll + (g[0] - self.bias[0]) * dt) + k * r
        self.pitch = (1 - k) * (self.pitch + (g[1] - self.bias[1]) * dt) + k * p
        if np.linalg.norm(g - self.bias) < 3:      # still: slowly learn the gyro bias
            self.bias = 0.98 * self.bias + 0.02 * g
        self.yaw += (g[2] - self.bias[2]) * dt
        self.yaw *= 0.999                          # gentle pull back to centre (no magnetometer)
        return g - self.bias


def mouse_move(dx, dy):
    import Quartz
    pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    b = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    x = min(max(pos.x + dx, 0), b.size.width - 1)
    y = min(max(pos.y + dy, 0), b.size.height - 1)
    ev = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)


def mouse_click():
    import Quartz
    pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    for t in (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp):
        Quartz.CGEventPost(Quartz.kCGHIDEventTap,
                           Quartz.CGEventCreateMouseEvent(None, t, pos, Quartz.kCGMouseButtonLeft))


def press_key(code):
    import Quartz
    for down in (True, False):
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, Quartz.CGEventCreateKeyboardEvent(None, code, down))


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
    fsr_on = [False, False]
    taps_recent = []
    t_prev = time.time()
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
        frame = {"status": band.status, "rate": 0, "events": [], "mouse": settings["mouse"]}
        recent = [r for r in rows if r[0] >= rows[-1][0] - 1.0] if rows else []
        frame["rate"] = len(recent)
        if not new:
            broadcast(frame)
            continue
        arr = np.array([r[1:-1] for r in new], float)
        imu1, imu2, pz, fsr = arr[:, 0:6], arr[:, 6:12], arr[:, 12:16], arr[:, 16:18]
        g1 = imus[0].update(imu1, dt)
        g2 = imus[1].update(imu2, dt)
        frame["imu"] = [{"ok": i.ok, "roll": i.roll, "pitch": i.pitch, "yaw": i.yaw} for i in imus]
        frame["bend"] = imus[1].pitch - imus[0].pitch if imus[0].ok and imus[1].ok else None
        peaks = pz.max(0)
        frame["piezo"] = [int(v) for v in peaks]
        frame["fsr"] = [int(v) for v in fsr.mean(0)]

        # taps (one per disc per 250 ms); two taps within 400 ms = double tap
        for k in range(4):
            if peaks[k] > settings["tap_thr"] and now - last_tap[k] > 0.25:
                last_tap[k] = now
                taps_recent = [t for t in taps_recent if now - t < 0.4] + [now]
                name = "double tap" if len(taps_recent) >= 2 else "tap"
                frame["events"].append({"kind": name, "disc": k, "v": int(peaks[k])})
                if settings["mouse"]:
                    mouse_click()
        # squeeze (FSR rising edge)
        for k in range(2):
            on = fsr.mean(0)[k] > settings["fsr_thr"]
            if on and not fsr_on[k]:
                frame["events"].append({"kind": "squeeze", "fsr": k})
            fsr_on[k] = on
        # flick (fast hand rotation)
        g = g2 if imus[1].ok else g1
        if g is not None and now - last_flick > (FLICK_LOCK_S if settings["present"] else 0.5):
            peak = (arr[:, 9:12] if imus[1].ok else arr[:, 3:6]) / GYR
            ax = int(np.argmax(np.abs(peak).max(0)))
            v = peak[np.argmax(np.abs(peak[:, ax])), ax]
            if abs(v) > settings["flick_dps"]:
                last_flick = now
                names = [("roll right", "roll left"), ("flick down", "flick up"), ("flick left", "flick right")]
                frame["events"].append({"kind": names[ax][0 if v > 0 else 1], "dps": int(abs(v))})
        # presentation mode: gestures -> slide keys
        if settings["present"]:
            for ev in frame["events"]:
                if settings["swap_lr"] and ev["kind"] in ("flick left", "flick right"):
                    ev["kind"] = "flick right" if ev["kind"] == "flick left" else "flick left"
                if ev["kind"] in SLIDE_KEYS:
                    code, action = SLIDE_KEYS[ev["kind"]]
                    try:
                        press_key(code)
                        ev["action"] = action
                    except Exception as e:
                        ev["action"] = "key blocked: allow Terminal in Accessibility (" + e.__class__.__name__ + ")"
        # air mouse
        src = g2 if settings["imu"] == 2 else g1
        if settings["mouse"] and src is not None:
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

    def do_GET(self):
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
        body = open(os.path.join(HERE, "demo.html"), "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            upd = json.loads(self.rfile.read(n) or b"{}")
            for k, v in upd.items():
                if k in settings:
                    settings[k] = type(settings[k])(v)
        except (ValueError, TypeError):
            pass
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(settings).encode())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port")
    ap.add_argument("--wifi", action="store_true")
    ap.add_argument("--ble", action="store_true")
    ap.add_argument("--no-open", action="store_true")
    a = ap.parse_args()
    band = wristtap.open_band(a)
    threading.Thread(target=engine, args=(band,), daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"WristTap demo on {url}  (Ctrl+C to stop)")
    if not a.no_open:
        subprocess.Popen(["open", "-a", "Safari", url])
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        band.close()
