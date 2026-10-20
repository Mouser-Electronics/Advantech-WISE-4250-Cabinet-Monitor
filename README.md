# Advantech WISE-4250 Wireless Industrial Cabinet Monitoring System

This repository contains the edge coordinator source code, RESTful API provisioning script, hardware pinout documentation, engineering design notes, and troubleshooting guide for the **Mouser Electronics** hardware project: **Industrial Cabinet Monitoring: Build a Wireless IoT System**.

The proof-of-concept system uses the **Advantech WISE-4250** dual-band Wi-Fi 5 (IEEE 802.11a/b/g/n/ac) wireless I/O platform and an **Advantech ICR-2545W** industrial cellular and Wi-Fi router to monitor control cabinet temperature and relative humidity (RH), track discrete enclosure switches, trigger local stack-light and dual interface-relay outputs via AES-128 encrypted Peer-to-Peer (P2P) rules and combinational edge logic, log timestamped data points to nonvolatile circular flash memory, and publish telemetry to an **Ubidots** cloud dashboard.

> **Safety and Scope Notice:** This project is intended as a controlled bench proof of concept for engineers experienced with industrial control wiring and network configuration. Installation in an operating control cabinet must comply with applicable electrical codes, enclosure ratings, conductor separation practices, equipment instructions, cybersecurity policies, and machinery safety procedures. Always de-energize and verify that all AC mains and DC circuits are de-energized before wiring, and use grounded electrostatic-discharge (ESD) handling procedures (such as a grounded wrist strap) when touching exposed electronics.

---

## Repository Contents

* `wise4250_cabinet_coordinator.py` *(Version 5)* — Python 3 edge coordinator script that polls the WISE-4250-S232 and WISE-4250-S252 RESTful JSON endpoints every `2.0s`, evaluates the cabinet alarm state machine, drives coordinator-owned sink outputs (`DO 0`–`DO 4`), discards premature reset gestures made while a critical fault remains active, records a local timestamped CSV log (`wise4250_cabinet_event_log.csv`), and publishes live telemetry to Ubidots. Includes a `--provision` CLI flag to automatically configure channel tags, `5.0s` measurement intervals, alarm limits, `20.0ms` digital debounce filters, hardware signal inversion (`Inv=1`) on `DI 0` and `DI 4`, `Low to High Latch` mode on `DI 4`, and Fail-Safe Value (`FSV`) settings over Wi-Fi.
* `configs/` *(optional backup directory)* — Sanitized `.cfg` and `.p2p` configuration backup files exported from the WISE-4250-S232 and WISE-4250-S252 HTML5 web interfaces.

---

## Hardware Bill of Materials (BOM)

| Manufacturer | Mouser Part Number | Manufacturer Part Number | Project Function | Qty |
| :--- | :--- | :--- | :--- | :---: |
| **Advantech** | `923-WISE-4250-S232` | `WISE-4250-S232` | Dual-Band Wi-Fi 5 Wireless I/O Module with Temperature & Humidity Sensor (-25°C to 70°C, 0% to 100% RH) | 1 |
| **Advantech** | `923-WISE-4250-S252` | `WISE-4250-S252` | Dual-Band Wi-Fi 5 Wireless I/O Module with 12 Digital Inputs & 12 Digital Outputs | 1 |
| **Advantech** | `923-ICR-2545W` | `ICR-2545W` | Industrial Cellular and IEEE 802.11ac/a/b/g/n Dual-Band Wi-Fi Router | 1 |
| **Advantech** | `923-IPS-D22A60W24V-A` | `IPS-D22A60W24V-A` | 60W, 24VDC (2.50A) DIN-Rail Power Supply (24VDC Control Rail) | 1 |
| **Phoenix Contact** | `651-2902999` | `2902999` (`UNO-PS/1AC/12DC/55W`) | 55W, 12VDC (4.60A) DIN-Rail Power Supply (12VDC Auxiliary Load Rail) | 1 |
| **Qualtek** | `562-211011-01` | `211011-01` | NEMA 5-15P to Blunt-Cut Stripped 18AWG/3C SVT AC Mains Power Cord, 1.83m, 125VAC, 10A | 2 |
| **IDEC** | `199-RV8HLD24` | `RV8H-L-D24` | 6mm Slim Electromechanical Interface Relay & DIN-Mount Screw-Terminal Socket, 24VDC Coil, SPDT 6A (`DO 4` Coordinator Relay & `DO 5` P2P Relay) | 2 |
| **Same Sky** | `179-CBM7525C145494` | `CBM-7525C-145-494` | 12VDC Brushless DC Cabinet Cooling Blower, 75mm × 75mm × 25mm, 13.35CFM, 0.58A Typ / 0.70A Max | 1 |
| **Adafruit** | `485-2993` | `2993` | Red, Yellow, and Green Alert Tower Light with Continuous Buzzer, 12VDC Common Anode | 1 |
| **Potter / Amseco** | `507-AMS-7B` | `AMS-7-B` | Mini Surface/Press-Fit Magnetic Door Contact Switch, Form A (Normally Open), Brown | 1 |
| **Banner Engineering** | `778-SSA-EB1P-02` | `SSA-EB1P-02` | 30mm Panel-Mount, 40mm Mushroom-Style Latching Pushbutton with Two Normally Closed (NC) Contacts | 1 |

