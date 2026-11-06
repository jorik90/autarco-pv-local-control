#!/usr/bin/env python3
"""
Lokaal uitleesscript voor Autarco / Solis omvormer via Modbus TCP (poort 502).
Geen externe libraries nodig (gebruikt alleen de standaard Python-bibliotheek).
"""

import argparse
import csv
import json
import os
import socket
import struct
import sys
import time
from datetime import datetime
from typing import Any, Dict, Tuple

DEFAULT_HOST = os.environ.get("AUTARCO_HOST", "192.168.1.100")
DEFAULT_PORT = int(os.environ.get("AUTARCO_PORT", "502"))
DEFAULT_UNIT_ID = int(os.environ.get("AUTARCO_UNIT_ID", "1"))
DEFAULT_TIMEOUT = 5.0


class AutarcoModbusClient:
    """Eenvoudige Modbus TCP-client voor Autarco (Solis/Ginlong) omvormers."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, unit_id: int = DEFAULT_UNIT_ID, timeout: float = DEFAULT_TIMEOUT):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.sock: socket.socket | None = None
        self._tx_id = 0

    def connect(self) -> None:
        if self.sock is not None:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        s.connect((self.host, self.port))
        self.sock = s

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def __enter__(self) -> "AutarcoModbusClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _recv_exact(self, n: int) -> bytes:
        assert self.sock is not None
        buf = bytearray()
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("Verbinding gesloten door omvormer")
            buf.extend(chunk)
        return bytes(buf)

    def read_input_registers(self, start_address: int, count: int) -> Tuple[int, ...]:
        """Leest Modbus Input Registers (Function Code 0x04)."""
        if self.sock is None:
            self.connect()
        assert self.sock is not None

        self._tx_id = (self._tx_id + 1) & 0xFFFF
        # MBAP Header (7 bytes): Transaction ID (2), Protocol ID=0 (2), Length=6 (2), Unit ID (1)
        # PDU (5 bytes): Function Code=4 (1), Start Address (2), Quantity (2)
        req = struct.pack(">HHHBBHH", self._tx_id, 0, 6, self.unit_id, 4, start_address, count)
        self.sock.sendall(req)

        header = self._recv_exact(7)
        rx_tx_id, proto_id, length, rx_unit_id = struct.unpack(">HHHB", header)
        payload = self._recv_exact(length - 1)

        func_code = payload[0]
        if func_code & 0x80:
            exc_code = payload[1] if len(payload) > 1 else -1
            raise RuntimeError(f"Modbus foutcode ontvangen: functie 0x{func_code:02x}, exception {exc_code}")

        byte_count = payload[1]
        reg_bytes = payload[2 : 2 + byte_count]
        if len(reg_bytes) != count * 2:
            raise RuntimeError(f"Onverwacht aantal bytes ontvangen: {len(reg_bytes)} i.p.v. {count * 2}")

        return struct.unpack(f">{count}H", reg_bytes)


def _u32(high: int, low: int) -> int:
    return (high << 16) | low


def _s16(val: int) -> int:
    return val - 0x10000 if val >= 0x8000 else val


def _decode_serial(regs: Tuple[int, ...]) -> str:
    # Solis slaat het 16-karakter serienummer (hex) in 3060..3063 op met verwisselde nibbles per byte (of achterstevoren per 16-bit woord)
    return "".join(f"{r:04X}"[::-1] for r in regs)


STATUS_MAP = {
    0: "Wachten op zon / Stand-by (Waiting)",
    1: "Opstarten / Netcontrole (Open Run)",
    2: "Zacht opstarten (Soft Run)",
    3: "Normaal in bedrijf (Generating)",
}


def read_inverter_data(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, unit_id: int = DEFAULT_UNIT_ID, timeout: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Leest alle relevante registers van de Autarco omvormer en geeft een gestructureerde dict terug."""
    reg_map: Dict[int, int] = {}

    with AutarcoModbusClient(host=host, port=port, unit_id=unit_id, timeout=timeout) as client:
        for base in (2999, 3019, 3039, 3059):
            vals = client.read_input_registers(base, 20)
            for idx, v in enumerate(vals):
                reg_map[base + idx] = v
            time.sleep(0.15)

    def r(addr: int) -> int:
        return reg_map[addr]

    ac_power_w = _u32(r(3004), r(3005))
    dc_power_w = _u32(r(3006), r(3007))
    total_energy_kwh = _u32(r(3008), r(3009))
    energy_this_month_kwh = _u32(r(3010), r(3011))
    energy_last_month_kwh = _u32(r(3012), r(3013))
    energy_today_kwh = round(r(3014) * 0.1, 1)
    energy_yesterday_kwh = round(r(3015) * 0.1, 1)
    energy_this_year_kwh = _u32(r(3016), r(3017))
    energy_last_year_kwh = _u32(r(3018), r(3019))

    dc1_voltage_v = round(r(3021) * 0.1, 1)
    dc1_current_a = round(r(3022) * 0.1, 1)
    dc2_voltage_v = round(r(3023) * 0.1, 1)
    dc2_current_a = round(r(3024) * 0.1, 1)
    dc_bus_voltage_v = round(r(3031) * 0.1, 1)

    ac_l1_voltage_v = round(r(3033) * 0.1, 1)
    ac_l2_voltage_v = round(r(3034) * 0.1, 1)
    ac_l3_voltage_v = round(r(3035) * 0.1, 1)
    ac_l1_current_a = round(r(3036) * 0.1, 1)
    ac_l2_current_a = round(r(3037) * 0.1, 1)
    ac_l3_current_a = round(r(3038) * 0.1, 1)

    temperature_c = round(_s16(r(3041)) * 0.1, 1)
    grid_frequency_hz = round(r(3042) * 0.01, 2)
    status_code = r(3043)
    status_text = STATUS_MAP.get(status_code, f"Onbekend ({status_code})")

    serial_number = _decode_serial((r(3060), r(3061), r(3062), r(3063)))

    inv_year = 2000 + r(3072)
    inv_month = r(3073)
    inv_day = r(3074)
    inv_hour = r(3075)
    inv_min = r(3076)
    inv_sec = r(3077)
    inverter_time = f"{inv_year:04d}-{inv_month:02d}-{inv_day:02d} {inv_hour:02d}:{inv_min:02d}:{inv_sec:02d}"

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "inverter_time": inverter_time,
        "host": host,
        "serial_number": serial_number,
        "product_model": f"0x{r(2999):04X}",
        "dsp_version": f"0x{r(3000):04X}",
        "lcd_version": f"0x{r(3001):04X}",
        "status_code": status_code,
        "status_text": status_text,
        "ac_power_w": ac_power_w,
        "dc_power_w": dc_power_w,
        "temperature_c": temperature_c,
        "grid_frequency_hz": grid_frequency_hz,
        "energy_today_kwh": energy_today_kwh,
        "energy_yesterday_kwh": energy_yesterday_kwh,
        "energy_this_month_kwh": energy_this_month_kwh,
        "energy_last_month_kwh": energy_last_month_kwh,
        "energy_this_year_kwh": energy_this_year_kwh,
        "energy_last_year_kwh": energy_last_year_kwh,
        "total_energy_kwh": total_energy_kwh,
        "dc1_voltage_v": dc1_voltage_v,
        "dc1_current_a": dc1_current_a,
        "dc1_power_w": round(dc1_voltage_v * dc1_current_a, 1),
        "dc2_voltage_v": dc2_voltage_v,
        "dc2_current_a": dc2_current_a,
        "dc2_power_w": round(dc2_voltage_v * dc2_current_a, 1),
        "dc_bus_voltage_v": dc_bus_voltage_v,
        "ac_l1_voltage_v": ac_l1_voltage_v,
        "ac_l1_current_a": ac_l1_current_a,
        "ac_l2_voltage_v": ac_l2_voltage_v,
        "ac_l2_current_a": ac_l2_current_a,
        "ac_l3_voltage_v": ac_l3_voltage_v,
        "ac_l3_current_a": ac_l3_current_a,
    }


