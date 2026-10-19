# Advantech WISE-4250 Wireless Industrial Cabinet Monitoring System

This repository contains the edge coordinator source code, RESTful API provisioning script, hardware pinout documentation, and dashboard configuration guide for the **Mouser Electronics** hardware project: **Industrial Cabinet Monitoring: Build a Wireless IoT System**.

The proof-of-concept system uses the **Advantech WISE-4250** dual-band Wi-Fi 5 (IEEE 802.11a/b/g/n/ac) wireless I/O platform to monitor control cabinet temperature and relative humidity (RH), track discrete enclosure switches, trigger local stack-light and relay outputs via AES-128 encrypted Peer-to-Peer (P2P) rules and combinational edge logic, log timestamped records to non-volatile flash memory, and publish telemetry to an **Ubidots** cloud dashboard.

---

## Repository Contents

* `wise4250_cabinet_coordinator.py` — Python 3 edge coordinator script that polls the WISE-4250-S232 and WISE-4250-S252 RESTful JSON endpoints, evaluates the five-state cabinet alarm machine, drives sink outputs, records a local timestamped CSV log (`wise4250_cabinet_event_log.csv`), and publishes live telemetry to Ubidots. Includes a `--provision` CLI flag to automatically configure channel tags, alarm limits, 10ms digital debounce filters, and Fail Safe Value (FSV) settings over Wi-Fi.
* `configs/` *(optional backup directory)* — Sanitized `.cfg` and `.p2p` configuration backup files exported from the WISE-4250-S232 and WISE-4250-S252 HTML5 web interfaces.

---

## Hardware Bill of Materials (BOM)

| Manufacturer | Mouser Part Number | Manufacturer Part Number | Project Function | Qty |
| :--- | :--- | :--- | :--- | :---: |
| **Advantech** | `923-WISE-4250-S232` | `WISE-4250-S232` | Dual-Band Wi-Fi 5 Wireless Temperature & RH Sensor Node (-25°C to 70°C, 0% to 100% RH) | 1 |
| **Advantech** | `923-WISE-4250-S252` | `WISE-4250-S252` | Dual-Band Wi-Fi 5 Wireless 12-Channel DI / 12-Channel DO Node | 1 |
| **Advantech** | `923-ICR-2545W` | `ICR-2545W` | Industrial Wireless Router & Local Project Network Gateway | 1 |
| **Advantech** | `923-IPS-D22A60W24V-A` | `IPS-D22A60W24V-A` | 60W, 24V DC DIN-Rail Power Supply | 1 |

**Supporting Bench & Enclosure Components:**
* 4× SPST dry-contact toggle switches (simulating cabinet door, cooling fan status, filter warning, and leak float switches)
* 1× Momentary normally open (NO) pushbutton switch (manual alarm reset)
* 3× 24V DC LED indicators or 3-tier stack light (Green, Amber, Red; rated <100mA per channel)
* 1× 24V DC piezo buzzer (rated <100mA)
* 1× 24V DC DIN-rail interface relay with integrated flyback diode (auxiliary cooling fan / dehumidifier load)
* 35mm DIN rail, end brackets, 0.5mm² to 2.5mm² hookup wire, Category 6 Ethernet patch cable, Torx T8 screwdriver, and flathead terminal screwdriver

---

## Network Architecture & IP Addressing

In factory-default `AP Mode` (or `Initial Mode`), WISE-4250 modules use the static IP address `192.168.1.1`. Configure the **Advantech ICR-2545W** router LAN on the `192.168.10.0/24` subnet to prevent IP conflicts during initial setup:

| Device | Hostname / Customized Name | IP Address | Role & Protocols |
| :--- | :--- | :--- | :--- |
| **Advantech ICR-2545W** | `ICR-2545W_GW` | `192.168.10.1` | Wi-Fi AP (`SSID: WISE_Cabinet_Net`, WPA3), DHCP & SNTP Server |
| **Engineering Host PC** | `Engineering_Host` | `192.168.10.50` | Runs `wise4250_cabinet_coordinator.py` & browser configuration |
| **Advantech WISE-4250-S232** | `Cabinet_Env_S232` | `192.168.10.101` | Temperature (`Ch 0`) & RH (`Ch 1`) node, Local Logger, P2P Sender |
| **Advantech WISE-4250-S252** | `Cabinet_DIO_S252` | `192.168.10.102` | 12DI / 12DO node, Local Logger, P2P Receiver (UDP Port `5048`) |

---

## Terminal Pinout & I/O Mapping (`WISE-4250-S252`)

Before mounting the `WISE-4250-S252`, verify that the rear operation-mode switch `SW1` Position 1 (`P1`) is set to `ON` (`Normal Mode`) and that the three internal cartridge DIP switches (`SW1`, `SW2`, and `SW3`) are set to `ON` (**Dry Contact Mode**).

### Digital Inputs (Lower Terminal Row — Dry Contact)
Wire each switch between its designated `DI` pin and bank common (`DCOM0` for `DI 0`–`DI 3`; `DCOM1` for `DI 4`):