**Supporting Bench & Enclosure Items (Not in BOM):**
* 2× Single-pole, single-throw (SPST) dry-contact toggle switches (simulating primary fan status on `DI 1` and filter warning on `DI 2`)
* 1× Double-pole (DPST/DPDT) toggle or float switch for simulating the bottom-pan leak sensor (providing one Normally Open contact for `DI 3` and one isolated Normally Closed leak-inhibit contact in series with the `+12VDC` blower relay supply feed)
* Standard 35mm symmetrical DIN rail, DIN-rail end brackets, 0.5mm² to 2.5mm² (20AWG to 14AWG) stranded copper hookup wire with insulated ferrules, rated AC and DC terminal distribution blocks, Category 6 Ethernet patch cable, Torx T8 screwdriver, and flathead terminal screwdriver

---

## Dual-Rail Power Budget & Supporting Component Specifications

### 1. Dual-Voltage DIN-Rail Power Architecture
* **24VDC Control Rail (`Advantech IPS-D22A60W24V-A`):** Accepts 85VAC to 264VAC input and provides a regulated 24VDC, 2.50A, 60.0W output bus with over-voltage, over-current, short-circuit, and over-temperature protection. The maximum connected 24VDC load is **10.40W (0.433A)**, comprising:
  * `WISE-4250-S232`: `1.60W` at `24VDC`
  * `WISE-4250-S252`: `1.60W` at `24VDC`
  * `ICR-2545W` Router (`9VDC` to `48VDC` input range): `2.90W` idle / `4.50W` average / `6.70W` maximum
  * 2× `IDEC RV8H-L-D24` 24VDC Interface Relays (`DO 4` and `DO 5`): `10.6mA` / `0.25W` each (`21.2mA` / `0.50W` combined)
  * **Available 24VDC Headroom:** **49.60W (82.7%)** of supply capacity, with `24VDC` sitting comfortably inside the router's `9VDC` to `48VDC` operating window.
* **12VDC Auxiliary Load Rail (`Phoenix Contact 2902999 / UNO-PS/1AC/12DC/55W`):** Accepts 85VAC to 264VAC input and provides a regulated 12VDC, 4.60A, 55.0W output bus. The maximum connected 12VDC load is **13.20W (1.10A)**, comprising:
  * `Same Sky CBM-7525C-145-494` 12VDC Blower: `0.58A` (`6.96W`) typical / `0.70A` (`8.40W`) maximum
  * `Adafruit 2993` 12VDC Alert Tower Light & Buzzer: Bounded by the `100mA` per-channel sink limit of `DO 0` through `DO 3` (`≤0.40A` / `4.80W` combined)
  * **Available 12VDC Headroom:** **41.80W (76.0%)** of supply capacity.

