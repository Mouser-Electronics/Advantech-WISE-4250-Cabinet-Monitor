#!/usr/bin/env python3
"""
wise4250_cabinet_coordinator.py (V7 - Option A Channel Mapping)
Advantech WISE-4250 Industrial Cabinet Monitoring Edge Coordinator & REST Provisioner
Author: Joseph Downing, Mouser Electronics
Tested Firmware Baseline: WISE-4250 Fw A1.01 B04 / A3.00 B01
Hardware Notes:
  - DI 0 (Potter AMS-7-B magnetic switch, held closed when door is shut) and
    DI 4 (Banner SSA-EB1P-02 NC contact 11-12, closed when armed, opens when pushed)
    use hardware Invert Signal (Inv=1) so Closed/Armed = 0 and Open/Pushed = 1.
  - DI 4 uses Low-to-High Latch mode (Md=2): pushing the button sets Lch=1 and Stat=1;
    pulling/twisting the actuator to re-arm returns Stat=0 while keeping Lch=1.
    The coordinator requires BOTH reset_latched == 1 AND reset_active == 0 to clear
    a critical alarm after the initiating fault clears.
  - Digital filter is set to 200 (20.0ms at 0.1ms/unit) to match the 20ms contact
    bounce specification of the Banner SSA-EB1P-02 pushbutton.
  - DO 0..DO 1 are owned exclusively by the WISE-4250-S232 P2P engine.
  - DO 2..DO 6 are owned exclusively by the Coordinator (with WDT FSV fallback).
  - Hardwired Leak-Inhibit Interlock: The +12VDC feed to the parallel NO contacts
    (terminals 11 COM and 14 NO) of DO 0 (Schneider RSL relay) and DO 6 (IDEC RV8H-L-D24) 
    passes through an isolated NC leak-inhibit contact that physically opens whenever a leak occurs (DI 3 = 1).
"""
import argparse
import csv
import os
import sys
import time
from datetime import datetime, timezone
import requests
from requests.auth import HTTPBasicAuth

# ==============================================================================
# 1. NETWORK, AUTHENTICATION & UBIDOTS CONFIGURATION
# ==============================================================================
S232_IP = os.getenv("WISE_S232_IP", "192.168.50.101")
S252_IP = os.getenv("WISE_S252_IP", "192.168.50.102")
WISE_USER = os.getenv("WISE_USER", "root")
WISE_PASS = os.getenv("WISE_PASS")
UBIDOTS_TOKEN = os.getenv("UBIDOTS_TOKEN")

if not WISE_PASS:
    raise RuntimeError("Set the WISE_PASS environment variable before running.")

UBIDOTS_DEVICE_LABEL = "wise-4250-cabinet-monitor"
UBIDOTS_URL = f"https://industrial.api.ubidots.com/api/v1.6/devices/{UBIDOTS_DEVICE_LABEL}/"

# ==============================================================================
# 2. ENVIRONMENTAL SETPOINTS & TIMING PARAMETERS
# ==============================================================================
TEMP_HIGH_LIMIT_C = 30.0         # Channel 0 High Alarm Threshold (Celsius)
RH_HIGH_LIMIT_PCT = 60.0         # Channel 1 High Alarm Threshold (% RH)
POLL_INTERVAL_SEC = 2.0          # 2.0s coordinator poll (S232 updates every 5.0s)
CSV_LOG_FILE = "wise4250_cabinet_telemetry_log.csv"

auth = HTTPBasicAuth(WISE_USER, WISE_PASS)
latched_alarm_code = 0  # 0=Normal, 1=Warning, 2=RH+Door, 3=Temp+FanFault, 4=Leak


