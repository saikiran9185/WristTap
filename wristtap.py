"""WristTap: camera-labelled mid-air pinch/tap dataset from a sensor wristband.

  python wristtap.py check            # is the band streaming? live numbers per sensor (USB)
  python wristtap.py check --wifi     # same, over Wi-Fi     python wristtap.py check --ble  # over Bluetooth
  python wristtap.py record --reps 20 # cued session: the Mac camera labels pinches, the band records

Each recording goes to sessions/<date_time>/:
  sensors.npz  t (Mac seconds), imu1 (N,6), imu2 (N,6), piezo (N,4), fsr (N,2), seq
  camera.csv   t, hand, d_index, d_middle, d_ring, d_pinky (thumb-tip distance / hand size)
  cues.csv     t_start, t_end, gesture
  meta.json    settings
"""
import argparse
import csv
import datetime
import glob
import json
import os
import random
import struct
import sys
import threading
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HAND_MODEL = os.path.expanduser("~/Projects/PhoneStereo/hand_landmarker.task")
PKT = struct.Struct("<HI6h6h4H2HH")      # 44 bytes, see firmware
MAGIC = b"\xaa\x55"
UDP_PORT = 4210
BLE_DATA = "7a1e0002-5752-4954-5441-500000000001"
GESTURES = ["REST", "PINCH INDEX", "PINCH MIDDLE", "PINCH PINKY", "AIR TAP"]
TIPS = {"index": 8, "middle": 12, "ring": 16, "pinky": 20}


def find_port():
    pats = ["/dev/cu.usbserial*", "/dev/cu.SLAB_USBtoUART*", "/dev/cu.wchusbserial*", "/dev/cu.usbmodem*"]
    ports = [p for pat in pats for p in glob.glob(pat)]
    if not ports:
        sys.exit("No ESP32 found. Plug it in with a DATA cable. Ports seen: "
                 + ", ".join(glob.glob("/dev/cu.*")))
    return ports[0]


class Band:
    """Reads packets in a thread; stamps each with Mac time via the ESP32 clock + best offset.

    source: a serial port path, "wifi" (UDP port 4210) or "ble" (Bluetooth LE device "WristTap").
    All three carry the same 44-byte packet, so everything downstream is identical.
    """

    def __init__(self, source):
        self.source = source
        self.rows = []            # (t_esp, imu1*6, imu2*6, piezo*4, fsr*2, seq)
        self.lock = threading.Lock()
        self.offset = None        # min(recv_time - esp_time): the least-delayed packet sets the clock
        self.drops = 0
        self.last_seq = None
        self.running = True
        self.wrap = 0
        self.last_us = 0
        self.buf = b""
        self.status = "starting"
        target = {"wifi": self._run_udp, "ble": self._run_ble}.get(source, self._run_serial)
        threading.Thread(target=target, daemon=True).start()

    # ── transports ──
    def _run_serial(self):
        import serial
        self.ser = serial.Serial(self.source, 921600, timeout=0.05)
        self.status = f"USB {self.source}"
        while self.running:
            self._feed(self.ser.read(4096))
        self.ser.close()

    def _run_udp(self):
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        s.bind(("", UDP_PORT))
        s.settimeout(0.2)
        self.status = f"Wi-Fi, listening on UDP {UDP_PORT}"
        while self.running:
            try:
                data, addr = s.recvfrom(2048)
            except OSError:
                continue
            self.status = f"Wi-Fi from {addr[0]}"
            self._feed(data)
        s.close()

    def _run_ble(self):
        import asyncio
        from bleak import BleakClient, BleakScanner

        async def main():
            while self.running:
                self.status = "Bluetooth: looking for WristTap..."
                dev = await BleakScanner.find_device_by_name("WristTap", timeout=8)
                if not dev:
                    continue
                try:
                    async with BleakClient(dev) as c:
                        self.status = "Bluetooth: connected"
                        self.last_seq = None
                        await c.start_notify(BLE_DATA, lambda _h, d: self._feed(bytes(d)))
                        while self.running and c.is_connected:
                            await asyncio.sleep(0.2)
                except Exception as e:          # dropped link: scan again
                    self.status = f"Bluetooth: lost ({e.__class__.__name__}), reconnecting"
        asyncio.run(main())

    # ── packet parser (shared) ──
    def _feed(self, data):
        if not data:
            return
        now = time.time()
        buf = self.buf + data
        while True:
            i = buf.find(MAGIC)
            if i < 0 or len(buf) - i < PKT.size:
                buf = buf[i:] if i >= 0 else buf[-1:]
                break
            f = PKT.unpack_from(buf, i)
            buf = buf[i + PKT.size:]
            us, seq = f[1], f[-1]
            if us < self.last_us and self.last_us - us > 1 << 31:
                self.wrap += 1 << 32
            self.last_us = us
            esp_t = (us + self.wrap) / 1e6
            off = now - esp_t
            if self.offset is None or off < self.offset:
                self.offset = off
            if self.last_seq is not None:
                gap = (seq - self.last_seq) & 0xFFFF
                if 1 < gap < 1000:
                    self.drops += gap - 1
            self.last_seq = seq
            with self.lock:
                self.rows.append((esp_t,) + f[2:-1] + (seq,))
                if len(self.rows) > 200000:
                    del self.rows[:100000]
        self.buf = buf

    def snapshot(self, n=None):
        with self.lock:
            return list(self.rows[-n:]) if n else list(self.rows)

    def close(self):
        self.running = False
        time.sleep(0.3)