def print_table(data: Dict[str, Any]) -> None:
    print("=" * 60)
    print(f" Autarco / Solis Omvormer ({data['host']}) - {data['timestamp']}")
    print("=" * 60)
    print(f" Serienummer       : {data['serial_number']}")
    print(f" Status            : {data['status_text']} (code {data['status_code']})")
    print(f" Tijd op omvormer  : {data['inverter_time']}")
    print("-" * 60)
    print(" ACTUEEL VERMOGEN & TEMPERATUUR")
    print(f"   AC Vermogen     : {data['ac_power_w']} W")
    print(f"   DC Vermogen     : {data['dc_power_w']} W")
    print(f"   Temperatuur     : {data['temperature_c']:.1f} °C")
    print(f"   Netfrequentie   : {data['grid_frequency_hz']:.2f} Hz")
    print("-" * 60)
    print(" ENERGIE OPBRENGST")
    print(f"   Vandaag         : {data['energy_today_kwh']:.1f} kWh")
    print(f"   Gisteren        : {data['energy_yesterday_kwh']:.1f} kWh")
    print(f"   Deze maand      : {data['energy_this_month_kwh']} kWh")
    print(f"   Vorige maand    : {data['energy_last_month_kwh']} kWh")
    print(f"   Dit jaar        : {data['energy_this_year_kwh']} kWh")
    print(f"   Vorig jaar      : {data['energy_last_year_kwh']} kWh")
    print(f"   Totaal (Leven)  : {data['total_energy_kwh']} kWh")
    print("-" * 60)
    print(" ZONNEPANELEN (DC STRINGS)")
    print(f"   String 1 (PV1)  : {data['dc1_voltage_v']:5.1f} V  | {data['dc1_current_a']:4.1f} A  | {data['dc1_power_w']:6.1f} W")
    print(f"   String 2 (PV2)  : {data['dc2_voltage_v']:5.1f} V  | {data['dc2_current_a']:4.1f} A  | {data['dc2_power_w']:6.1f} W")
    print(f"   DC Busspanning  : {data['dc_bus_voltage_v']:5.1f} V")
    print("-" * 60)
    print(" NETZIJDE (AC 3-FASE)")
    print(f"   Fase L1         : {data['ac_l1_voltage_v']:5.1f} V  | {data['ac_l1_current_a']:4.1f} A")
    print(f"   Fase L2         : {data['ac_l2_voltage_v']:5.1f} V  | {data['ac_l2_current_a']:4.1f} A")
    print(f"   Fase L3         : {data['ac_l3_voltage_v']:5.1f} V  | {data['ac_l3_current_a']:4.1f} A")
    print("=" * 60)


