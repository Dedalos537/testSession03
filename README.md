# TA 03 · Sistema de control de temperatura IoT

Rama `TA03-1` (parte de `TA03`). Tiene tres entregables:

1. **Laboratorio Packet Tracer** (`packet-tracer/Temperature_Control_System.pkt`): dos oficinas con sensores IoT conectadas por un ISP a un servidor IoT y a un servidor DNS.
2. **Simulador web** (`index.html`): página autocontenida que representa el pipeline MQTT → EMQX → Telegraf → InfluxDB → Grafana con datos generados en el navegador. Es una simulación: no hay broker, base de datos ni hardware reales.
3. **Actividad 10** (`Semana10_Laboratorio_EMQX_Roles_IoT/`): laboratorio con EMQX real en Docker, un sensor virtual en Python que publica por MQTT y un monitor que guarda el histórico en CSV. Ver la sección [Actividad 10](#actividad-10-semana10_laboratorio_emqx_roles_iot).

## Estructura

```
index.html                         Simulador (un solo archivo, sin build)
packet-tracer/                     Laboratorio .pkt (Packet Tracer 9.0) + licencia GPL-2.0 del proyecto original
tools/pkt_codec.py                 Codifica/decodifica el formato .pkt a XML
tools/verify_pkt.py                Verifica la configuración del laboratorio (22 comprobaciones)
tools/check-inline-js.mjs          Compila los <script> inline del HTML
tests/simulador.spec.mjs           Tests E2E con Playwright (escritorio y móvil)
.github/workflows/ci.yml           Pipeline CI/CD
```

## Laboratorio Packet Tracer

### Direccionamiento

| Equipo | Interfaz | Dirección |
|---|---|---|
| ISP (2911) | Gi0/0 → Switch | 10.0.0.1/24 |
| ISP | Gi0/1 → WAN (Oficina 1) | 209.165.200.225/27, pool DHCP `WAN` |
| ISP | Gi0/2 → WAN-2 (Oficina 2) | 209.165.201.225/27, pool DHCP `CELL` |
| IOT-SERVER | Fa0 | 10.0.0.253/24, gw 10.0.0.1 |
| DNS-SERVER | Fa0 | 10.0.0.254/24, gw 10.0.0.1 |
| Gateways de oficina (DLC100) | LAN | 192.168.25.1/24, DHCP .100–.149, NAT |

### Correcciones aplicadas al archivo original

- DHCP del ISP: `default-router` apuntaba a la dirección de broadcast (`.255`); ahora apunta a `.225`.
- `ip dhcp excluded-address` tenía los rangos invertidos; ahora es `.225 .229`.
- La configuración del ISP se guardó en el arranque (startup-config = running-config). Se agregaron `hostname ISP` y un banner.
- DNS-SERVER: registros A `iot.com`, `www.iot.com` e `iotserver.com` → 10.0.0.253, y `dns.com` → 10.0.0.254.
- Oficina 2 usa su propio SSID (`Office2`) para no chocar con `HomeGateway` de la Oficina 1.

### Cómo probarlo

1. Abre el `.pkt` en Packet Tracer 9.0 y pulsa **Fast Forward Time** varias veces hasta que DHCP converja.
2. En **laptop - 1** → *Desktop* → *Command Prompt*:
   ```
   ipconfig            (debe mostrar 192.168.25.x)
   ping 10.0.0.253
   nslookup iot.com    (el primer intento puede expirar mientras se resuelve ARP; repítelo)
   ```
3. **Ver la página IoT dentro de Packet Tracer:** en **laptop - 1** → *Desktop* → *Web Browser*, escribe `http://iot.com` (o `http://10.0.0.253`) y pulsa *Go*. Inicia sesión con **admin / admin**. Verás el **IoT Monitor** con el *Thermostat* y el *Temperature* monitor: lectura en vivo, cambio de estado (Off / Cooling / Heating / Auto) y umbrales.
4. Repite desde **laptop - 2** (Oficina 2).
5. Para probar la reacción física, cambia la temperatura ambiente (*Environment*) o usa el termostato: el calefactor o el enfriador se activan y el LCD del MCU muestra el valor.

La verificación automática del archivo se ejecuta con:

```
pip install twofish==0.3.0      # Python 3.11
python tools/verify_pkt.py packet-tracer/Temperature_Control_System.pkt
```

## Simulador web

Ábrelo con doble clic en `index.html`, o publícalo con GitHub Pages (lo hace el pipeline). Incluye:

- Topología SVG animada: Sensor DHT22 + ESP32 → Gateway Wi-Fi → Docker host (EMQX → Telegraf → InfluxDB) → Grafana.
- Controles: temperatura base, ruido, intervalo de muestreo, QoS 0/1/2, pausar/reanudar e inyección de pico térmico.
- Consola con pestañas EMQX (CONNECT, PUBLISH, PUBACK, PUBREC/PUBREL/PUBCOMP) e InfluxDB (line protocol).
- Dashboard: gauge, máx/mín/media, humedad y gráficos de temperatura y humedad con tooltip.
- Exportación del buffer a CSV y JSON.

Funciona sin conexión: los gráficos se dibujan con `<canvas>` propio y las fuentes caen a system-ui/monospace si Google Fonts no carga.

### Desarrollo local

```
npm ci
npm run lint                     # html-validate + compilación de JS
npx playwright install chromium
npm test                         # 7 escenarios × (desktop, mobile)
```

## Actividad 10: Semana10_Laboratorio_EMQX_Roles_IoT

La guía completa está en [`Semana10_Laboratorio_EMQX_Roles_IoT/README.md`](Semana10_Laboratorio_EMQX_Roles_IoT/README.md). Para iniciarlo:

```
cd Semana10_Laboratorio_EMQX_Roles_IoT
docker compose up -d --build
```

- Dashboard EMQX: http://localhost:18083 (admin / public; pide cambiarla en el primer ingreso).
- Topics: `iot/utp/semana10/equipo01/telemetria` y `.../estado` (QoS 1, Last Will `offline`).
- Histórico: `data/telemetria.csv`.

Cambios respecto al ZIP original:

- `apps/Dockerfile`: se agregó `PYTHONUNBUFFERED=1`. Sin esto, `docker compose logs sensor` y `docker compose logs monitor` (pasos 12 y 13) no mostraban nada, porque Python retenía la salida en buffer.
- `docker-compose.yml`: los puertos del host se pueden cambiar con `MQTT_HOST_PORT` y `DASHBOARD_HOST_PORT` (por defecto 1883 y 18083), por si Mosquitto de la Semana 08 sigue ocupando 1883. Está documentado en `.env.example` y en `docs/SOLUCION_PROBLEMAS.md`.
- `scripts/ci_prueba_laboratorio.sh`: prueba de integración que recorre las partes B, C, D, F y G del README. Usa su propio proyecto Compose (`semana10-ci`), así que no borra los datos del laboratorio del estudiante.

## Pipeline (`.github/workflows/ci.yml`)

Se ejecuta en cada push y pull request a `TA03` y `TA03-1`:

| Job | Qué hace |
|---|---|
| `lint` | Valida el HTML con html-validate y compila los scripts inline |
| `packet-tracer` | Descifra el `.pkt` y verifica router, DHCP, DNS, servidor IoT, clientes IoT y gateways; publica el resultado en el resumen del job |
| `e2e` | Playwright en Chromium (escritorio y Pixel 7): rótulo de simulación, sin errores ni scroll horizontal, generación de datos, handshake QoS 2, pausa, pico térmico y exportación CSV/JSON. Sube el reporte HTML como artefacto |
| `lab-semana10` | Compila `sensor_simulator.py` y `monitor.py`, valida el compose y ejecuta la prueba de integración con EMQX real: tres contenedores arriba, dashboard en 18083, PUBLISH y SUBSCRIBE, dos clientes en EMQX, CSV con columnas y rangos correctos, Last Will `offline` al detener el sensor y recuperación al reiniciarlo. Sube el log y el CSV como artefacto `semana10-evidencias` |
| `deploy` | Solo en push a `TA03` y con los tres jobs anteriores en verde: publica `index.html` y el `.pkt` en GitHub Pages |

## Créditos

El laboratorio de Packet Tracer parte de [Compusalle/Temperature-Control-System](https://github.com/Compusalle/Temperature-Control-System) (GPL-2.0, ver `packet-tracer/LICENSE`).
