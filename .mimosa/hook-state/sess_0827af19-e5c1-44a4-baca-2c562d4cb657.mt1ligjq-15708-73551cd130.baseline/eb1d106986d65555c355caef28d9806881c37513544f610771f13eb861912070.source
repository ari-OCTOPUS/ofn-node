# =============================================================================
# deploy/esp32/firmware.py — ESP32 Sensor / Watchdog firmware
# =============================================================================
# MicroPython firmware for ESP32 devices.
# Flash MicroPython first: https://micropython.org/download/ESP32_GENERIC/
# Then upload this file as main.py via mpremote or Thonny.
#
# Each ESP32 is positioned near one worker node (or the main OPi5+).
# It monitors ambient temperature via an optional DS18B20 sensor and
# sends heartbeat HTTP POSTs to the fleet manager.
#
# Wiring (optional DS18B20 temperature sensor):
#   DS18B20 data → GPIO 4
#   VCC → 3.3V, GND → GND, 4.7kΩ pull-up to 3.3V
#
# Config: edit WIFI_SSID, WIFI_PASS, MANAGER_URL, ESP_ID below.
# =============================================================================

import ujson
import utime
import urequests
import machine
import network

# ── User config (edit per device) ────────────────────────────────────────────
WIFI_SSID    = "YOUR_WIFI_SSID"
WIFI_PASS    = "YOUR_WIFI_PASSWORD"
MANAGER_URL  = "http://192.168.1.100:7700"
ESP_ID       = "s01"           # s01..s10 — unique per ESP32
TARGET_WORKER = "w01"          # which worker node this ESP monitors (for temp labelling)
REPORT_INTERVAL = 60           # seconds between reports
HAS_TEMP_SENSOR = False        # set True if DS18B20 wired on GPIO 4
TEMP_PIN        = 4

# ── LED blink ─────────────────────────────────────────────────────────────────
led = machine.Pin(2, machine.Pin.OUT)   # onboard LED (GPIO2 on most ESP32)

def blink(n=1, ms=100):
    for _ in range(n):
        led.on();  utime.sleep_ms(ms)
        led.off(); utime.sleep_ms(ms)


# ── WiFi ──────────────────────────────────────────────────────────────────────
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi:", WIFI_SSID)
        wlan.connect(WIFI_SSID, WIFI_PASS)
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            utime.sleep(1)
            timeout -= 1
            print(".", end="")
        print()
    if wlan.isconnected():
        print("WiFi OK:", wlan.ifconfig()[0])
        blink(3, 100)
        return True
    else:
        print("WiFi FAILED")
        return False


# ── Temperature (DS18B20) ──────────────────────────────────────────────────────
def read_temp_c() -> float:
    if not HAS_TEMP_SENSOR:
        return 0.0
    try:
        import onewire, ds18x20
        ow  = onewire.OneWire(machine.Pin(TEMP_PIN))
        ds  = ds18x20.DS18X20(ow)
        roms = ds.scan()
        if not roms:
            return 0.0
        ds.convert_temp()
        utime.sleep_ms(750)
        return ds.read_temp(roms[0])
    except Exception as e:
        print("Temp sensor error:", e)
        return 0.0


# ── CPU load proxy (ESP32 internal temp via ADC hall sensor) ──────────────────
def read_internal_temp() -> float:
    """ESP32 hall sensor gives rough internal die temp — not ambient."""
    try:
        import esp32
        return esp32.hall_sensor() * 0.1   # rough conversion, not accurate
    except Exception:
        return 0.0


# ── Report to manager ─────────────────────────────────────────────────────────
def send_report(temp_c: float, uptime_s: int):
    payload = ujson.dumps({
        "worker_id":   ESP_ID,
        "ip":          "",
        "role":        "SENSOR",
        "algo":        "",
        "symbol":      "",
        "hashrate_hs": 0.0,
        "cpu_temp_c":  temp_c,
        "cpu_load_pct": 0.0,
        "ram_used_pct": 0.0,
        "uptime_s":    uptime_s,
        "miner_running": False,
    })
    try:
        resp = urequests.post(
            MANAGER_URL + "/report",
            headers={"Content-Type": "application/json"},
            data=payload,
            timeout=5,
        )
        resp.close()
        blink(1, 50)
        return True
    except Exception as e:
        print("Report error:", e)
        blink(5, 50)   # rapid blink = comm error
        return False


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    start_ms = utime.ticks_ms()
    wlan_ok  = connect_wifi()

    # Register with manager
    if wlan_ok:
        try:
            reg = urequests.post(
                MANAGER_URL + "/register",
                headers={"Content-Type": "application/json"},
                data=ujson.dumps({"worker_id": ESP_ID, "role": "SENSOR", "ip": ""}),
                timeout=5,
            )
            reg.close()
            print("Registered:", ESP_ID)
        except Exception as e:
            print("Register error:", e)

    while True:
        if not network.WLAN(network.STA_IF).isconnected():
            print("WiFi lost — reconnecting...")
            connect_wifi()

        temp   = read_temp_c()
        uptime = utime.ticks_diff(utime.ticks_ms(), start_ms) // 1000
        print(f"[{ESP_ID}] temp={temp:.1f}°C  uptime={uptime}s")

        send_report(temp, uptime)
        utime.sleep(REPORT_INTERVAL)


main()
