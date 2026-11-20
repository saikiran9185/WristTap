"""WristTap 3D mouse: where the hand is in 3D space, from the band alone.

  ./space.sh            # band on USB
  ./space.sh --ble      # Bluetooth
  ./space.sh --wifi     # Wi-Fi

Opens http://localhost:8792.

How it works (no camera, no outside sensor):
  The elbow rests in one spot (desk or armrest). MPU #1 gives the forearm's direction,
  MPU #2 gives the hand's direction. With the forearm and hand lengths, that pins down
  the hand's position:   hand = elbow + forearm_len * forearm_dir + hand_len * hand_dir
  Each MPU runs its own orientation filter (gyro + gravity) on every 500 Hz sample.
  Up/down and tilt are held by gravity, so they don't drift. Left/right turning (yaw)
  comes from the gyro only and drifts slowly: recenter at your 000 point to reset it.

Recenter (set this spot as 0, 0, 0):
  - press "Set 000 here" on the page, or
  - squeeze and hold either FSR for 1 second (hands-free).

Position is also sent as JSON over UDP to 127.0.0.1:4211, e.g. {"x":1.2,"y":-3.4,"z":5.0}
(centimetres; x = right, y = up, z = forward), so Blender, Unity or TouchDesigner can read it.
"""
import argparse
import json
import math
import os
import queue
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

import wristtap
from demo import mouse_click

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8792
UDP_OUT = ("127.0.0.1", 4211)
ACC = 4096.0      # LSB per g   (+-8 g)
GYR = 32.8        # LSB per dps (+-1000 dps)
STILL_START_S = 1.5   # hold still this long at start: learns the gyro offset

settings = {      # changed live from the page
    "forearm_cm": 26.0, "hand_cm": 9.0,      # elbow -> wrist, wrist -> pointer (knuckles)
    "dir1": 1, "dir2": 1,                    # +1 if the MPU's x arrow points to the fingers, -1 if to the elbow
    "abs_mouse": False, "px_per_cm": 35.0,   # absolute 2D mouse from x / y
    "tap_thr": 150, "fsr_thr": 900, "hold_s": 1.0,
}
clients = []
clients_lock = threading.Lock()
cmd = {"recenter": False}


class Orientation:
    """Mahony filter: gyro integrates, gravity pulls roll/pitch back. Quaternion = sensor -> world (z up)."""

    def __init__(self):
        self.q = None
        self.bias = np.zeros(3)
        self.integral = np.zeros(3)
        self.start_samples = []
        self.t_first = None
        self.ok = False

    def ready(self):
        return self.q is not None and self.t_first is not None and not self.start_samples

    def step(self, a_raw, g_raw, t, dt):
        if not a_raw.any():
            self.ok = False
            return
        self.ok = True
        a = a_raw / ACC
        g_dps = g_raw / GYR
        an = np.linalg.norm(a)
        if self.q is None:                          # start level with gravity, yaw = 0
            r = math.atan2(a[1], a[2])
            p = math.atan2(-a[0], math.hypot(a[1], a[2]))
            cr, sr, cp, sp = math.cos(r / 2), math.sin(r / 2), math.cos(p / 2), math.sin(p / 2)
            self.q = np.array([cr * cp, sr * cp, cr * sp, -sr * sp])
            self.t_first = t
        if self.start_samples is not None and t - self.t_first < STILL_START_S:
            self.start_samples.append(g_dps)        # learning the gyro offset: keep still
            return
        if self.start_samples:
            self.bias = np.mean(self.start_samples, 0)
            self.start_samples = []
        g_corr = g_dps - self.bias
        if np.linalg.norm(g_corr) < 2.5 and abs(an - 1) < 0.05:
            self.bias += 0.001 * g_corr             # still: keep refining the offset
        w = np.radians(g_corr)
        q0, q1, q2, q3 = self.q
        if 0.85 < an < 1.15:                        # trust gravity only when not shaking
            v = np.array([2 * (q1 * q3 - q0 * q2), 2 * (q0 * q1 + q2 * q3), q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3])
            e = np.cross(a / an, v)
            self.integral += 0.02 * e * dt
            w = w + 1.5 * e + self.integral
        dq = 0.5 * np.array([-q1 * w[0] - q2 * w[1] - q3 * w[2],
                             q0 * w[0] + q2 * w[2] - q3 * w[1],
                             q0 * w[1] - q1 * w[2] + q3 * w[0],
                             q0 * w[2] + q1 * w[1] - q2 * w[0]])
        self.q = self.q + dq * dt
        self.q /= np.linalg.norm(self.q)

    def x_axis(self):
        """The sensor's x arrow, in world coordinates."""
        q0, q1, q2, q3 = self.q
        return np.array([1 - 2 * (q2 * q2 + q3 * q3), 2 * (q1 * q2 + q0 * q3), 2 * (q1 * q3 - q0 * q2)])


def broadcast(obj):
    data = ("data: " + json.dumps(obj) + "\n\n").encode()
    with clients_lock:
        for q in list(clients):
            try:
                q.put_nowait(data)
            except queue.Full:
                pass


