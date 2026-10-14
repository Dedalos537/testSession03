import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt

HOST = os.getenv("MQTT_HOST", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_FILTER = os.getenv("TOPIC_FILTER", "iot/utp/semana10/+/+")
CSV_PATH = Path(os.getenv("CSV_PATH", "/app/data/telemetria.csv"))

CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

FIELDS = [
    "recibido_en",
    "topic",
    "equipo",
    "dispositivo",
    "temperatura_c",
    "humedad_pct",
    "bateria_pct",
    "estado",
    "fecha_origen",
]

if not CSV_PATH.exists():
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writeheader()

def now_utc():
    return datetime.now(timezone.utc).isoformat()

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[OK] Monitor conectado a {HOST}:{PORT}")
        print(f"[SUB] {TOPIC_FILTER}")
        client.subscribe(TOPIC_FILTER, qos=1)
    else:
        print(f"[ERROR] Conexión fallida. Código: {reason_code}")

def on_message(client, userdata, msg):
    raw = msg.payload.decode("utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"valor": raw}

    row = {
        "recibido_en": now_utc(),
        "topic": msg.topic,
        "equipo": data.get("equipo", ""),
        "dispositivo": data.get("dispositivo", ""),
        "temperatura_c": data.get("temperatura_c", ""),
        "humedad_pct": data.get("humedad_pct", ""),
        "bateria_pct": data.get("bateria_pct", ""),
        "estado": data.get("estado", ""),
        "fecha_origen": data.get("fecha", ""),
    }

    with CSV_PATH.open("a", newline="", encoding="utf-8-sig") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(row)

    print(f"[MSG] {msg.topic} -> {raw}")

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="monitor-semana10",
    protocol=mqtt.MQTTv311,
)
client.on_connect = on_connect
client.on_message = on_message

print("=== MONITOR MQTT — SEMANA 10 ===")
print(f"CSV: {CSV_PATH}")

client.connect(HOST, PORT, keepalive=60)
client.loop_forever()