# ==============================================================================
# 3. AUTOMATED REST API NODE PROVISIONING (--provision)
# ==============================================================================
def provision_nodes():
    """
    Alternative to manual web UI setup: pushes channel tags, 5.0s measurement
    intervals, alarm thresholds, 20.0ms DI debounce filters, Invert Signal (Inv=1)
    on DI 0 and DI 4, Low-to-High Latch on DI 4, and FSV states on DO 0..DO 6.
    """
    print(f"[*] Provisioning WISE-4250-S232 at http://{S232_IP} ...")
    s232_sensor_cfg = {
        "SCfg": [
            {
                "Ch": 0,
                "En": 1,
                "Rng": 4096,         # 0x1000 = Temperature (C)
                "EnLA": 0,
                "EnHA": 1,
                "LAMd": 0,
                "HAMd": 0,           # 0 = Momentary Alarm Mode
                "LoA": "0.0",
                "HiA": f"{TEMP_HIGH_LIMIT_C:.1f}",
                "Dev": "0.5",
                "PItv": 500,         # 500 * 10ms = 5.0s measurement interval
                "Val": "0.0",
                "Tag": "Cabinet_Temp_C"
            },
            {
                "Ch": 1,
                "En": 1,
                "Rng": 4128,         # 0x1020 = Humidity (% RH)
                "EnLA": 0,
                "EnHA": 1,
                "LAMd": 0,
                "HAMd": 0,           # 0 = Momentary Alarm Mode
                "LoA": "0.0",
                "HiA": f"{RH_HIGH_LIMIT_PCT:.1f}",
                "Dev": "2.0",
                "PItv": 500,         # 500 * 10ms = 5.0s measurement interval
                "Val": "0.0",
                "Tag": "Cabinet_RH_Pct"
            }
        ]
    }
    r1 = requests.patch(f"http://{S232_IP}/sensor_config/slot_0", json=s232_sensor_cfg, auth=auth, timeout=5)
    r1.raise_for_status()
    print("    [+] WISE-4250-S232 Sensor Channels 0 & 1 configured.")

    print(f"[*] Provisioning WISE-4250-S252 Digital Inputs at http://{S252_IP} ...")
    di_tags_modes = [
        (0, 0, 1, "Cabinet_Door_Sw"),    # Mode 0 = DI, Inv = 1 (Door Closed=0, Open=1)
        (1, 0, 0, "Cooling_Fan_Stat"),   # Mode 0 = DI, Inv = 0 (Fan Off=0, Running=1)
        (2, 0, 0, "Filter_Dirty_Warn"),  # Mode 0 = DI, Inv = 0 (Clean=0, Clogged=1)
        (3, 0, 0, "Leak_Fault_Sensor"),  # Mode 0 = DI, Inv = 0 (Dry=0, Leak=1)
        (4, 2, 1, "Manual_Alarm_Rst"),   # Mode 2 = LowToHighLatch, Inv = 1 (Armed=0, Pushed=1)
    ]
    s252_di_cfg = {
        "DICfg": [
            {
                "Ch": ch,
                "En": 1,
                "Md": md,
                "Inv": inv,
                "Fltr": 1,           # Enable Digital Debounce Filter
                "FtLo": 200,         # 200 * 0.1ms = 20.0ms (matches SSA-EB1P-02 20ms bounce spec)
                "FtHi": 200,         # 200 * 0.1ms = 20.0ms
                "Tag": tag
            }
            for ch, md, inv, tag in di_tags_modes
        ]
    }
    r2 = requests.patch(f"http://{S252_IP}/di_config/slot_0", json=s252_di_cfg, auth=auth, timeout=5)
    r2.raise_for_status()
    print("    [+] WISE-4250-S252 Digital Inputs DI 0..DI 4 configured (20.0ms filter).")

    print(f"[*] Provisioning WISE-4250-S252 Digital Outputs at http://{S252_IP} ...")
    # DO 0..DO 1 are owned by S232 P2P rules; DO 2..DO 6 are owned by the Coordinator & WDT FSV
    do_tags_fsv = [
        (0, 0, "P2P_Temp_Fan_Cmd"),   # S232 P2P Rule 0 (Schneider RSL Relay); FSV = 0
        (1, 0, "P2P_RH_Warn_Cmd"),    # S232 P2P Rule 1 status output; FSV = 0
        (2, 0, "LED_Green_Normal"),   # Adafruit 2993 Green wire; FSV = 0
        (3, 1, "LED_Amber_Warn"),     # Adafruit 2993 Yellow wire; FSV = 1 (Comm-loss warning)
        (4, 0, "LED_Red_Alarm"),      # Adafruit 2993 Red wire; FSV = 0
        (5, 0, "Alarm_Buzzer"),       # Adafruit 2993 Orange wire; FSV = 0
        (6, 1, "Aux_Fan_Relay"),      # IDEC RV8H-L-D24 Coil A2-; FSV = 1 (Comm-loss cooling request)
    ]
    s252_do_cfg = {
        "DOCfg": [
            {
                "Ch": ch,
                "En": 1,
                "Md": 0,
                "FSV": fsv,
                "Tag": tag
            }
            for ch, fsv, tag in do_tags_fsv
        ]
    }
    r3 = requests.patch(f"http://{S252_IP}/do_config/slot_0", json=s252_do_cfg, auth=auth, timeout=5)
    r3.raise_for_status()
    print("    [+] WISE-4250-S252 Digital Outputs DO 0..DO 6 configured.")
    print("[✓] Provisioning complete!")