def mouse_to(x_px, y_px):
    import Quartz
    b = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    x = min(max(x_px, 0), b.size.width - 1)
    y = min(max(y_px, 0), b.size.height - 1)
    ev = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)
    return b.size.width, b.size.height


def engine(band):
    ori = [Orientation(), Orientation()]
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    n_seen = 0
    t_prev = None
    last_tap = [0.0] * 4
    hold_since = None
    yaw0 = None           # heading of "forward", set at recenter
    hand_fix = 0.0        # turns the hand's heading back in line with the forearm (they drift apart)
    p0 = None             # world position of the 000 point (elbow = origin)
    screen = None
    while True:
        time.sleep(1 / 60)
        with band.lock:
            total = len(band.rows)
            if total < n_seen:
                n_seen = max(0, total - 20)
            new = band.rows[n_seen:]
            rows = band.rows[-600:]
        n_seen = total
        frame = {"status": band.status, "events": []}
        frame["rate"] = len([r for r in rows if r[0] >= rows[-1][0] - 1.0]) if rows else 0
        if not new:
            broadcast(frame)
            continue
        arr = np.array([r[:-1] for r in new], float)    # t, imu1*6, imu2*6, piezo*4, fsr*2
        now = time.time()
        for row in arr:
            t = row[0]
            dt = 0.002 if t_prev is None else min(max(t - t_prev, 0.0), 0.05)
            t_prev = t
            ori[0].step(row[1:4], row[4:7], t, dt)
            ori[1].step(row[7:10], row[10:13], t, dt)
            # hold an FSR for hold_s -> recenter (hands-free)
            if max(row[17], row[18]) > settings["fsr_thr"]:
                hold_since = t if hold_since is None else hold_since
                if t - hold_since >= settings["hold_s"]:
                    cmd["recenter"] = True
                    hold_since = float("inf")         # once per hold
            else:
                hold_since = None
        # taps (click in absolute-mouse mode)
        peaks = arr[:, 13:17].max(0)
        for k in range(4):
            if peaks[k] > settings["tap_thr"] and now - last_tap[k] > 0.25:
                last_tap[k] = now
                frame["events"].append({"kind": "tap", "disc": k})
                if settings["abs_mouse"]:
                    try:
                        mouse_click()
                    except Exception as e:
                        frame["events"].append({"kind": "mouse error", "msg": str(e)})

        a, h = ori
        frame["imu_ok"] = [a.ok, h.ok]
        if not (a.ok and a.ready()):
            frame["calibrating"] = a.ok
            broadcast(frame)
            continue
        d1 = a.x_axis() * settings["dir1"]
        hand_ok = h.ok and h.ready()
        d2 = h.x_axis() * settings["dir2"] if hand_ok else d1.copy()
        if yaw0 is None or cmd["recenter"]:
            # 000 pose: hand flat and straight in line with the forearm
            if math.hypot(d1[0], d1[1]) > 0.2:
                yaw0 = math.atan2(d1[1], d1[0])
                if math.hypot(d2[0], d2[1]) > 0.2:
                    hand_fix = yaw0 - math.atan2(d2[1], d2[0])
            yaw0 = yaw0 or 0.0
        ch, sh = (math.cos(hand_fix), math.sin(hand_fix)) if hand_ok else (1.0, 0.0)
        d2 = np.array([ch * d2[0] - sh * d2[1], sh * d2[0] + ch * d2[1], d2[2]])
        wrist = settings["forearm_cm"] * d1
        tip = wrist + settings["hand_cm"] * d2
        if p0 is None or cmd["recenter"]:
            p0 = tip.copy()
            if cmd["recenter"]:
                frame["events"].append({"kind": "recenter"})
            cmd["recenter"] = False
        c, s = math.cos(yaw0), math.sin(yaw0)

        def local(v):     # world -> (x right, y up, z forward), cm, relative to the 000 point
            v = v - p0
            fwd, left = c * v[0] + s * v[1], -s * v[0] + c * v[1]
            return [round(-left, 2), round(v[2], 2), round(fwd, 2)]

        pos = local(tip)
        frame["pos"] = pos
        frame["arm"] = [local(np.zeros(3)), local(wrist), pos]
        try:
            udp.sendto(json.dumps({"x": pos[0], "y": pos[1], "z": pos[2], "t": round(now, 3)}).encode(), UDP_OUT)
        except OSError:
            pass
        if settings["abs_mouse"]:
            try:
                if screen is None:
                    screen = mouse_to(0, 0)
                ppc = settings["px_per_cm"]
                mouse_to(screen[0] / 2 + pos[0] * ppc, screen[1] / 2 - pos[1] * ppc)
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
        body = open(os.path.join(HERE, "space.html"), "rb").read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            upd = json.loads(self.rfile.read(n) or b"{}")
            if upd.pop("recenter", False):
                cmd["recenter"] = True
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
    print(f"WristTap 3D mouse on {url}  (Ctrl+C to stop). Keep your arm still for 2 s while it starts.")
    if not a.no_open:
        subprocess.Popen(["open", "-a", "Safari", url])
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        band.close()