| Terminal Pin | Common Reference | Channel Tag | Simulated Cabinet Signal | Logic State Mapping |
| :--- | :--- | :--- | :--- | :--- |
| `DI 0` (Pin 1) | `DCOM0` (Pin 5) | `Cabinet_Door_Sw` | Enclosure Door Interlock Switch | `0` = Closed (Open contact) / `1` = Open (Closed to `DCOM0`) |
| `DI 1` (Pin 2) | `DCOM0` (Pin 5) | `Cooling_Fan_Stat` | Circulation Fan Status Contact | `0` = Fan Off / `1` = Fan Running |
| `DI 2` (Pin 3) | `DCOM0` (Pin 5) | `Filter_Dirty_Warn` | Intake Filter Differential Switch | `0` = Filter Clean / `1` = Filter Clogged Warning |
| `DI 3` (Pin 4) | `DCOM0` (Pin 5) | `Leak_Fault_Sensor` | Bottom-Pan Condensation/Leak Float | `0` = Dry (Normal) / `1` = Leak Fault Detected |
| `DI 4` (Pin 6) | `DCOM1` (Pin 10) | `Manual_Alarm_Rst` | Momentary Manual Reset Button | `0` = Idle / `1` = Reset Pressed (`Low to High Latch`) |

### Digital Outputs (Upper Terminal Row — Open-Collector Sink Type)
Connect the positive (`+`) lead of each 24V DC load to the `+24V` supply rail, connect the negative (`-`) lead to the designated `DO` terminal, and tie terminal `DGND` (Pin 13) to the power supply `0V` return:

| Terminal Pin | Return Reference | Channel Tag | Connected Load | Fail Safe Value (`FSV`) |
| :--- | :--- | :--- | :--- | :--- |
| `DO 0` (Pin 1) | `DGND` (Pin 13) | `LED_Green_Normal` | 24V DC Green Normal Indicator | `0` (`OFF` on comm timeout) |
| `DO 1` (Pin 2) | `DGND` (Pin 13) | `LED_Amber_Warn` | 24V DC Amber Warning Indicator | `1` (`ON` on comm timeout) |
| `DO 2` (Pin 3) | `DGND` (Pin 13) | `LED_Red_Alarm` | 24V DC Red Critical Alarm LED | `0` (`OFF` on comm timeout) |
| `DO 3` (Pin 4) | `DGND` (Pin 13) | `Alarm_Buzzer` | 24V DC Piezo Audible Buzzer | `0` (`OFF` on comm timeout) |
| `DO 4` (Pin 5) | `DGND` (Pin 13) | `Aux_Fan_Relay` | 24V DC Auxiliary Cooling Relay | `1` (`ON` — Fail-safe cooling active) |

---

## Software Setup & Quick Start

### 1. Install Dependencies
Ensure Python 3.10 or newer is installed on your host computer, then install the `requests` library:
```bash
pip install requests
```

### 2. Configure Credentials
Open `wise4250_cabinet_coordinator.py` in a text editor and update the authentication and Ubidots variables at the top of the file:
```python
S232_IP = "192.168.10.101"
S252_IP = "192.168.10.102"
WISE_USER = "root"
WISE_PASS = "Wise2026"  # Replace with your 8-character WISE-4250 root password

UBIDOTS_TOKEN = "BBUS-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Replace with your Ubidots API Token
UBIDOTS_DEVICE_LABEL = "wise-4250-cabinet-monitor"
```

### 3. Auto-Provision Module Channels via REST API (Optional)
Once both modules have joined the `192.168.10.0/24` Wi-Fi network, you can automatically push all channel tags, 30.0°C / 60.0% RH high-alarm thresholds, 10ms (`100`) digital debounce filters, `Low to High Latch` mode on `DI 4`, and `FSV` output states using the `--provision` flag:
```bash
python wise4250_cabinet_coordinator.py --provision
```

### 4. Run the Edge Coordinator & Ubidots Publisher
Start the continuous polling, state-machine evaluation, local CSV logging, and Ubidots publishing loop:
```bash
python wise4250_cabinet_coordinator.py
```

---

## Cabinet Alarm State Machine Summary

| State Code | Operating Condition | Trigger Logic (`WISE-4250-S232` & `WISE-4250-S252`) | Active Outputs (`DO 0`–`DO 4`) | Latch Behavior |
| :---: | :--- | :--- | :--- | :--- |
| **`0`** | **Normal** | Temp ≤ 30.0°C, RH ≤ 60.0%, `DI 0`=`0`, `DI 2`=`0`, `DI 3`=`0` | `DO 0` (Green LED) | Non-latched |
| **`1`** | **Warning** | (RH > 60.0% with Door Closed) OR Temp > 30.0°C (Fan On) OR `DI 2`=`1` (Filter Warn) | `DO 1` (Amber LED) + `DO 4` (Aux Fan Relay if Temp/RH high) | Momentary (auto-clears) |
| **`2`** | **Environmental Intrusion Alarm** | RH > 60.0% **AND** `DI 0`=`1` (Cabinet Door Open) | `DO 2` (Red LED) + `DO 4` (Aux Fan Relay) | Latched until fault clears + `DI 4` Reset pressed |
| **`3`** | **Thermal Fan Fault Alarm** | Temp > 30.0°C **AND** `DI 1`=`0` (Primary Cooling Fan Off) | `DO 2` (Red LED) + `DO 3` (Buzzer) + `DO 4` (Aux Fan Relay) | Latched until fault clears + `DI 4` Reset pressed |
| **`4`** | **Critical Leak Alarm** | `DI 3`=`1` (Bottom-Pan Moisture / Leak Detected) | `DO 2` (Red LED) + `DO 3` (Buzzer) | Latched until fault clears + `DI 4` Reset pressed |

---

## License

Provided for educational and engineering reference by **Mouser Electronics**.