### 2. Supporting Field Component Specifications
* **Potter / Amseco `AMS-7-B` Magnetic Door Contact (`507-AMS-7B`):** Miniature surface- or press-fit Alnico 5 magnetic reed switch with 304mm (12in), 22AWG leads and a 19mm (0.75in) operating gap. Uses a Form A (Normally Open) contact rated at 10VA (1.0A carry, 0.5A switching, 200VDC breakdown) that is held closed when the cabinet door magnet is aligned and opens when the door opens.
* **Banner Engineering `SSA-EB1P-02` Latching Pushbutton (`778-SSA-EB1P-02`):** 30mm panel-mount, 40mm mushroom-style mechanical pushbutton (push-to-latch, pull- or twist-clockwise-to-release) equipped with two Normally Closed (NC) gold-plated silver contacts (`11-12` and `21-22`, rated 5A thermal current, 1mA at 5VAC/DC minimum load, with a specified `20ms` contact bounce time). When armed, contact `11-12` is closed; when pushed, contact `11-12` opens until manually rearmed. In this bench proof of concept, the `SSA-EB1P-02` serves strictly as a manual alarm-reset input rather than a machine-safeguarding emergency stop device.
* **Dual IDEC `RV8H-L-D24` Slim Interface Relays (`199-RV8HLD24`, Qty 2) & Hardwired Leak-Inhibit Interlock:** Each pre-assembled 6mm DIN-rail electromechanical SPDT (`1C`) relay and screw-terminal socket features a 24VDC coil (`10.6mA` rated current, `2,270Ω` coil resistance, `0.25W` power consumption), built-in green LED indicator, coil surge-suppression diode, and gold-plated silver-nickel contacts (`11` COM, `14` NO, `12` NC) rated for `6A` at `30VDC` or `250VAC` resistive loads. Using two separate relays allows the Python coordinator (`DO 4`) and the decentralized `WISE-4250-S232` P2P engine (`DO 5`) to command the 12VDC cooling blower independently without software write collisions. Verify relay suitability for the blower's DC electronic-motor load and startup current (the nominal `6A` rating should not be interpreted solely as a resistive-load allowance). Routing the `+12VDC` feed to terminal `11` (`COM`) of both relays through the isolated Normally Closed (`NC`) leak-inhibit pole of the double-pole leak switch guarantees that an active leak physically opens the blower power path upstream of both `DO 4` and `DO 5`.
* **Adafruit `2993` 12VDC Alert Tower Light (`485-2993`) & Same Sky `CBM-7525C-145-494` 12VDC Blower (`179-CBM7525C145494`):** The tower light integrates red, yellow, and green LED segments plus a continuous piezo buzzer fed by a common `+12VDC` **brown wire** and switched to ground via individual color-coded control leads (**green wire** = green LED, **yellow wire** = yellow LED, **red wire** = red LED, **orange wire** = continuous buzzer). The Same Sky brushless DC blower (75.8mm × 75.7mm × 25mm frame, omniCOOL™ bearing) operates from 10.8VDC to 13.2VDC (12VDC nominal, **red wire** `+Vin`, **black wire** `-Vin`) to deliver 13.35CFM airflow at 4,500RPM with auto-restart, reverse-polarity protection, and an integrated soft-start function.

---

## Network Architecture & IP Addressing

In factory-default `AP Mode` (or `Initial Mode`), WISE-4250 modules use the static IP address `192.168.1.1`. Configure the **Advantech ICR-2545W** router LAN on the `192.168.10.0/24` subnet to prevent IP conflicts during commissioning:

| Device | Hostname / Customized Name | IP Address | Role & Protocols |
| :--- | :--- | :--- | :--- |
| **Advantech ICR-2545W** | `ICR-2545W_GW` | `192.168.10.1` | Wi-Fi AP (`SSID: WISE_Cabinet_Net`, WPA3), 10/100Mbps LAN (`ETH0`), DHCP & NTP Server |
| **Engineering Host PC** | `Engineering_Host` | `192.168.10.50` | Connected via Cat 6 Ethernet to `ETH0`; runs `wise4250_cabinet_coordinator.py` |
| **Advantech WISE-4250-S232** | `Cabinet_Env_S232` | `192.168.10.101` | Temperature (`Ch 0`) & RH (`Ch 1`) node, Circular Flash Logger, P2P Sender |
| **Advantech WISE-4250-S252** | `Cabinet_DIO_S252` | `192.168.10.102` | 12DI / 12DO node, Circular Flash Logger, P2P Receiver (UDP Port `5048`) |

---

## Hardware Wiring & Terminal Pinout Map

