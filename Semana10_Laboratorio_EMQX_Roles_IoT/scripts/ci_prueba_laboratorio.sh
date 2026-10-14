#!/usr/bin/env bash
# Prueba de integración del laboratorio (usada por GitHub Actions; también corre en Linux/macOS).
# Reproduce las partes B, D, F y G del README: levantar, publicar, suscribir, CSV y falla/recuperación.
set -euo pipefail
cd "$(dirname "$0")/.."

export INTERVAL_SECONDS="${INTERVAL_SECONDS:-1}"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-semana10-ci}"  # aislado: no toca los volúmenes del laboratorio del estudiante
CSV=data/telemetria.csv

paso() { printf '\n== %s\n' "$*"; }
falla() { echo "FALLA: $*" >&2; docker compose ps; docker compose logs --tail 40; exit 1; }
esperar() { # esperar <segundos> <descripción> <comando...>
  local t=$1 d=$2; shift 2
  for _ in $(seq 1 "$t"); do if "$@" >/dev/null 2>&1; then echo "OK  $d"; return 0; fi; sleep 1; done
  falla "$d (tras ${t}s)"
}
filas_telemetria() { grep -c '/telemetria,' "$CSV" 2>/dev/null || echo 0; }

trap 'docker compose down -v --remove-orphans >/dev/null 2>&1 || true' EXIT
rm -f "$CSV"

paso "Validar docker-compose.yml"
docker compose config --quiet && echo "OK  compose válido"

paso "Parte B: levantar EMQX, sensor y monitor"
docker compose up -d --build --wait --wait-timeout 180
for s in semana10-emqx semana10-sensor semana10-monitor; do
  [ "$(docker inspect -f '{{.State.Running}}' "$s")" = true ] || falla "$s no está corriendo"
  echo "OK  $s corriendo"
done
esperar 60 "EMQX healthy" sh -c '[ "$(docker inspect -f "{{.State.Health.Status}}" semana10-emqx)" = healthy ]'

paso "Parte C: dashboard EMQX responde en :${DASHBOARD_HOST_PORT:-18083}"
esperar 60 "dashboard HTTP 200" curl -fsS -o /dev/null "http://127.0.0.1:${DASHBOARD_HOST_PORT:-18083}/"

paso "Parte D: publicación y suscripción"
esperar 30 "sensor publica [PUB]" sh -c 'docker compose logs sensor | grep -q "\[PUB\] iot/utp/semana10/equipo01/telemetria"'
esperar 30 "monitor suscrito a iot/utp/semana10/+/+" sh -c 'docker compose logs monitor | grep -q "\[SUB\] iot/utp/semana10/+/+"'
esperar 30 "monitor recibe [MSG]" sh -c 'docker compose logs monitor | grep -q "\[MSG\] iot/utp/semana10/equipo01/telemetria"'
esperar 30 "EMQX lista 2 clientes conectados" sh -c '[ "$(docker exec semana10-emqx emqx ctl clients list | grep -c "connected=true")" -ge 2 ]'

paso "Parte F: histórico CSV"
esperar 30 "CSV con >= 3 filas de telemetría" sh -c "[ \$(grep -c '/telemetria,' $CSV) -ge 3 ]"
python3 - "$CSV" <<'PY' || falla "CSV con columnas o valores inesperados"
import csv, sys
COLS = ["recibido_en", "topic", "equipo", "dispositivo", "temperatura_c", "humedad_pct", "bateria_pct", "estado", "fecha_origen"]
reader = csv.DictReader(open(sys.argv[1], encoding="utf-8-sig"))
assert reader.fieldnames == COLS, reader.fieldnames
print("OK  columnas del CSV")
rows = [r for r in reader if r["topic"].endswith("/telemetria")]
for r in rows:
    assert 20.0 <= float(r["temperatura_c"]) <= 31.5, r
    assert 40.0 <= float(r["humedad_pct"]) <= 78.0, r
    assert 72.0 <= float(r["bateria_pct"]) <= 100.0, r
print(f"OK  {len(rows)} filas con temperatura, humedad y batería en rango")
PY

paso "Parte G: falla del nodo (Last Will) y recuperación"
docker compose stop sensor
esperar 30 "monitor recibe estado offline (Last Will)" sh -c 'docker compose logs monitor | grep -q "\"estado\": \"offline\""'
antes=$(filas_telemetria); sleep 4
[ "$(filas_telemetria)" -eq "$antes" ] && echo "OK  sin telemetría nueva con el sensor detenido" || falla "llegó telemetría con el sensor detenido"
docker compose start sensor
esperar 30 "telemetría se reanuda" sh -c "[ \$(grep -c '/telemetria,' $CSV) -gt $antes ]"
esperar 30 "estado vuelve a online" sh -c "tail -n 20 $CSV | grep -q ',online,'"

paso "Resultado"
echo "Laboratorio Semana 10 verificado: $(filas_telemetria) mensajes de telemetría en $CSV"
