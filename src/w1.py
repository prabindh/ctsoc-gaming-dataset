import asyncio
from bleak import BleakClient
import struct
import time
import csv
from collections import deque
import requests
import threading

# Configuration (Replace with your device MAC address)
WATCH_MAC  = "XX:XX:XX:XX:XX:XX"  # e.g., "F5:87:2B:6D:C0:9A"
DATA_UUID  = "cd5c1525-4448-7db8-ae4c-d1da8cba36d0"  # Only active PPG channel
MASTER_CSV = "valorant_biometrics_master.csv"

# ── Peak detector tuning ──────────────────────────────────────────────────────
MIN_PEAK_DISTANCE = 0.5    # blocks dicrotic notch double-count
MAX_PEAK_DISTANCE = 1.5    # resets on signal loss
AMPLITUDE_RATIO   = 0.60   # rejects peaks < 60% of last real peak

# ── Spike detection ───────────────────────────────────────────────────────────
SPIKE_THRESHOLD = 15
BASELINE_WINDOW = 20

# ── State ─────────────────────────────────────────────────────────────────────
ppg_buffer     = deque(maxlen=200)
last_peak_time = None
last_peak_val  = None
rr_intervals   = deque(maxlen=4)
bpm_history    = deque(maxlen=BASELINE_WINDOW)
last_sent_bpm  = None


def get_baseline():
    if len(bpm_history) < 5:
        return None
    return sum(bpm_history) / len(bpm_history)


def classify_bpm(bpm):
    baseline = get_baseline()
    if baseline is None:
        return "CALIBRATING"
    delta = bpm - baseline
    if delta >= SPIKE_THRESHOLD * 2:
        return "INTENSE_SPIKE"
    elif delta >= SPIKE_THRESHOLD:
        return "ELEVATED"
    elif delta <= -SPIKE_THRESHOLD:
        return "RECOVERY"
    return "NORMAL"


def send_to_receiver(payload: dict):
    """Non-blocking — never holds up the BLE async loop."""
    def _post():
        try:
            requests.post(
                "http://localhost:5000/log",
                json={"event": "BIOMETRIC_DATA", "data": payload},
                timeout=0.15
            )
        except Exception:
            pass
    threading.Thread(target=_post, daemon=True).start()


# ── PPG peak detector ─────────────────────────────────────────────────────────

def detect_peak(ts, value):
    global last_peak_time, last_peak_val

    ppg_buffer.append((ts, value))
    if len(ppg_buffer) < 11:
        return None

    recent = list(ppg_buffer)[-11:]
    mid_ts, mid_val = recent[5]

    # Must be strictly greater than all 5 neighbors on each side
    is_peak = (all(mid_val > s[1] for s in recent[:5]) and
               all(mid_val > s[1] for s in recent[6:]))
    if not is_peak:
        return None

    # Reject dicrotic notch
    if last_peak_val is not None and mid_val < last_peak_val * AMPLITUDE_RATIO:
        return None

    if last_peak_time is not None:
        rr = mid_ts - last_peak_time

        if rr < MIN_PEAK_DISTANCE:
            return None

        if rr > MAX_PEAK_DISTANCE:
            last_peak_time = mid_ts
            last_peak_val  = mid_val
            rr_intervals.clear()
            return None

        rr_intervals.append(rr)
        last_peak_time = mid_ts
        last_peak_val  = mid_val

        if len(rr_intervals) >= 2:
            avg_rr = sum(rr_intervals) / len(rr_intervals)
            return int(60.0 / avg_rr)
    else:
        last_peak_time = mid_ts
        last_peak_val  = mid_val

    return None


# ── BLE packet handler ────────────────────────────────────────────────────────

def parse_ppg(sender, data):
    global last_sent_bpm
    try:
        ts_now = time.time()

        for i in range(0, len(data) // 4, 2):
            val = struct.unpack_from('<i', data, i * 4)[0]
            bpm = detect_peak(ts_now, val)

            if bpm and 55 <= bpm <= 180:
                bpm_history.append(bpm)
                status = classify_bpm(bpm)
                ts_ms  = int(ts_now * 1000)
                rr_ms  = int(rr_intervals[-1] * 1000) if rr_intervals else 0

                prefix = ("🔴" if status == "INTENSE_SPIKE"
                          else "🟡" if status == "ELEVATED"
                          else "🟢")

                if bpm != last_sent_bpm:
                    print(f"{prefix} [{time.strftime('%H:%M:%S')}]  "
                          f"BPM: {bpm:3d}  RR: {rr_ms}ms  |  {status}")
                    last_sent_bpm = bpm

                    send_to_receiver({
                        "timestamp_ms" : ts_ms,
                        "bpm"          : bpm,
                        "rr_ms"        : rr_ms,
                        "status"       : status
                    })

                with open(MASTER_CSV, 'a', newline='') as f:
                    csv.writer(f).writerow([ts_ms, bpm, rr_ms, status])

    except Exception as e:
        print(f"[ERR] {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print("=" * 55)
    print("  HealthyPi × Valorant — BPM + HRV Stream")
    print("=" * 55)
    print(f"  Watch  : {WATCH_MAC}")
    print(f"  Channel: PPG ch1 (cd5c1525)")
    print(f"  Output : {MASTER_CSV}\n")
    print(f"  Connecting...\n")

    async with BleakClient(WATCH_MAC) as client:
        print("  Connected! Starting PPG stream...\n")
        await client.start_notify(DATA_UUID, parse_ppg)

        print("  Calibrating baseline", end="", flush=True)
        while len(bpm_history) < 5:
            await asyncio.sleep(1)
            print(".", end="", flush=True)

        baseline = sum(bpm_history) / len(bpm_history)
        print(f"\n  ✅ Baseline ready — avg BPM: {baseline:.0f}")
        print("  ▶  You can now start your Valorant match!\n")

        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    with open(MASTER_CSV, 'w', newline='') as f:
        csv.writer(f).writerow(["timestamp_ms", "bpm", "rr_ms", "status"])
    asyncio.run(main())
