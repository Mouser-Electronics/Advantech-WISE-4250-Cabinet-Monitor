# Advantech WISE-4250 Wireless Industrial Cabinet Monitoring System

This repository contains the edge coordinator source code, RESTful API provisioning script, hardware pinout documentation, engineering design notes, and troubleshooting guide for the **Mouser Electronics** hardware project: **Industrial Cabinet Monitoring: Build a Wireless IoT System**.

The proof-of-concept system uses the **Advantech WISE-4250** dual-band Wi-Fi 5 (IEEE 802.11a/b/g/n/ac) wireless I/O platform and an **Advantech ICR-2545W** industrial cellular and Wi-Fi router to monitor control cabinet temperature and relative humidity (RH), track discrete enclosure switches, trigger local stack-light and dual interface-relay outputs via AES-128 encrypted Peer-to-Peer (P2P) rules and combinational edge logic, log timestamped data points to nonvolatile circular flash memory, and publish telemetry to an **Ubidots** cloud dashboard.

> **Safety and Scope Notice:** This project is intended as a controlled bench proof of concept for engineers experienced with industrial control wiring and network configuration. Installation in an operating control cabinet must comply with applicable electrical codes, enclosure ratings, conductor separation practices, equipment instructions, cybersecurity policies, and machinery safety procedures. Always de-energize and verify that all AC mains and DC circuits are de-energized before wiring, and use grounded electrostatic-discharge (ESD) handling procedures (such as a grounded wrist strap) when touching exposed electronics.

---

## Repository Contents

* `wise4250_cabinet_coordinator.py` *(Version 7 - Option A Channel Mapping)* — Python 3 edge coordinator script that polls the WISE-4250-S232 and WISE-4250-S252 RESTful JSON endpoints every 2.0s, evaluates the cabinet alarm state machine, drives coordinator-owned sink outputs (`DO 2`–`DO 6`, leaving `DO 0`–`DO 1` to the WISE-4250-S232 P2P engine), immediately discards any reset request initiated while a critical fault remains active, records an append-only periodic bench telemetry CSV log (`wise4250_cabinet_telemetry_log.csv`; implement log rotation before unattended deployment), and publishes live telemetry to Ubidots. Includes a `--provision` CLI flag to automatically configure channel tags, `5.0s` measurement intervals, alarm limits, `20.0ms` digital debounce filters, hardware signal inversion (`Inv=1`) on `DI 0` and `DI 4`, `Low to High Latch` mode on `DI 4`, and Fail-Safe Value (`FSV`) settings over Wi-Fi.
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
| **IDEC** | `199-RV8HLD24` | `RV8H-L-D24` | 6mm Slim Electromechanical Interface Relay & DIN-Mount Screw-Terminal Socket, 24VDC Coil, SPDT 6A (`DO 6` Coordinator Blower Relay) | 1 |
| **Schneider Electric** | `996-RSLZVA1` | `RSLZVA1` (with RSL1AB4BD Relay) | 6.2mm Harmony DIN-Rail Screw-Terminal Socket with LED & Protection Circuit + Compatible 24VDC RSL Relay (`DO 0` P2P Thermal Override Socket) | 1 |
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
* **24VDC Control Rail (`Advantech IPS-D22A60W24V-A`):** Accepts 85VAC to 264VAC input and provides a regulated 24VDC, 2.50A, 60.0W output bus with over-voltage, over-current, short-circuit, and over-temperature protection. The maximum connected 24VDC load is **10.45W (0.435A)**, comprising:
  * `WISE-4250-S232`: `1.60W` at `24VDC`
  * `WISE-4250-S252`: `1.60W` at `24VDC`
  * `ICR-2545W` Router (`9VDC` to `48VDC` input range): `2.90W` idle / `4.50W` average / `6.70W` maximum
  * `IDEC RV8H-L-D24` 24VDC Interface Relay (`DO 6`): `10.6mA` / `0.25W`
  * `Schneider Electric RSLZVA1` Socket + RSL Relay (`DO 5` / `DO 0` P2P Thermal Override): `0.17W` nominal coil power + LED (budgeted at `0.30W`)
  * **Available 24VDC Headroom:** **49.55W (82.6%)** of supply capacity.
