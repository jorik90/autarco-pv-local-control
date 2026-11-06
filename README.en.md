# Read Autarco Solar Inverters Locally (No Invrida Subscription Needed)

> 🇳🇱 **Nederlandse versie (standaard):** [Lees deze documentatie in het Nederlands (`README.md`)](README.md)

After solar and inverter company **Autarco** went bankrupt, its software and monitoring platform (`my.autarco.com`) were taken over by **Invrida** (`my.invrida.com`). While monitoring your own solar panels was previously included with the purchase of the hardware, Invrida now charges **€30 per year (€2.50/month)** to keep access to the app and your yield history. Without a paid subscription, access to the app and `my.invrida.com` is cut off.

Fortunately, you **do not need the Autarco or Invrida cloud at all** to read, monitor, and control your Autarco inverter. Under the hood, Autarco inverters are manufactured by **Solis (Ginlong)** and use a network stick that speaks standard **Modbus TCP (port 502)** directly on your local network.

This repository provides:
1. A zero-dependency **Python CLI script** ([`autarco_reader.py`](autarco_reader.py)) to read your inverter locally into a formatted terminal table, JSON, or CSV.
2. Complete **Home Assistant setup instructions** (both via the HACS *Solis Modbus* integration and via Home Assistant's built-in Modbus YAML in [`homeassistant_modbus.yaml`](homeassistant_modbus.yaml)).
3. The complete **Modbus register map** (both for reading metrics and for active power curtailment / remote on-off control during negative electricity prices).
4. Instructions on how to **block data uploads to the Invrida cloud** while keeping local access intact.

---

## Background: From Autarco to a Paid Invrida Subscription

Owners of Autarco systems received an email notice from Invrida stating (translated from Dutch):

> **What is changing**  
> Your system currently does not have an active monitoring subscription. If you want to keep your app, your overview, and your yield history, you must take out a subscription yourself. If you do not, your access to the app and to `my.invrida.com` will be closed afterward.
>
> **€30 per year**  
> That is €2.50 per month to continue monitoring your system completely. [...]  
> *Why there is a fee: until now, the software, servers, and storage of your data were paid for through the sale of solar panels and inverters. You were always paying for it — just not visibly, because it was included in the price of your installation. Invrida does not sell panels; we only make the software. Therefore, monitoring is now a standalone service with its own price.*

With the tools and configurations in this repository, you retain 100% free, local, real-time access to all your solar data (with far more technical detail than the cloud app ever provided).

---

## Tested Hardware

* **Autarco Inverter:** `Autarco S2.LD6000-MIII` (3-phase string inverter, 6 kW, 2 MPPTs)
  * Underlying OEM platform: **Solis / Ginlong 3P(3-20)K-4G** (`Product Model 0x0503`, DSP `0x003B`, LCD `0x0084`)
* **Datalogger (LAN/WiFi stick):** Solis/Ginlong embedded lwIP `1.3.1` module (`Web Ver: 2.4.0`, firmware `10010119`)
* **Protocol:** Standard **Modbus TCP** on port **`502`**, Slave/Unit ID **`1`**

*(If you have another Autarco string inverter from the S1 or S2 series with a LAN or Wi-Fi stick that has port 502 open, this setup works almost identically).*

---

## 1. Local Reading via the Python Script (`autarco_reader.py`)

The script [`autarco_reader.py`](autarco_reader.py) uses only the Python 3 standard library (no `pip install` required).

### Usage

```bash
# 1. Print a formatted summary table in the terminal (replace 192.168.1.100 with your inverter's IP)
./autarco_reader.py --host 192.168.1.100

# You can also set the IP address via an environment variable:
export AUTARCO_HOST=192.168.1.100
./autarco_reader.py

# 2. Output as JSON (useful for custom scripts, MQTT, Telegraf, or Node-RED)
./autarco_reader.py --host 192.168.1.100 --format json

# 3. Append reading to a CSV log file
./autarco_reader.py --host 192.168.1.100 --csv-file measurements.csv

# 4. Continuous monitoring (e.g., poll every 15 seconds)
./autarco_reader.py --host 192.168.1.100 --watch 15
```

### Example Output

```text
============================================================
 Autarco / Solis Omvormer (192.168.1.100) - 2026-06-15T13:30:00
============================================================
 Serienummer       : 1805XXXXXXXXXXXX
 Status            : Normaal in bedrijf (Generating) (code 3)
 Tijd op omvormer  : 2026-06-15 13:30:00
------------------------------------------------------------
 ACTUEEL VERMOGEN & TEMPERATUUR
   AC Vermogen     : 2500 W
   DC Vermogen     : 2600 W
   Temperatuur     : 32.5 °C
   Netfrequentie   : 50.00 Hz
------------------------------------------------------------
 ENERGIE OPBRENGST
   Vandaag         : 12.5 kWh
   Gisteren        : 18.0 kWh
   Deze maand      : 210 kWh
   Vorige maand    : 450 kWh
   Dit jaar        : 3200 kWh
   Vorig jaar      : 5100 kWh
   Totaal (Leven)  : 10500 kWh
------------------------------------------------------------
 ZONNEPANELEN (DC STRINGS)
   String 1 (PV1)  : 380.0 V  |  3.4 A  | 1292.0 W
   String 2 (PV2)  : 385.0 V  |  3.4 A  | 1309.0 W
   DC Busspanning  : 610.0 V
------------------------------------------------------------
 NETZIJDE (AC 3-FASE)
   Fase L1         : 230.1 V  |  3.6 A
   Fase L2         : 230.5 V  |  3.6 A
   Fase L3         : 231.0 V  |  3.6 A
============================================================
```

---

## 2. Home Assistant Integration

You can integrate the inverter into Home Assistant in two ways:
* **Option A (via UI / HACS):** Using the community `Solis Modbus` integration (includes inverter control & automatic clock synchronization).
* **Option B (no HACS, native Home Assistant):** Using the built-in `modbus:` integration in `configuration.yaml`.

> **Important:** The inverter's network stick only accepts **one simultaneous TCP connection on port 502**. Do not run Option A and Option B (or a continuous Python polling script) at the same time.

### Option A: Via HACS (`Pho3niX90/solis_modbus`)

1. In **HACS**, install the **Solis Modbus** integration (`https://github.com/Pho3niX90/solis_modbus`) and restart Home Assistant.
2. Go to **Settings** → **Devices & Services** → **Add Integration** → search for **Solis Modbus**.
3. **Screen 1 (Connection Method):** Select **`S2_WL_ST`**.
4. **Screen 2 (Inverter Configuration):** Enter the following settings for the **Autarco S2.LD6000-MIII**:
   * **IP Address:** Your inverter's local IP address (e.g., `192.168.1.100`)
   * **Port:** `502`
   * **Modbus Slave ID:** `1`
   * **Inverter Model:** **`3P(3-20)K-4G`** *(or `S5-GR3P`)*
   * **Inverter Serial:** Your 16-character inverter serial number *(can be read via `./autarco_reader.py` or found on the inverter label)*
   * **Poll profile:** `Normal` *(do **not** use `Extreme`)*
   * **Fast / Normal / Slow Poll Interval:** `15` / `30` / `60` seconds
5. **Checkboxes on Screen 2:**
   * ✅ **Has PV (Solar Panels):** **ON**
   * ✅ **Suppress 'datalogger unreachable' repair issue while the sun is below the horizon:** **ON** *(prevents repair warnings at night when the inverter powers down)*
   * ✅ **Automatically correct inverter clock drift (`clock_sync`):** **ON** *(automatically keeps the inverter's internal clock accurate without cloud sync)*
   * ❌ **Turn OFF all other checkboxes** (`Updated to V2 Firmware`, `Has Battery Storage`, `Has HV Battery`, `Has Generator`, `Has AC Coupling`, `Parallel inverter`, `Second smart meter`, `EPM / export power manager`, `Extreme` options).

### Option B: Via Built-in Home Assistant Modbus (`configuration.yaml`)

Prefer not to use HACS? Copy the contents of [`homeassistant_modbus.yaml`](homeassistant_modbus.yaml) into your `configuration.yaml` (update `host:` to your inverter's IP address) and restart Home Assistant. Afterwards, add `sensor.autarco_opbrengst_totaal` to your **Home Assistant Energy Dashboard**.

---

## 3. Built-in Datalogger Web Interface (`http://<IP>/`)

The LAN stick inside the inverter also hosts a built-in web interface on port 80:
* **URL:** `http://<IP-ADDRESS>/` (e.g., `http://192.168.1.100/`)
* **Default Username:** `admin`
* **Default Password:** `123456789`

**Note:** Due to a bug in the Solis/Autarco stick firmware (`Web Ver 2.4.0` / `10010119`), `status.html` (`inverter.cgi`) on this built-in webpage only populates the serial number while showing `0 W` and `0 kWh` for power and energy. **Do not flash or modify the stick's firmware** to fix this webpage: newer Solis/Solarman firmwares frequently disable local Modbus TCP on port `502`, which would lock you out of local monitoring completely.

---

## 4. Blocking Uploads to the Invrida / Autarco Cloud

Even without a paid subscription, the datalogger stick continues to upload your solar production data to the external cloud server (`Remote server A: Connected`). You can easily block this outbound traffic while keeping local Modbus TCP access working.

### Method 1: In Your Router (e.g., Ubiquiti EdgeRouter X)
1. **Assign a Static DHCP Lease:**
   * In EdgeOS, go to **Services** → **DHCP Server** → **View Leases** and create a *Static MAC/IP Mapping* for the stick's MAC address.
2. **Block Outbound Internet Traffic in the Firewall:**
   * Go to **Firewall/NAT** → **Firewall Policies** → edit your `WAN_OUT` (or `LAN_IN`) ruleset.
   * Add a rule with **Action: Drop**, **Protocol: All protocols**, and set **Source** to the IP address (or MAC address) of the inverter.

### Method 2: On a Fritz!Box
1. Go to **Internet** → **Filters** → **Parental Controls (Kinderslot)**.
2. Select the inverter's device entry and choose **Block internet use**.

### Method 3: Directly on the Stick (Static IP Without Gateway)
1. Log in to `http://<IP-ADDRESS>/` (`admin` / `123456789`) → **Advanced** → **LAN settings**.
2. Switch to **Static IP**:
   * **IP Address:** Your current local IP address (e.g., `192.168.1.100`)
   * **Subnet Mask:** `255.255.255.0`
   * **Default Gateway:** `192.168.1.254` *(an unused IP address on your subnet that is not a router)*
   * **Preferred DNS:** `127.0.0.1`
3. Click **Save** and reboot the stick via **Restart**. The stick can now only communicate inside your local LAN and cannot reach the internet.

---

## 5. Complete Modbus Register Map (`S2.LD6000-MIII`)

### A. Read-Only — Input Registers (Function Code `0x04`)
*(All addresses listed below are 0-based wire protocol addresses as used directly in Python and Home Assistant).*

| Address (0-based) | Parameter | Type | Scale / Unit | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `2999` | Product Model | `U16` | Hex | `0x0503` on S2.LD6000-MIII |
| `3000` | DSP Software Version | `U16` | Hex | `0x003B` |
| `3001` | LCD Software Version | `U16` | Hex | `0x0084` |
| `3002` | AC Output Type | `U16` | Enum | `1` = 3-phase 4-wire |
| `3003` | DC Input Type | `U16` | Enum | `1` = 2 MPPT / DC inputs |
| `3004–3005` | **AC Active Power** | `U32` | `1 W` | Real-time AC power exported |
| `3006–3007` | **DC Total Power** | `U32` | `1 W` | Real-time DC power from panels |
| `3008–3009` | **Total Energy (Lifetime)** | `U32` | `1 kWh` | Cumulative lifetime yield |
| `3010–3011` | **Energy This Month** | `U32` | `1 kWh` | Current calendar month |
| `3012–3013` | **Energy Last Month** | `U32` | `1 kWh` | Previous calendar month |
| `3014` | **Energy Today** | `U16` | `0.1 kWh` | Daily yield today |
| `3015` | **Energy Yesterday** | `U16` | `0.1 kWh` | Daily yield yesterday |
| `3016–3017` | **Energy This Year** | `U32` | `1 kWh` | Current calendar year |
| `3018–3019` | **Energy Last Year** | `U32` | `1 kWh` | Previous calendar year |
| `3021` | **DC Voltage String 1 (PV1)** | `U16` | `0.1 V` | MPPT 1 voltage |
| `3022` | **DC Current String 1 (PV1)** | `U16` | `0.1 A` | MPPT 1 current |
| `3023` | **DC Voltage String 2 (PV2)** | `U16` | `0.1 V` | MPPT 2 voltage |
| `3024` | **DC Current String 2 (PV2)** | `U16` | `0.1 A` | MPPT 2 current |
| `3029` | Fault / Alarm Code | `U16` | Bitmask | `0` = No fault |
| `3030` | DC Busbar Half Voltage (+) | `U16` | `0.1 V` | Positive DC bus half |
| `3031` | **DC Busbar Voltage (Total)** | `U16` | `0.1 V` | Total internal DC bus voltage |
| `3032` | DC Busbar Half Voltage (-) | `U16` | `0.1 V` | Negative DC bus half |
| `3033` | **AC Voltage Phase L1** | `U16` | `0.1 V` | Grid voltage phase 1 |
| `3034` | **AC Voltage Phase L2** | `U16` | `0.1 V` | Grid voltage phase 2 |
| `3035` | **AC Voltage Phase L3** | `U16` | `0.1 V` | Grid voltage phase 3 |
| `3036` | **AC Current Phase L1** | `U16` | `0.1 A` | Grid current phase 1 |
| `3037` | **AC Current Phase L2** | `U16` | `0.1 A` | Grid current phase 2 |
| `3038` | **AC Current Phase L3** | `U16` | `0.1 A` | Grid current phase 3 |
| `3040` | Working Mode | `U16` | Code | `0`=None, `1`=Volt-Watt, `2`=Volt-VAr, `3`=Fixed PF |
| `3041` | **Inverter Temperature** | `S16` | `0.1 °C` | Internal IGBT temperature |
| `3042` | **Grid Frequency** | `U16` | `0.01 Hz` | e.g., `5000` = `50.00 Hz` |
| `3043` | **Operating Status** | `U16` | Code | `0`=Waiting, `1`=Open Run, `2`=Soft Run, `3`=Generating |
| `3049` | Actual Power Limit | `U16` | `0.01 %` | `11000` = `110.00%` |
| `3053` | Grid Standard Profile Code | `U16` | Code | `14` = EN50549 (NL) |
| `3055–3056` | Reactive Power | `S32` | `1 VAr` | Instantaneous reactive power |
| `3057–3058` | Apparent Power | `S32` | `1 VA` | Instantaneous apparent power |
| `3059` | Power Factor (`cos φ`) | `S16` | `0.001` | `1000` = `1.000` |
| `3060–3063` | Serial Number (4 words) | `U16[4]` | Hex (reversed per word) | Reverse hex characters of each 16-bit word |
| `3072–3077` | Internal Clock (Y, M, D, H, M, S) | `U16[6]` | Year + 2000 | Current inverter timestamp |

### B. Configuration / Control — Holding Registers (Function Code `0x06` / `0x10`)

Useful for dynamic energy tariffs (curtailing or shutting down the inverter during negative electricity prices):

* **Remote Inverter ON / OFF:**
  * Register `3007` (or `3006` 0-based):
    * Write `0xBE` (`190`) = **Turn Inverter ON (Start)**
    * Write `0xDE` (`222`) = **Turn Inverter OFF (Standby / Stop)**
* **Active Power Limitation / Curtailment (0% – 110%):**
  1. Enable the *Power Limitation Switch* on register `3070` (or `3069` 0-based):
     * `0xAA` (`170`) = **Power Limit ON**
     * `0x55` (`85`) = **Power Limit OFF**
  2. Write the desired target percentage to register `3052` (or `3051` 0-based) scaled by `0.01%` (e.g., `5000` = `50%`, `0` = `0%`, `10000` = `100%`).
* **Set Inverter System Time / Clock:**
  * Registers `3000 to 3005` (or `2999 to 3004` 0-based): Year (`0–99`), Month (`1–12`), Day (`1–31`), Hour (`0–23`), Minute (`0–59`), Second (`0–59`).

---

## How This Was Investigated (Reproducing With AI)

This entire investigation—reverse-engineering the inverter on the local network, mapping out the Modbus registers, and generating the code and documentation—was performed by AI using **Google Antigravity** (running on **Windows with Ubuntu WSL**) powered by **Gemini 4 Argon (Medium)**.

> **Why run the AI agent inside Ubuntu WSL / Linux?**  
> Linux (and therefore Ubuntu on WSL under Windows) ships out-of-the-box with a much richer set of networking, text-processing, and diagnostic tools than a standard Windows shell (`cmd` / PowerShell). Utilities such as `python3` (for raw TCP/UDP sockets and binary `struct` packing), real `curl` (without PowerShell aliases, for inspecting raw HTTP headers), `ping`, `ip`, `grep`, `tr` (e.g., for stripping null bytes from broken embedded CGI responses), and `git` are all available by default. This allows an AI agent to probe network protocols, craft binary Modbus frames, and parse device responses on the fly without installing extra software.

Do you have another inverter or smart device whose manufacturer went bankrupt or started charging for cloud access? Here is how you can reproduce this in a few minutes using Antigravity (or a similar agentic coding assistant):

1. **Ensure your WSL / Linux terminal can reach the same subnet as the inverter** and look up the inverter's IP address in your router.
2. **Give the AI agent a prompt like:**
   > *"The manufacturer of my inverter (<Brand / Model>) went bankrupt and I can no longer access my data. Make sure I can read the inverter locally. Its IP address is `<IP-ADDRESS>`."*
3. **What the AI agent autonomously executes from WSL:**
   * **Port Discovery:** Scans common inverter ports on the local IP (such as TCP `80`, `443`, `502` for Modbus TCP, `8899` for Solarman V5, and UDP `48899`).
   * **HTTP & OEM Identification:** Inspects HTTP headers and embedded web pages on port `80` (which immediately revealed `WWW-authenticate: Basic realm="solis"` on an `lwIP/1.3.1` stack with default credentials `admin` / `123456789`).
   * **Modbus Register Probing:** Sends test requests to port `502` (Function Code `0x04` Input Registers and `0x03` Holding Registers), reads raw register blocks (`2999–3079`), and cross-references them against Solis/Ginlong Modbus specifications to verify scaling, endianness, and serial number encoding.
   * **Integration & Code Generation:** Writes a ready-to-use local reader script and inspects the source code of existing Home Assistant integrations (like `Pho3niX90/solis_modbus`) to match the exact model template (`3P(3-20)K-4G`) to the discovered registers.

---

## License

This project is licensed under the [MIT License](LICENSE) — free to use, modify, and distribute.