### 1. Advantech `ICR-2545W` Router Power & Ethernet Wiring
1. **6-Pin Power/IO Connector (`CON-ICR2-6-PWR`):** Locate the green 6-pin plug-in screw terminal block on the left side of the `ICR-2545W` chassis. Connect the positive **`+` (`PWR`)** terminal to the `+24VDC` distribution bus (`IPS-D22A60W24V-A`) and the negative **`-` (`GND`)** terminal to the shared `0V` common reference block (leaving the auxiliary router `DI`/`DO` pins unconnected).
2. **Chassis Ground & Antennas:** Connect the router's side **Grounding Screw** to the protective earth (`FG/PE`) ground bar, and thread the Wi-Fi antenna onto the `R-SMA` Wi-Fi connector (and cellular antennas onto `ANT`/`DIV` if using LTE WAN backhaul).
3. **Ethernet LAN Connection:** Plug one end of the Category 6 Ethernet patch cable into one of the three switched **`ETH0`** RJ45 ports (`10/100Mbps`) on the front panel of the `ICR-2545W` and the other end into the engineering host PC (`192.168.10.50`).

### 2. `WISE-4250-S252` Internal DIP Switch Settings
* **Rear Operation Mode Switch (`SW1` on both `WISE-4250-S232` and `WISE-4250-S252`):** Set Position 1 (`P1`) of `SW1` to **`ON` (`Normal Mode`)** (`P1 = OFF` forces factory-recovery `Initial Mode` at `192.168.1.1`).
* **Internal Cartridge Contact-Type Switches (`SW1`, `SW2`, and `SW3` inside `WISE-S252`):** For **Dry Contact** operation across all three four-channel input banks (`DI 0–3`, `DI 4–7`, and `DI 8–11`), set **`SW1-1`, `SW2-1`, and `SW3-1` to `ON`**, and ensure **`SW1-2`, `SW2-2`, and `SW3-2` are set to `OFF`**.

### 3. Complete Node Terminal Pinout & Logic Mapping