def open_band(a):
    if a.wifi:
        return Band("wifi")
    if a.ble:
        return Band("ble")
    return Band(a.port or find_port())


def check(a):
    band = open_band(a)
    print("Reading... Ctrl+C to stop. Tap the band, press the FSRs, move your wrist.\n")
    t0 = time.time()
    try:
        while True:
            time.sleep(1)
            rows = band.snapshot()
            recent = [r for r in rows if r[0] >= rows[-1][0] - 1.0] if rows else []
            if not recent:
                print(f"no packets yet [{band.status}] (Wi-Fi: is the Mac on the same network? USB: reset button?)")
                continue
            arr = np.array([r[1:-1] for r in recent], float)
            imu1, imu2, pz, fsr = arr[:, 0:6], arr[:, 6:12], arr[:, 12:16], arr[:, 16:18]
            accel_g = lambda m: np.linalg.norm(m[:, :3], axis=1) / 4096.0   # +-8 g -> 4096 LSB/g
            def imu_txt(m):
                if not m.any():
                    return "MISSING (check wiring / AD0)"
                return f"|a| {accel_g(m).mean():.2f} g (peak {accel_g(m).max():.2f})"
            print(f"[{time.time()-t0:5.0f}s] {band.status}: {len(recent)} pkt/s  drops {band.drops}  "
                  f"IMU1 {imu_txt(imu1)}  IMU2 {imu_txt(imu2)}")
            print("        piezo peak " + "  ".join(f"{int(v):4d}" for v in pz.max(0))
                  + "   FSR " + "  ".join(f"{int(v):4d}" for v in fsr.mean(0)))
    except KeyboardInterrupt:
        band.close()


def make_tracker():
    from mediapipe.tasks.python import BaseOptions, vision
    return vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=HAND_MODEL), running_mode=vision.RunningMode.VIDEO,
        num_hands=1, min_hand_detection_confidence=0.5, min_tracking_confidence=0.5))


def pinch_distances(lms):
    """Thumb-tip to each fingertip, divided by wrist-to-middle-knuckle length (scale-free)."""
    p = np.array([(l.x, l.y, l.z) for l in lms])
    size = np.linalg.norm(p[9, :2] - p[0, :2]) + 1e-6
    return {k: float(np.linalg.norm(p[4, :2] - p[i, :2]) / size) for k, i in TIPS.items()}


