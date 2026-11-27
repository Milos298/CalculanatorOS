"""Pico drivers. Wi-Fi and LED modules load only when needed."""
import time

def is_hardware():
    """Return True when running under MicroPython on a board with machine.Pin."""
    try:
        import machine
        return hasattr(machine, "Pin")
    except ImportError:
        return False

def led_set(state):
    try:
        from machine import Pin
        Pin("LED", Pin.OUT).value(1 if state else 0)
        return True, "HARDWARE LED is " + ("on." if state else "off.")
    except Exception as error:
        return False, "LED is unavailable: " + str(error)

def led_state():
    try:
        from machine import Pin
        return bool(Pin("LED", Pin.OUT).value()), None
    except Exception as error:
        return None, "LED state is unavailable: " + str(error)

def chip_temperature_celsius():
    """Read the RP2350's internal sensor; this is chip temperature, not room temperature."""
    try:
        from machine import ADC
        sensor = ADC(4)  # RP2350 internal temperature channel
        voltage = sensor.read_u16() * (3.3 / 65535)
        temperature = 27 - (voltage - 0.706) / 0.001721
        return temperature, None
    except Exception as error:
        return None, "Chip temperature sensor is unavailable: " + str(error)

def wifi_interface():
    try:
        import network
        mode = getattr(network, "STA_IF", None)
        if mode is None:
            mode = network.WLAN.IF_STA
        return network, network.WLAN(mode)
    except Exception:
        return None, None

def wifi_scan():
    _, wlan = wifi_interface()
    if wlan is None:
        return None, "Wi-Fi library is unavailable."
    try:
        wlan.active(True)
        return wlan.scan(), None
    except Exception as error:
        return None, str(error)

def wifi_connect(ssid, password):
    _, wlan = wifi_interface()
    if wlan is None:
        return False, "Wi-Fi library is unavailable."
    try:
        wlan.active(True)
        wlan.connect(ssid, password)
        for _ in range(20):
            if wlan.isconnected():
                return True, "Connected. IP: " + wlan.ifconfig()[0]
            time.sleep(1)
        return False, "Connection failed. Check the password and signal."
    except Exception as error:
        return False, "Wi-Fi error: " + str(error)

def wifi_status():
    _, wlan = wifi_interface()
    if wlan is None:
        return "Wi-Fi library is unavailable."
    try:
        if wlan.isconnected():
            return "Connected. IP: " + wlan.ifconfig()[0]
        return "Wi-Fi is not connected."
    except Exception as error:
        return "Wi-Fi error: " + str(error)

def bluetooth_status():
    try:
        import bluetooth
        ble = bluetooth.BLE()
        return "Bluetooth LE is " + ("on." if ble.active() else "off.")
    except Exception as error:
        return "Bluetooth LE is unavailable: " + str(error)

def bluetooth_scan(duration_ms=5000):
    try:
        import bluetooth
    except Exception as error:
        return None, "Bluetooth LE is unavailable: " + str(error)

    ble = bluetooth.BLE()
    results = {}
    irq_scan_result = getattr(bluetooth, "_IRQ_SCAN_RESULT", 5)

    def decode_name(payload):
        index = 0
        while index < len(payload):
            size = payload[index]
            if size == 0 or index + size >= len(payload):
                break
            ad_type = payload[index + 1]
            if ad_type in (0x08, 0x09):
                try:
                    return payload[index + 2:index + size + 1].decode()
                except Exception:
                    return "(name unavailable)"
            index += size + 1
        return "(unnamed)"

    def on_event(event, data):
        if event == irq_scan_result:
            _, address, _, rssi, payload = data
            address_text = ":".join("%02X" % byte for byte in bytes(address))
            results[address_text] = (decode_name(bytes(payload)), rssi)

    try:
        ble.active(True)
        ble.irq(on_event)
        ble.gap_scan(duration_ms, active=True)
        started = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), started) < duration_ms + 500:
            time.sleep_ms(50)
        ble.gap_scan(None)
        ble.irq(None)
        return results, None
    except Exception as error:
        try:
            ble.gap_scan(None)
            ble.irq(None)
        except Exception:
            pass
        return None, str(error)