| Module | Terminal Row & Pin | Reference Pin | Channel Tag (`Max 21 chars`) | Connected Field Device / Part Number | Electrical & Logic State Mapping / FSV |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WISE-4250-S232** | Power `+Vs` / `-Vs` | `+24VDC` / `0V` | `Cabinet_Env_S232` | 24VDC Power Input & Built-In SHT41-AD1F Sensor | `Ch 0`: Temp (`>30.0°C` High Alarm); `Ch 1`: RH (`>60.0%` RH High Alarm) |
| **WISE-4250-S252** | Upper Row Pin 14 (`+Vs`), Pin 15 (`-Vs`) | `+24VDC` / `0V` | `Cabinet_DIO_S252` | 24VDC Module Power Input (`IPS-D22A60W24V-A`) | 10VDC to 50VDC range (`1.60W` at `24VDC`) |
| **WISE-4250-S252** | Lower Row Pin 1 (`DI 0`) | Lower Pin 5 (`DCOM0`) | `Cabinet_Door_Sw` | Potter `AMS-7-B` Form A (N.O.) Magnetic Door Switch | Closed door holds reed closed; `Inv=1` maps Door Closed=`0`, Door Open=`1` |
| **WISE-4250-S252** | Lower Row Pin 2 (`DI 1`) | Lower Pin 5 (`DCOM0`) | `Cooling_Fan_Stat` | Primary Fan Running Status Toggle Switch (SPST) | `0` = Primary Fan Off (`Open`) / `1` = Primary Fan Running (`Closed to DCOM0`) |
| **WISE-4250-S252** | Lower Row Pin 3 (`DI 2`) | Lower Pin 5 (`DCOM0`) | `Filter_Dirty_Warn` | Intake Filter Differential Toggle Switch (SPST) | `0` = Filter Clean (`Open`) / `1` = Filter Clogged Warning (`Closed to DCOM0`) |
| **WISE-4250-S252** | Lower Row Pin 4 (`DI 3`) | Lower Pin 5 (`DCOM0`) | `Leak_Fault_Sensor` | Bottom-Pan Leak Switch (DPST/DPDT Pole 1 `NO`) | `0` = Dry (`Open`) / `1` = Leak Detected (`Closed to DCOM0`); Pole 2 `NC` inhibits `+12VDC` blower feed |
| **WISE-4250-S252** | Lower Row Pin 6 (`DI 4`) | Lower Pin 10 (`DCOM1`) | `Manual_Alarm_Rst` | Banner `SSA-EB1P-02` Pushbutton (`NC` Contact `11-12`) | Armed=Closed, Pushed=Open; `Inv=1` + `Low to High Latch` records push (`Lch=1`) & re-arm (`Stat=0`) |
| **WISE-4250-S252** | Upper Row Pin 1 (`DO 0`) | Upper Pin 13 (`DGND`) | `LED_Green_Normal` | Adafruit `2993` Tower Light — **Green Wire** (`12VDC`) | Coordinator owned; Brown wire to `+12VDC`; Sink `1` = Green On; `FSV = 0` (Comm-loss Off) |
| **WISE-4250-S252** | Upper Row Pin 2 (`DO 1`) | Upper Pin 13 (`DGND`) | `LED_Amber_Warn` | Adafruit `2993` Tower Light — **Yellow Wire** (`12VDC`) | Coordinator owned; Brown wire to `+12VDC`; Sink `1` = Yellow On; `FSV = 1` (Comm-loss On) |
| **WISE-4250-S252** | Upper Row Pin 3 (`DO 2`) | Upper Pin 13 (`DGND`) | `LED_Red_Alarm` | Adafruit `2993` Tower Light — **Red Wire** (`12VDC`) | Coordinator owned; Brown wire to `+12VDC`; Sink `1` = Red On; `FSV = 0` (Comm-loss Off) |
| **WISE-4250-S252** | Upper Row Pin 4 (`DO 3`) | Upper Pin 13 (`DGND`) | `Alarm_Buzzer` | Adafruit `2993` Tower Light — **Orange Wire** (`12VDC`) | Coordinator owned; Brown wire to `+12VDC`; Sink `1` = Buzzer On; `FSV = 0` (Comm-loss Off) |
| **WISE-4250-S252** | Upper Row Pin 5 (`DO 4`) | Upper Pin 13 (`DGND`) | `Aux_Fan_Relay` | IDEC `RV8H-L-D24` #1 Coil (`A2-`) Switching Blower | Coordinator owned; Coil `A1+` to `+24VDC`; Contacts `11-14` fed via Leak-Inhibit `NC` contact; `FSV = 1` |
| **WISE-4250-S252** | Upper Row Pin 6 (`DO 5`) | Upper Pin 13 (`DGND`) | `P2P_Temp_Fan_Cmd` | IDEC `RV8H-L-D24` #2 Coil (`A2-`) Switching Blower | P2P Rule `0` owned (`>30.0°C`); Coil `A1+` to `+24VDC`; Contacts `11-14` in parallel with `DO 4` behind Leak-Inhibit `NC`; `FSV = 0` |
| **WISE-4250-S252** | Upper Row Pin 7 (`DO 6`) | Upper Pin 13 (`DGND`) | `P2P_RH_Warn_Cmd` | Dedicated S232 P2P High-RH (`>60.0%`) Status Output | P2P Rule `1` owned (logical status demonstration on S252 DO page); `FSV = 0` |

---

## Engineering Notes & Design Considerations

1. **Dual Blower Relays (`DO 4` and `DO 5`), Hardwired Leak Inhibit, and Communication-Loss (`FSV`) Behavior:**
   * `DO 4` energizes the 24VDC coil (`A2-`) of the first **IDEC `RV8H-L-D24`** interface relay (`10.6mA`), while `DO 5` energizes the 24VDC coil (`A2-`) of the second **IDEC `RV8H-L-D24`** interface relay. Their isolated SPDT contacts (terminals `11` COM and `14` NO on both relays) are wired in parallel to switch `+12VDC` power from the Phoenix Contact `2902999` supply to the Same Sky `CBM-7525C-145-494` auxiliary cabinet cooling blower (`0.58A` typical, `0.70A` max).
   * During a `State 4` liquid-leak alarm, the coordinator intentionally de-energizes `DO 4` so the blower does not circulate moisture across cabinet electronics. Because the `WISE-4250-S232` P2P engine evaluates temperature independently of the `WISE-4250-S252` leak input, routing the `+12VDC` feed to terminal `11` (`COM`) of both relays through the isolated Normally Closed (`NC`) leak-inhibit pole of the double-pole leak switch ensures that an active leak physically opens the blower supply path upstream of both `DO 4` and `DO 5`—preventing blower operation even if temperature simultaneously exceeds `30.0°C`. If a different device (such as a drain pump or dehumidifier) is connected, its normal, alarm, and FSV states must be reassessed.
   * Setting `FSV = 1` on `DO 4` commands the relay output on after a `60s` communication-watchdog timeout to request auxiliary cooling, which represents a communication-loss response rather than a complete fail-safe cooling architecture. Applications requiring verified cooling must monitor fan tachometer feedback and evaluate power, relay, and airflow failure modes.