* **12VDC Auxiliary Load Rail (`Phoenix Contact 2902999 / UNO-PS/1AC/12DC/55W`):** Accepts 85VAC to 264VAC input and provides a regulated 12VDC, 4.60A, 55.0W output bus. The maximum connected 12VDC load is **13.20W (1.10A)**, comprising:
  * `Same Sky CBM-7525C-145-494` 12VDC Blower: `0.58A` (`6.96W`) typical / `0.70A` (`8.40W`) maximum
  * `Adafruit 2993` 12VDC Alert Tower Light & Buzzer: Bounded by the `100mA` per-channel sink limit of `DO 2` through `DO 5` (`≤0.40A` / `4.80W` combined)
  * **Available 12VDC Headroom:** **41.80W (76.0%)** of supply capacity.

### 2. Supporting Field Component Specifications
* **Potter / Amseco `AMS-7-B` Magnetic Door Contact (`507-AMS-7B`):** Miniature surface- or press-fit Alnico 5 magnetic reed switch with 304mm (12in), 22AWG leads and a 19mm (0.75in) operating gap. Uses a Form A (Normally Open) contact rated at 10VA (1.0A carry, 0.5A switching, 200VDC breakdown) that is held closed when the cabinet door magnet is aligned and opens when the door opens.
* **Banner Engineering `SSA-EB1P-02` Latching Pushbutton (`778-SSA-EB1P-02`):** 30mm panel-mount, 40mm mushroom-style mechanical pushbutton (push-to-latch, pull- or twist-clockwise-to-release) equipped with two Normally Closed (NC) gold-plated silver contacts (`11-12` and `21-22`, rated 5A thermal current, 1mA at 5VAC/DC minimum load, with a specified `20ms` contact bounce time). When armed, contact `11-12` is closed; when pushed, contact `11-12` opens until manually rearmed. In this bench proof of concept, the `SSA-EB1P-02` serves strictly as a manual alarm-reset input rather than a machine-safeguarding emergency stop device.
* **Dual Blower Control Relays (`DO 0` P2P & `DO 6` Coordinator) & Hardwired Leak-Inhibit Interlock:** Using two separate 6mm-class DIN-rail electromechanical SPDT (`1C`) interface relays (`IDEC RV8H-L-D24` on `DO 6` and `Schneider Electric RSLZVA1` socket with an installed 24VDC RSL relay on `DO 0`) allows the Python coordinator and the decentralized `WISE-4250-S232` P2P engine to command the 12VDC cooling blower independently without software write collisions. Routing the `+12VDC` feed to terminal `11` (`COM`) of both relays through the isolated Normally Closed (`NC`) leak-inhibit pole of the double-pole leak switch guarantees that an active leak physically opens the blower power path upstream of both `DO 0` and `DO 6`.
* **Adafruit `2993` 12VDC Alert Tower Light (`485-2993`) & Same Sky `CBM-7525C-145-494` 12VDC Blower (`179-CBM7525C145494`):** The tower light integrates red, yellow, and green LED segments plus a continuous piezo buzzer fed by a common `+12VDC` **brown wire** and switched to ground via individual color-coded control leads (**green wire** = green LED on `DO 2`, **yellow wire** = yellow LED on `DO 3`, **red wire** = red LED on `DO 4`, **orange wire** = continuous buzzer on `DO 5`). The Same Sky brushless DC blower operates from 10.8VDC to 13.2VDC (12VDC nominal, **red wire** `+Vin`, **black wire** `-Vin`) to deliver 13.35CFM airflow at 4,500RPM with auto-restart, reverse-polarity protection, and an integrated soft-start function.

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

