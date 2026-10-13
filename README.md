# TA 03 · Sistema de control de temperatura IoT

Rama `TA03`. Tiene dos entregables:

1. **Laboratorio Packet Tracer** (`packet-tracer/Temperature_Control_System.pkt`): dos oficinas con sensores IoT conectadas por un ISP a un servidor IoT y a un servidor DNS.
2. **Simulador web** (`index.html`): página autocontenida que representa el pipeline MQTT → EMQX → Telegraf → InfluxDB → Grafana con datos generados en el navegador. Es una simulación: no hay broker, base de datos ni hardware reales.

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

## Pipeline (`.github/workflows/ci.yml`)

Se ejecuta en cada push y pull request a `TA03`:

| Job | Qué hace |
|---|---|
| `lint` | Valida el HTML con html-validate y compila los scripts inline |
| `packet-tracer` | Descifra el `.pkt` y verifica router, DHCP, DNS, servidor IoT, clientes IoT y gateways; publica el resultado en el resumen del job |
| `e2e` | Playwright en Chromium (escritorio y Pixel 7): rótulo de simulación, sin errores ni scroll horizontal, generación de datos, handshake QoS 2, pausa, pico térmico y exportación CSV/JSON. Sube el reporte HTML como artefacto |
| `deploy` | Solo en push a `TA03` y con los tres jobs anteriores en verde: publica `index.html` y el `.pkt` en GitHub Pages |

## Créditos

El laboratorio de Packet Tracer parte de [Compusalle/Temperature-Control-System](https://github.com/Compusalle/Temperature-Control-System) (GPL-2.0, ver `packet-tracer/LICENSE`).