2. **Relative Humidity Measurement vs. Dew-Point Condensation:**
   * The `WISE-4250-S232` relative humidity measurement indicates environmental conditions associated with condensation risk; determining whether liquid condensation will form on a specific surface requires comparing the calculated dew point against the temperature of vulnerable enclosure surfaces, whereas the system's bottom-pan leak input (`DI 3`) detects accumulated moisture directly.
3. **Single-Owner Output Arbitration, Polling Cadence & Telemetry Semantics:**
   * Do not configure the Python coordinator, P2P rules, and watchdog logic as independent writers to the same digital output channel. In this architecture, the Python coordinator exclusively writes `DO 0` through `DO 4` during normal operation (with Communication WDT `FSV` providing loss-of-coordinator fallback on those five channels), while the `WISE-4250-S232` P2P engine exclusively writes `DO 5` (`P2P_Temp_Fan_Cmd`) and `DO 6` (`P2P_RH_Warn_Cmd`). In this bench build, `DO 6` demonstrates P2P high-humidity command transfer through the `WISE-4250-S252` output-status page; connect a properly rated indicator or interface relay if a physical high-humidity response is required.
   * The Python coordinator polls every `2.0s` to minimize latency for discrete input and output processing, while the `WISE-4250-S232` environmental channels update every `5.0s` (`PItv = 500`, with the hardware applying the smaller interval configured between `Channel 0` and `Channel 1`). Consequently, consecutive `2.0s` polls can return the same temperature and RH sample between sensor conversions.
   * The Ubidots variable `coordinator_fan_request` reports the coordinator's `DO 4` command only—not verified blower rotation, airflow, the upstream leak-inhibit contact state, or the `DO 5` P2P relay state.
4. **Nonvolatile Circular Flash Logging:**
   * Each WISE-4250 module includes nonvolatile flash memory storing more than 10,000 timestamped data points (samples) in a circular ring buffer. Leaving `Clear Log when Power Up` unchecked preserves previously committed log samples across power cycles, while changing any channel mode (`DI`, `Counter`, `Latch`, `DO`, `Pulse Output`) or modifying the `By Channel` / `By Sensor` logging masks automatically clears existing buffer memory to rebuild the internal log structure.

---

## Software Setup & Quick Start

### 1. Install Dependencies
Ensure Python 3.10 or newer is installed on your host computer, then install the `requests` library:
```bash
pip install requests
```

### 2. Export Environment Credentials
To prevent accidental deployment with hardcoded default passwords, `wise4250_cabinet_coordinator.py` requires `WISE_PASS` to be set as an environment variable before running (raising a `RuntimeError` if absent), while `UBIDOTS_TOKEN` is optional for cloud publishing:

**Linux / macOS (Bash/Zsh):**
```bash
export WISE_PASS="Your8CharRootPassword"
export UBIDOTS_TOKEN="BBUS-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

**Windows (PowerShell):**
```powershell
$env:WISE_PASS="Your8CharRootPassword"
$env:UBIDOTS_TOKEN="BBUS-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 3. Auto-Provision Module Channels via REST API (Optional Alternative to Manual Web UI Setup)
Once both modules have joined the `192.168.10.0/24` Wi-Fi network, you can automatically push all channel tags, `5.0s` (`500`) measurement intervals, `30.0°C` / `60.0%` RH high-alarm thresholds, `20.0ms` (`200`) digital debounce filters, `Invert Signal` (`Inv=1`) on `DI 0` and `DI 4`, `Low to High Latch` mode on `DI 4`, and `FSV` output states on `DO 0`–`DO 6` using the `--provision` flag (do not run both manual configuration and automated provisioning without reviewing the final settings):
```bash
python wise4250_cabinet_coordinator.py --provision
```
*(Note: `--provision` configures `/sensor_config/slot_0`, `/di_config/slot_0`, and `/do_config/slot_0`; network commissioning, SNTP time sync, Communication WDT, P2P rules, and Data Logger settings are configured through the web UI instructions in the project article.)*