# ==============================================================================
# 4. RUNTIME TELEMETRY POLLING & STATE MACHINE EVALUATION
# ==============================================================================
def read_s232_environment():
    """GET /sensor_value/slot_0 from WISE-4250-S232 (Ch 0: Temp C, Ch 1: RH %)."""
    url = f"http://{S232_IP}/sensor_value/slot_0"
    resp = requests.get(url, auth=auth, timeout=3)
    resp.raise_for_status()
    channels = {ch["Ch"]: ch["EgF"] for ch in resp.json().get("SVal", [])}
    return float(channels.get(0, 0.0)), float(channels.get(1, 0.0))

def read_s252_inputs():
    """
    GET /di_value/slot_0 from WISE-4250-S252 (DI 0..DI 4).
    Evaluates DI 4 Lch (reset_latched) and Stat (reset_active) separately so the
    coordinator can confirm the Banner SSA-EB1P-02 button was both pushed (Lch == 1)
    and re-armed (Stat == 0) before clearing a latched alarm.
    """
    url = f"http://{S252_IP}/di_value/slot_0"
    resp = requests.get(url, auth=auth, timeout=3)
    resp.raise_for_status()
    di_list = resp.json().get("DIVal", [])
    di_map = {ch["Ch"]: ch for ch in di_list}
    return {
        "door_open": int(di_map.get(0, {}).get("Stat", 0)),
        "fan_running": int(di_map.get(1, {}).get("Stat", 0)),
        "filter_warn": int(di_map.get(2, {}).get("Stat", 0)),
        "leak_fault": int(di_map.get(3, {}).get("Stat", 0)),
        "reset_latched": int(di_map.get(4, {}).get("Lch", 0)),
        "reset_active": int(di_map.get(4, {}).get("Stat", 0)),
    }

def clear_s252_reset_latch():
    """PATCH /di_value/slot_0/ch_4 to clear the Low-to-High Latch on DI 4."""
    url = f"http://{S252_IP}/di_value/slot_0/ch_4"
    resp = requests.patch(url, json={"Lch": 0}, auth=auth, timeout=3)
    resp.raise_for_status()

def write_s252_coordinator_outputs(do_states):
    """
    PATCH /do_value/slot_0 on WISE-4250-S252 for Coordinator-owned channels
    (DO 2..DO 6 only), leaving P2P-owned channels (DO 0..DO 1) untouched.
    """
    url = f"http://{S252_IP}/do_value/slot_0"
    payload = {
        "DOVal": [{"Ch": ch_idx + 2, "Val": val} for ch_idx, val in enumerate(do_states)]
    }
    resp = requests.patch(url, json=payload, auth=auth, timeout=3)
    resp.raise_for_status()