### 3. Complete Node Terminal Pinout & Logic Mapping (Option A)
| Module | Terminal Row & Pin | Reference Pin | Channel Tag (`Max 21 chars`) | Connected Field Device / Part Number | Electrical & Logic State Mapping / FSV |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WISE-4250-S232** | Power `+Vs` / `-Vs` | `+24VDC` / `0V` | `Cabinet_Env_S232` | 24VDC Power Input & Built-In SHT41-AD1F Sensor | `Ch 0`: Temp (`>30.0°C` High Alarm); `Ch 1`: RH (`>60.0%` RH High Alarm) |
| **WISE-4250-S252** | Upper Row Pin 14 (`+Vs`), Pin 15 (`-Vs`) | `+24VDC` / `0V` | `Cabinet_DIO_S252` | 24VDC Module Power Input (`IPS-D22A60W24V-A`) | 10VDC to 50VDC range (`1.60W` at `24VDC`) |
| **WISE-4250-S252** | Lower Row Pin 1 (`DI 0`) | Lower Pin 5 (`DCOM0`) | `Cabinet_Door_Sw` | Potter `AMS-7-B` Form A (N.O.) Magnetic Door Switch | Closed door holds reed closed; `Inv=1` maps Door Closed=`0`, Door Open=`1` |
| **WISE-4250-S252** | Lower Row Pin 2 (`DI 1`) | Lower Pin 5 (`DCOM0`) | `Cooling_Fan_Stat` | Primary Fan Running Status Toggle Switch (SPST) | `0` = Primary Fan Off (`Open`) / `1` = Primary Fan Running (`Closed to DCOM0`) |
| **WISE-4250-S252** | Lower Row Pin 3 (`DI 2`) | Lower Pin 5 (`DCOM0`) | `Filter_Dirty_Warn` | Intake Filter Differential Toggle Switch (SPST) | `0` = Filter Clean (`Open`) / `1` = Filter Clogged Warning (`Closed to DCOM0`) |
| **WISE-4250-S252** | Lower Row Pin 4 (`DI 3`) | Lower Pin 5 (`DCOM0`) | `Leak_Fault_Sensor` | Bottom-Pan Leak Switch (DPST/DPDT Pole 1 `NO`) | `0` = Dry (`Open`) / `1` = Leak Detected (`Closed to DCOM0`); Pole 2 `NC` inhibits `+12VDC` blower feed |
| **WISE-4250-S252** | Lower Row Pin 6 (`DI 4`) | Lower Pin 10 (`DCOM1`) | `Manual_Alarm_Rst` | Banner `SSA-EB1P-02` Pushbutton (`NC` Contact `11-12`) | Armed=Closed, Pushed=Open; `Inv=1` + `Low to High Latch` records push (`Lch=1`) & re-arm (`Stat=0`) |
| **WISE-4250-S252** | Upper Row Pin 1 (`DO 0`) | Upper Pin 13 (`DGND`) | `P2P_Temp_Fan_Cmd` | Schneider `RSLZVA1` Socket + RSL Relay Coil (`A2`) | P2P Rule `0` owned (`>30.0°C`); Contacts `11-14` in parallel with `DO 6` behind Leak-Inhibit `NC`; `FSV = 0` |
| **WISE-4250-S252** | Upper Row Pin 2 (`DO 1`) | Upper Pin 13 (`DGND`) | `P2P_RH_Warn_Cmd` | Dedicated S232 P2P High-RH (`>60.0%`) Status Output | P2P Rule `1` owned (logical status demonstration on S252 DO page); `FSV = 0` |
| **WISE-4250-S252** | Upper Row Pin 3 (`DO 2`) | Upper Pin 13 (`DGND`) | `LED_Green_Normal` | Adafruit `2993` Tower Light — **Green Wire** (`12VDC`) | Coordinator owned; Brown wire to `+12VDC`; Sink `1` = Green On; `FSV = 0` (Comm-loss Off) |
| **WISE-4250-S252** | Upper Row Pin 4 (`DO 3`) | Upper Pin 13 (`DGND`) | `LED_Amber_Warn` | Adafruit `2993` Tower Light — **Yellow Wire** (`12VDC`) | Coordinator owned; Brown wire to `+12VDC`; Sink `1` = Yellow On; `FSV = 1` (Comm-loss On) |
| **WISE-4250-S252** | Upper Row Pin 5 (`DO 4`) | Upper Pin 13 (`DGND`) | `LED_Red_Alarm` | Adafruit `2993` Tower Light — **Red Wire** (`12VDC`) | Coordinator owned; Brown wire to `+12VDC`; Sink `1` = Red On; `FSV = 0` (Comm-loss Off) |
| **WISE-4250-S252** | Upper Row Pin 6 (`DO 5`) | Upper Pin 13 (`DGND`) | `Alarm_Buzzer` | Adafruit `2993` Tower Light — **Orange Wire** (`12VDC`) | Coordinator owned; Brown wire to `+12VDC`; Sink `1` = Buzzer On; `FSV = 0` (Comm-loss Off) |
| **WISE-4250-S252** | Upper Row Pin 7 (`DO 6`) | Upper Pin 13 (`DGND`) | `Aux_Fan_Relay` | IDEC `RV8H-L-D24` Coil (`A2-`) Switching Blower | Coordinator owned; Coil `A1+` to `+24VDC`; Contacts `11-14` fed via Leak-Inhibit `NC` contact; `FSV = 1` |