def record(a):
    import cv2
    import mediapipe as mp

    band = open_band(a)
    cap = cv2.VideoCapture(a.cam, cv2.CAP_AVFOUNDATION)
    for _ in range(20):
        if cap.isOpened():
            break
        time.sleep(0.5)
        cap = cv2.VideoCapture(a.cam, cv2.CAP_AVFOUNDATION)
    if not cap.isOpened():
        band.close()
        sys.exit("Mac camera not allowed: System Settings > Privacy & Security > Camera (allow your terminal)")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    tracker = make_tracker()

    plan = [g for g in GESTURES for _ in range(a.reps)]
    random.shuffle(plan)
    out = os.path.join(HERE, "sessions", datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out)
    cam_rows, cues = [], []
    state, idx, t_state = "intro", 0, time.time()
    t0 = time.time()
    print(f"Recording {len(plan)} cues to {out}\nWindow: SPACE = start, Q = stop early")

    while True:
        ok, frame = cap.read()
        now = time.time()
        if not ok:
            continue
        frame = cv2.flip(frame, 1)
        res = tracker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,
                                                data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)),
                                       int((now - t0) * 1000))
        if res.hand_landmarks:
            d = pinch_distances(res.hand_landmarks[0])
            cam_rows.append([now, 1] + [d[k] for k in TIPS])
            h, w = frame.shape[:2]
            for l in res.hand_landmarks[0]:
                cv2.circle(frame, (int(l.x * w), int(l.y * h)), 3, (0, 220, 0), -1)
        else:
            cam_rows.append([now, 0] + [np.nan] * 4)

        # cue state machine: ready (1.2 s) -> GO (1.5 s) -> next
        if state == "ready" and now - t_state > 1.2:
            state, t_state = "go", now
        elif state == "go" and now - t_state > 1.5:
            cues.append([t_state, now, plan[idx]])
            idx += 1
            state, t_state = ("ready", now) if idx < len(plan) else ("done", now)

        msg, col = {"intro": ("Press SPACE to start", (255, 255, 255)),
                    "ready": (f"next: {plan[idx] if idx < len(plan) else ''}", (0, 200, 255)),
                    "go": (f"NOW: {plan[idx] if idx < len(plan) else ''}", (0, 0, 255)),
                    "done": ("Done - saving", (0, 255, 0))}[state]
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 90), (0, 0, 0), -1)
        cv2.putText(frame, msg, (24, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.6, col, 3)
        rows = band.snapshot(250)
        info = f"cue {idx}/{len(plan)}  band {len(rows)*2 if rows else 0} pkt/s  drops {band.drops}"
        cv2.putText(frame, info, (24, frame.shape[0] - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.imshow("WristTap record", frame)
        k = cv2.waitKey(1) & 0xFF
        if k == ord(" ") and state == "intro":
            state, t_state = "ready", now
        if k == ord("q") or (state == "done" and now - t_state > 0.5):
            break

    cap.release()
    cv2.destroyAllWindows()
    rows = band.snapshot()
    off = band.offset or 0.0
    band.close()
    arr = np.array([r[1:-1] for r in rows], dtype=np.int32) if rows else np.zeros((0, 18), np.int32)
    np.savez_compressed(os.path.join(out, "sensors.npz"),
                        t=np.array([r[0] + off for r in rows]), imu1=arr[:, 0:6], imu2=arr[:, 6:12],
                        piezo=arr[:, 12:16], fsr=arr[:, 16:18], seq=np.array([r[-1] for r in rows]))
    with open(os.path.join(out, "camera.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "hand", "d_index", "d_middle", "d_ring", "d_pinky"])
        w.writerows(cam_rows)
    with open(os.path.join(out, "cues.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_start", "t_end", "gesture"])
        w.writerows(cues)
    json.dump({"reps": a.reps, "gestures": GESTURES, "packets": len(rows), "drops": band.drops,
               "camera_frames": len(cam_rows), "cues_done": len(cues), "note": a.note},
              open(os.path.join(out, "meta.json"), "w"), indent=2)
    print(f"Saved {len(rows)} band packets, {len(cam_rows)} camera frames, {len(cues)} cues -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["check", "record"])
    ap.add_argument("--port")
    ap.add_argument("--wifi", action="store_true", help="read over Wi-Fi (UDP 4210) instead of USB")
    ap.add_argument("--ble", action="store_true", help="read over Bluetooth LE instead of USB")
    ap.add_argument("--cam", type=int, default=0)
    ap.add_argument("--reps", type=int, default=20, help="repetitions per gesture")
    ap.add_argument("--note", default="", help="e.g. 'band on left wrist, sitting'")
    a = ap.parse_args()
    check(a) if a.mode == "check" else record(a)