### 4. Run the Edge Coordinator & Ubidots Publisher
Start the continuous `2.0s` polling, state-machine evaluation, local CSV logging, and Ubidots publishing loop:
```bash
python wise4250_cabinet_coordinator.py
```

---

## Cabinet Alarm State Machine & Validation Matrix

| Test Scenario | Input Stimulus (`S232` & `S252`) | Active State / Owner | Expected `WISE-4250-S252` Outputs | Verification Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **1. Normal Baseline** | Temp ≤ 30.0°C, RH ≤ 60.0%, `DI 0`=`0` (Door closed), `DI 1`=`1` (Fan on), `DI 2`=`0`, `DI 3`=`0` | `State 0` (Coordinator) | `DO 0` (Green)=`1`; `DO 1`–`DO 6`=`0` | Green tower LED lit; blower off; Ubidots shows `alarm_state = 0` |
| **2a. Filter Warning Only** | Toggle `DI 2` (`Filter_Dirty_Warn`) to `1` with Temp ≤ 30.0°C and RH ≤ 60.0% | `State 1` (Coordinator) | `DO 1` (Yellow)=`1`; `DO 4` (Blower Relay)=`0` | Yellow tower LED illuminates; auxiliary blower remains off |
| **2b. High RH or Temp Warning** | Raise RH > 60.0% (Door closed, `DI 0`=`0`) OR Temp > 30.0°C (Primary fan on, `DI 1`=`1`) | `State 1` (Coordinator + P2P) | `DO 1` (Yellow)=`1`, `DO 4` (Blower)=`1`; `DO 5`=`1` (if Temp>30°C), `DO 6`=`1` (if RH>60%) | Yellow tower LED and `CBM-7525C-145-494` blower activate; auto-clears when stimulus returns ≤ limit |
| **3. High RH + Open Door** | Raise RH > 60.0% and open door (`AMS-7-B` magnet separated, `DI 0`=`1`) | `State 2` (Coordinator Latched) | `DO 2` (Red)=`1`, `DO 4` (Blower)=`1`, `DO 6` (P2P RH)=`1` | Red tower LED and blower latch ON even after door closes and RH drops ≤ 60.0% |
| **4. High Temp + Fan Off** | Raise Temp > 30.0°C and set `DI 1` (`Cooling_Fan_Stat`) to `0` | `State 3` (Coordinator Latched) | `DO 2` (Red)=`1`, `DO 3` (Buzzer)=`1`, `DO 4` (Blower)=`1`, `DO 5` (P2P Temp)=`1` | Red tower LED, continuous buzzer, and auxiliary blower latch ON |
| **5. Active Leak Fault (+ High Temp Override Check)** | Toggle double-pole leak switch (`DI 3`=`1`, Leak-Inhibit `NC` open), including with Temp > 30.0°C (`DO 5`=`1`) | `State 4` (Coordinator Latched + Hardwired Inhibit) | `DO 2` (Red)=`1`, `DO 3` (Buzzer)=`1`, `DO 4`=`0`; upstream `NC` contact opens `+12VDC` blower feed | Red LED and buzzer latch ON; blower remains physically OFF even when `DO 5`=`1` is asserted by P2P |
| **6. Alarm Clear & Reset (+ Active-Fault Reset Discard)** | 1) Push & re-arm `SSA-EB1P-02` while fault is still active (`Lch` discarded). 2) Clear fault, push (`Lch=1`, `Stat=1`), then twist/pull to re-arm (`Stat=0`) | Returns to `State 0` or `State 1` | Premature reset during active fault is discarded; after fault clears, alarm clears only after new push-and-re-arm (`Stat=0`) | Confirms active-fault reset discard and release-confirmed post-fault reset |
| **7. Isolated P2P Test** | Coordinator stopped (`Ctrl+C`), Comm WDT temporarily disabled, `DO 4` confirmed `0`; apply >30.0°C & >60.0% RH | S232 P2P Engine (`DO 5` & `DO 6`) | `DO 4` remains `0`; `DO 5`=`1` energizes IDEC Relay #2 and blower; `DO 6`=`1` on status page; both return to `0` when cleared | Proves P2P path (`DO 5`) alone physically energizes blower with `DO 4` off, and `DO 5`/`DO 6` clear to `0` |
| **8. Isolated WDT / FSV Test** | Restore normal Temp ≤ 30.0°C & RH ≤ 60.0% (`DO 5`=`0`, `DO 6`=`0`), re-enable Comm WDT, stop script for `60s` | S252 Comm WDT Timeout | `DO 1` (Yellow)=`1`, `DO 4` (IDEC Relay #1 Blower)=`1`; `DO 0`, `DO 2`, `DO 3`, `DO 5`, `DO 6`=`0` | Isolates and confirms `60s` communication-loss `FSV` activation; restarting script restores `State 0` |

---

## Troubleshooting Common Hardware and Network Issues

If the system does not respond as expected during bench commissioning or validation, check the following five diagnostic areas:

* **Power Polarity, Common Ground, and LED Diagnostics:** If a module fails to power on, verify with a digital multimeter that the `+Vs` and `-Vs` terminals receive `24VDC` with correct polarity. Ensure the `0V` negative outputs of both the `24VDC` (`IPS-D22A60W24V-A`) and `12VDC` (`Phoenix Contact 2902999`) supplies are tied together at Upper Row Pin 13 (`DGND`) on the `WISE-4250-S252`; without a shared `0V` reference, the `12VDC` Adafruit `2993` tower light channels on `DO 0` through `DO 3` will not illuminate when sunk to `DGND`. If all four green `Signal Strength` LEDs blink simultaneously, the radio-frequency (RF) board has encountered a hardware fault; if three `Signal Strength` LEDs blink simultaneously, the plug-in I/O cartridge is not seated properly on the board-to-board header.
* **AP Mode Versus Infrastructure IP Conflicts:** Remember that toggling the Wireless Mode between `AP Mode` and `Infrastructure Mode` (or moving rear DIP switch `SW1` Pin 1) requires a full power cycle before taking effect. If three consecutive login attempts fail, the web server locks out authentication for five minutes; to reset a lost root password, set `SW1` Pin 1 to `OFF` (`Initial Mode`), power-cycle the unit, connect to `192.168.1.1`, and click **Reset Password** in the WISE Studio utility.
* **Digital Input Contact Mode and NC/NO Polarity:** If toggling a switch on `DI 0` through `DI 4` does not update the status indicator on the **I/O Status > DI** page, verify that internal switches **`SW1-1`, `SW2-1`, and `SW3-1`** inside the `WISE-S252` cartridge are set to **`ON`** and **`SW1-2`, `SW2-2`, and `SW3-2`** are set to **`OFF`** (`Dry Contact` mode)—or at minimum verify the banks containing the channels used by the project (`SW1` and `SW2` covering `DI 0` through `DI 4`)—and confirm that each switch bridges its `DI` pin to the matching bank common (`DCOM0` on Lower Row Pin 5 for `DI 0` through `DI 3`; `DCOM1` on Lower Row Pin 10 for `DI 4`). Remember that the Banner `SSA-EB1P-02` uses Normally Closed (`NC`) contacts (`11-12`) and the Potter `AMS-7-B` closes when the door magnet is aligned; both require **Invert Signal (`Inv = 1`)** enabled in the DI configuration—and the `SSA-EB1P-02` must be pulled or twisted clockwise back to its armed position (`Stat = 0`) *after* the initiating critical fault has cleared and the button has been pushed (`Lch = 1`) for the coordinator to clear a latched alarm.
* **Data Logger Memory Resets:** Changing any channel mode (`DI`, `Counter`, `Latch`, `DO`, or `Pulse Output`) or modifying the `By Channel` / `By Sensor` logging masks automatically clears existing samples in the local circular flash logger to rebuild the internal memory structure. Always export logged `.json` files via **Local Data Query > Save** before modifying channel configurations.
* **Wireless RSSI and Firewall Blocking:** For reliable packet delivery, maintain at least three illuminated `Signal Strength` LEDs (`RSSI` above `-64dBm`) and avoid mounting the whip antenna completely inside an unvented metal box without an external magnetic antenna extension base (`1750008767-01`). When running the **Site Survey** diagnostic tool in WISE Studio, ensure **Advantech Public** is allowed through Windows Defender Firewall (`Control Panel\System and Security\Windows Defender Firewall\Allowed apps`) so UDP test packets are not blocked.

---

## License

Provided for educational and engineering reference by **Mouser Electronics**.