---

## Engineering Notes & Design Considerations

1. **Dual Blower Relays (`DO 0` and `DO 6`), Hardwired Leak Inhibit, and Communication-Loss (`FSV`) Behavior:**
   * `DO 0` energizes the Schneider Electric `RSLZVA1` socket and its installed 24VDC RSL relay, while `DO 6` energizes the 24VDC coil (`A2-`) of the **IDEC `RV8H-L-D24`** interface relay. Their isolated SPDT contacts (terminals `11` COM and `14` NO on both relays) are wired in parallel to switch `+12VDC` power from the Phoenix Contact `2902999` supply to the Same Sky `CBM-7525C-145-494` auxiliary cabinet cooling blower (`0.58A` typical, `0.70A` max).
   * During a `State 4` liquid-leak alarm, the coordinator intentionally de-energizes `DO 6` so the blower does not circulate moisture across cabinet electronics. Because the `WISE-4250-S232` P2P engine evaluates temperature independently of the `WISE-4250-S252` leak input, routing the `+12VDC` feed to terminal `11` (`COM`) of both relays through the isolated Normally Closed (`NC`) leak-inhibit pole of the double-pole leak switch ensures that an active leak physically opens the blower supply path upstream of both `DO 0` and `DO 6`—preventing blower operation even if temperature simultaneously exceeds `30.0°C`. If a different device (such as a drain pump or dehumidifier) is connected, its normal, alarm, and FSV states must be reassessed.
   * Setting `FSV = 1` on `DO 6` commands the relay output on after a `60s` communication-watchdog timeout to request auxiliary cooling, which represents a communication-loss response rather than a complete fail-safe cooling architecture. Applications requiring verified cooling must monitor fan tachometer feedback and evaluate power, relay, and airflow failure modes.
2. **Relative Humidity Measurement vs. Dew-Point Condensation:**
   * The `WISE-4250-S232` relative humidity measurement indicates environmental conditions associated with condensation risk; determining whether liquid condensation will form on a specific surface requires comparing the calculated dew point against the temperature of vulnerable enclosure surfaces, whereas the system's bottom-pan leak input (`DI 3`) detects accumulated moisture directly.
3. **Single-Owner Output Arbitration, Polling Cadence & Telemetry Semantics:**
   * Do not configure the Python coordinator, P2P rules, and watchdog logic as independent writers to the same digital output channel. In this Option A architecture, the WISE-4250-S232 P2P engine exclusively owns `DO 0` and `DO 1` (`P2P_Temp_Fan_Cmd` and `P2P_RH_Warn_Cmd`), while the Python coordinator exclusively writes `DO 2` through `DO 6` during normal operation (with Communication WDT `FSV` providing loss-of-coordinator fallback on `DO 3` and `DO 6`). In this bench build, `DO 1` demonstrates P2P high-humidity command transfer through the `WISE-4250-S252` output-status page; connect a properly rated indicator or interface relay if a physical high-humidity response is required.
   * The Python coordinator polls every `2.0s` to minimize latency for discrete input and output processing, while the `WISE-4250-S232` environmental channels update every `5.0s` (`PItv = 500`, with the hardware applying the smaller interval configured between `Channel 0` and `Channel 1`). Consequently, consecutive `2.0s` polls can return the same temperature and RH sample between sensor conversions.
   * The Ubidots variable `coordinator_fan_request` reports the coordinator's `DO 6` command only—not verified blower rotation, airflow, the upstream leak-inhibit contact state, or the `DO 0` P2P relay state.
4. **Nonvolatile Circular Flash Logging:**
   * Each WISE-4250 module includes nonvolatile flash memory storing more than 10,000 timestamped data points (samples) in a circular ring buffer. Leaving `Clear Log when Power Up` unchecked preserves previously committed log samples across power cycles, while changing any channel mode (`DI`, `Counter`, `Latch`, `DO`, `Pulse Output`) or modifying the `By Channel` / `By Sensor` logging masks automatically clears existing buffer memory to rebuild the internal log structure.

---

## Software Setup & Quick Start

### 1. Install Dependencies
Ensure Python 3.10 or newer is installed on your host computer, then install the `requests` library:
```bash
pip install requests
