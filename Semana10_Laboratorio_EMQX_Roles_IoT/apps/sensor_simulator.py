import json
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

HOST = os.getenv("MQTT_HOST", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TEAM_ID = os.getenv("TEAM_ID", "equipo01").strip()
DEVICE_ID = os.getenv("DEVICE_ID", "esp32-virtual-01").strip()
INTERVAL = float(os.getenv("INTERVAL_SECONDS", "5"))

BASE_TOPIC = f"iot/utp/semana10/{TEAM_ID}"
TELEMETRY_TOPIC = f"{BASE_TOPIC}/telemetria"
STATUS_TOPIC = f"{BASE_TOPIC}/estado"

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[OK] Conectado a MQTT {HOST}:{PORT}")
        online = {
            "equipo": TEAM_ID,
            "dispositivo": DEVICE_ID,
            "estado": "online",
            "fecha": utc_now(),
        }
        client.publish(STATUS_TOPIC, json.dumps(online), qos=1, retain=True)
    else:
        print(f"[ERROR] Falló la conexión MQTT. Código: {reason_code}")

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id=f"{DEVICE_ID}-{TEAM_ID}",
    protocol=mqtt.MQTTv311,
)

offline = {
    "equipo": TEAM_ID,
    "dispositivo": DEVICE_ID,
    "estado": "offline",
}
client.will_set(STATUS_TOPIC, json.dumps(offline), qos=1, retain=True)
client.on_connect = on_connect

print("=== SENSOR VIRTUAL — SEMANA 10 ===")
print(f"Equipo: {TEAM_ID}")
print(f"Dispositivo: {DEVICE_ID}")
print(f"Topic telemetría: {TELEMETRY_TOPIC}")
print(f"Intervalo: {INTERVAL} s")

client.connect(HOST, PORT, keepalive=60)
client.loop_start()

try:
    while True:
        # Simulación didáctica de un nodo IoT ambiental.
        temperatura = round(random.uniform(20.0, 31.5), 1)
        humedad = round(random.uniform(40.0, 78.0), 1)
        bateria = round(random.uniform(72.0, 100.0), 1)

        payload = {
            "equipo": TEAM_ID,
            "dispositivo": DEVICE_ID,
            "temperatura_c": temperatura,
            "humedad_pct": humedad,
            "bateria_pct": bateria,
            "fecha": utc_now(),
        }

        result = client.publish(
            TELEMETRY_TOPIC,
            json.dumps(payload, ensure_ascii=False),
            qos=1,
            retain=False,
        )
        result.wait_for_publish()
        print("[PUB]", TELEMETRY_TOPIC, json.dumps(payload, ensure_ascii=False))
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    print("\nDeteniendo sensor virtual...")

finally:
    online = {
        "equipo": TEAM_ID,
        "dispositivo": DEVICE_ID,
        "estado": "offline",
        "fecha": utc_now(),
    }
    try:
        client.publish(STATUS_TOPIC, json.dumps(online), qos=1, retain=True).wait_for_publish()
    except Exception:
        pass
    client.loop_stop()
    client.disconnect()