def evaluate_cabinet_logic(temp_c, rh_pct, di):
    """Evaluate multi-sensor cabinet rules and return (alarm_code, [DO2..DO6])."""
    global latched_alarm_code
    high_temp = temp_c > TEMP_HIGH_LIMIT_C
    high_rh = rh_pct > RH_HIGH_LIMIT_PCT

    # Critical alarm priority: State 4 (Leak) > State 3 (Temp+FanOff) > State 2 (RH+DoorOpen)
    active_critical = 0
    if di["leak_fault"] == 1:
        active_critical = 4
    elif high_temp and di["fan_running"] == 0:
        active_critical = 3
    elif high_rh and di["door_open"] == 1:
        active_critical = 2

    if active_critical > 0:
        latched_alarm_code = active_critical
        if di["reset_latched"] == 1:
            clear_s252_reset_latch()
    elif latched_alarm_code >= 2:
        if di["reset_latched"] == 1 and di["reset_active"] == 0:
            latched_alarm_code = 0
            clear_s252_reset_latch()

    if latched_alarm_code == 0:
        if high_rh or high_temp or di["filter_warn"] == 1:
            current_state = 1  # Warning State
        else:
            current_state = 0  # Normal State
    else:
        current_state = latched_alarm_code

    if current_state < 2 and di["reset_latched"] == 1 and di["reset_active"] == 0:
        clear_s252_reset_latch()

    # Map state to Coordinator-owned outputs [DO2_Green, DO3_Amber, DO4_Red, DO5_Buzzer, DO6_AuxFanRelay]
    if current_state == 0:
        outputs = [1, 0, 0, 0, 0]
    elif current_state == 1:
        # DO 3 (Amber) illuminates for all warnings; DO 6 (Aux Fan) energizes only for thermal/humidity warnings
        outputs = [0, 1, 0, 0, 1 if (high_rh or high_temp) else 0]
    elif current_state == 2:
        outputs = [0, 0, 1, 0, 1]
    elif current_state == 3:
        outputs = [0, 0, 1, 1, 1]
    else:  # current_state == 4 (Leak Alarm: DO 6 forced OFF and upstream NC contact opens +12VDC feed)
        outputs = [0, 0, 1, 1, 0]

    return current_state, outputs

def publish_to_ubidots(payload):
    """
    Non-critical telemetry upload to Ubidots: checks HTTP status and logs errors
    without blocking local cabinet protection logic.
    """
    if not UBIDOTS_TOKEN:
        return
    headers = {"X-Auth-Token": UBIDOTS_TOKEN, "Content-Type": "application/json"}
    try:
        resp = requests.post(UBIDOTS_URL, json=payload, headers=headers, timeout=4)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[Cloud Warning] Ubidots telemetry upload failed (local control unaffected): {exc}")

def run_coordinator():
    """Main polling, local evaluation, CSV logging, and Ubidots publishing loop."""
    with open(CSV_LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow([
                "Timestamp_UTC", "Temp_C", "RH_Pct", "Door_Open",
                "Fan_Running", "Filter_Warn", "Leak_Fault", "Alarm_State",
                "Coordinator_Fan_Request"
            ])

        print("Starting WISE-4250 Cabinet Coordinator... Press Ctrl+C to stop.")
        while True:
            try:
                temp_c, rh_pct = read_s232_environment()
                di = read_s252_inputs()
                state_code, do_vals = evaluate_cabinet_logic(temp_c, rh_pct, di)
                write_s252_coordinator_outputs(do_vals)

                ts_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                writer.writerow([
                    ts_iso, f"{temp_c:.2f}", f"{rh_pct:.2f}",
                    di["door_open"], di["fan_running"], di["filter_warn"],
                    di["leak_fault"], state_code, do_vals[4]
                ])
                f.flush()

                ubidots_payload = {
                    "temperature": round(temp_c, 2),
                    "humidity": round(rh_pct, 2),
                    "door_status": di["door_open"],
                    "fan_status": di["fan_running"],
                    "filter_warning": di["filter_warn"],
                    "leak_status": di["leak_fault"],
                    "alarm_state": state_code,
                    "coordinator_fan_request": do_vals[4],
                }
                publish_to_ubidots(ubidots_payload)

                print(
                    f"[{ts_iso}] Temp={temp_c:.2f}C | RH={rh_pct:.2f}% | "
                    f"DI={di} | State={state_code} | DO2..6={do_vals}"
                )
            except KeyboardInterrupt:
                print("\n[!] Stopping coordinator.")
                sys.exit(0)
            except Exception as exc:
                print(f"[Local Polling Warning] Cycle error: {exc}")

            time.sleep(POLL_INTERVAL_SEC)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WISE-4250 Cabinet Coordinator")
    parser.add_argument(
        "--provision",
        action="store_true",
        help="Push channel tags, alarms, 20ms filters, Inv=1, and FSV settings via REST API"
    )
    args = parser.parse_args()

    if args.provision:
        provision_nodes()
    else:
        run_coordinator()