def write_csv(data: Dict[str, Any], filepath: str | None) -> None:
    fieldnames = list(data.keys())
    if filepath:
        file_exists = os.path.isfile(filepath) and os.path.getsize(filepath) > 0
        with open(filepath, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(data)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lees je Autarco (Solis) omvormer lokaal uit via Modbus TCP."
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"IP-adres van de omvormer (standaard: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Modbus TCP-poort (standaard: {DEFAULT_PORT})")
    parser.add_argument("--unit", type=int, default=DEFAULT_UNIT_ID, help=f"Modbus Unit ID (standaard: {DEFAULT_UNIT_ID})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Socket time-out in seconden")
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table", help="Uitvoerformaat op standaarduitvoer (table, json, csv)")
    parser.add_argument("--csv-file", metavar="PAD", help="Voeg de meting toe als rij aan een CSV-bestand (maakt header aan als bestand nieuw is)")
    parser.add_argument("--json-file", metavar="PAD", help="Schrijf de meting weg naar een JSON-bestand")
    parser.add_argument("--watch", type=int, metavar="SECONDEN", help="Blijf elke N seconden uitlezen (bijv. --watch 10)")

    args = parser.parse_args()

    try:
        while True:
            data = read_inverter_data(host=args.host, port=args.port, unit_id=args.unit, timeout=args.timeout)

            if args.format == "json":
                print(json.dumps(data, indent=2, ensure_ascii=False))
            elif args.format == "csv":
                write_csv(data, None)
            else:
                print_table(data)

            if args.csv_file:
                write_csv(data, args.csv_file)

            if args.json_file:
                with open(args.json_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            if not args.watch:
                break
            time.sleep(args.watch)
    except KeyboardInterrupt:
        print("\nGestopt door gebruiker.")
        return 0
    except Exception as exc:
        print(f"Fout bij uitlezen van omvormer ({args.host}:{args.port}): {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
