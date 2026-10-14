# Semana 10 — Laboratorio integrador: MQTT + EMQX + roles profesionales IoT

Curso: **Herramientas de Desarrollo Profesional - TIC**  
Unidad 3: **Internet de las Cosas (IoT)**  
Sesión 03: **Certificaciones y roles laborales en IoT**

---

## 1. Propósito

Este laboratorio retoma el flujo técnico trabajado en las semanas anteriores y lo utiliza para comprender **qué profesional interviene en cada capa de una solución IoT**.

Se implementará un entorno **100 % virtual**:

```text
SENSOR VIRTUAL
Python
    |
    | publica JSON por MQTT
    v
EMQX
Broker MQTT en Docker
    |
    +----------------------+
    |                      |
    v                      v
MONITOR                 DASHBOARD EMQX
Python                  localhost:18083
    |
    v
telemetria.csv
```

Al finalizar, el estudiante deberá poder relacionar:

```text
componente técnico
        ↓
capa IoT
        ↓
responsabilidad
        ↓
rol profesional
        ↓
habilidad
        ↓
ruta formativa / certificación
```

---

# 2. Qué aprenderás

- Levantar un broker MQTT local con Docker.
- Utilizar EMQX como plataforma de mensajería IoT.
- Publicar telemetría simulada cada 5 segundos.
- Suscribirte a topics MQTT.
- Monitorear clientes y conexiones desde EMQX Dashboard.
- Persistir mensajes en CSV.
- Simular una falla del nodo y observar su impacto.
- Relacionar cada componente con un rol profesional IoT.
- Elaborar un roadmap profesional personal.

---

# 3. Requisitos

Necesitas únicamente:

- Windows 10/11.
- Docker Desktop funcionando.
- Navegador web.
- PowerShell.
- Aproximadamente 1 GB libre para imágenes y datos del laboratorio.

No necesitas:

- ESP32 físico.
- Sensores físicos.
- Mosquitto instalado.
- Python instalado localmente.
- Node-RED.
- Cuenta cloud.

Todo el entorno de ejecución se levanta con Docker.

---

# 4. Estructura

```text
Semana10_Laboratorio_EMQX_Roles_IoT/
│
├── docker-compose.yml
├── .env.example
├── README.md
│
├── apps/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── sensor_simulator.py
│   └── monitor.py
│
├── data/
│   └── telemetria.csv        ← se genera automáticamente
│
├── docs/
│   ├── MAPA_ROLES.md
│   ├── PLANTILLA_ROADMAP_PROFESIONAL.md
│   ├── EVIDENCIAS.md
│   └── SOLUCION_PROBLEMAS.md
│
└── scripts/
    ├── 01_verificar_docker.ps1
    ├── 02_iniciar_laboratorio.ps1
    ├── 03_ver_logs.ps1
    ├── 04_detener_sensor.ps1
    ├── 05_reiniciar_sensor.ps1
    ├── 06_detener_todo.ps1
    └── 07_limpiar_total.ps1
```

---

# PARTE A — PREPARACIÓN

## 5. Descomprimir el proyecto

Descomprima el ZIP en una ruta sencilla, por ejemplo:

```text
C:\UTP\Semana10_Laboratorio_EMQX_Roles_IoT
```

Evite ejecutar el proyecto directamente dentro del ZIP.

---

## 6. Abrir PowerShell en la carpeta

Ejemplo:

```powershell
cd "C:\UTP\Semana10_Laboratorio_EMQX_Roles_IoT"
```

Compruebe:

```powershell
dir
```

Debe aparecer:

```text
docker-compose.yml
README.md
apps
data
docs
scripts
```

---

## 7. Verificar Docker

```powershell
docker --version
docker compose version
docker info
```

Si `docker info` muestra error de conexión, abra Docker Desktop y espere a que el motor termine de iniciar.

También puede usar:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\01_verificar_docker.ps1
```

---

# PARTE B — LEVANTAR LA ARQUITECTURA

## 8. Iniciar todo el laboratorio

Desde la carpeta raíz:

```powershell
docker compose up -d --build
```

La primera ejecución descargará la imagen de EMQX y la imagen base de Python. Puede tardar algunos minutos.

Compruebe:

```powershell
docker compose ps
```

Debe observar tres servicios:

```text
semana10-emqx
semana10-sensor
semana10-monitor
```

También puede ejecutar:

```powershell
.\scripts\02_iniciar_laboratorio.ps1
```

---

## 9. Qué hace cada contenedor

### `semana10-emqx`
Broker MQTT local.

Puertos principales:

```text
1883  → MQTT TCP
18083 → Dashboard web
```

### `semana10-sensor`
Nodo IoT simulado.

Cada 5 segundos publica:

- temperatura;
- humedad;
- batería;
- fecha;
- identificador de equipo;
- identificador de dispositivo.

### `semana10-monitor`
Cliente suscriptor.

Escucha los mensajes, los muestra en consola y guarda un histórico CSV.

---

# PARTE C — EMQX DASHBOARD

## 10. Abrir EMQX

Abra:

```text
http://localhost:18083
```

En una instalación nueva, las credenciales iniciales habituales del Dashboard son:

```text
Usuario: admin
Contraseña: public
```

El Dashboard puede solicitar que cambie la contraseña en el primer ingreso. Use una contraseña de laboratorio que pueda recordar.

> Estas credenciales corresponden al Dashboard de administración, no a usuarios MQTT de producción.

---

## 11. Qué observar en EMQX

Busque en el Dashboard:

- estado del nodo EMQX;
- conexiones;
- clientes;
- suscripciones;
- métricas;
- mensajes publicados.

Debe aparecer el nodo sensor y el cliente monitor.

No es necesario modificar configuraciones avanzadas para completar esta práctica.

---

# PARTE D — TELEMETRÍA

## 12. Ver publicaciones del sensor

PowerShell:

```powershell
docker compose logs -f sensor
```

Debe observar mensajes similares a:

```text
[PUB] iot/utp/semana10/equipo01/telemetria {
  "equipo": "equipo01",
  "dispositivo": "esp32-virtual-01",
  "temperatura_c": 25.8,
  "humedad_pct": 61.2,
  "bateria_pct": 89.7,
  ...
}
```

Detenga la vista de logs con:

```text
Ctrl + C
```

El contenedor NO se detiene; solo sale de la visualización de logs.

---

## 13. Ver el suscriptor

```powershell
docker compose logs -f monitor
```

Debe aparecer:

```text
[SUB] iot/utp/semana10/+/+
[MSG] iot/utp/semana10/equipo01/telemetria -> {...}
```

Aquí se observa el patrón **publish/subscribe** de MQTT.

---

# PARTE E — TOPICS Y QoS

## 14. Topics utilizados

Para el equipo `equipo01`:

```text
iot/utp/semana10/equipo01/telemetria
iot/utp/semana10/equipo01/estado
```

El monitor utiliza:

```text
iot/utp/semana10/+/+
```

El símbolo:

```text
+
```

es un comodín MQTT de un nivel.

Así, el monitor podría recibir mensajes de varios equipos.

---

## 15. QoS utilizado

El laboratorio utiliza:

```text
QoS 1
```

Significa:

> el mensaje se entrega al menos una vez.

Pregunta de análisis:

```text
¿Qué beneficio y qué posible costo tiene usar QoS 1?
```

---

# PARTE F — HISTÓRICO

## 16. Revisar el CSV

Después de unos segundos aparecerá:

```text
data\telemetria.csv
```

Puede abrirlo con Excel o con:

```powershell
Get-Content .\data\telemetria.csv
```

Columnas:

```text
recibido_en
topic
equipo
dispositivo
temperatura_c
humedad_pct
bateria_pct
estado
fecha_origen
```

Aquí la mensajería se transforma en información que posteriormente podría usar un dashboard o un sistema analítico.

---

# PARTE G — SIMULAR UNA FALLA

## 17. Detener solo el nodo IoT

Ejecute:

```powershell
docker compose stop sensor
```

o:

```powershell
.\scripts\04_detener_sensor.ps1
```

Ahora vuelva a EMQX Dashboard.

Observe:

- disminución de clientes conectados;
- cese de nuevas publicaciones de telemetría;
- estado del dispositivo.

El sensor configuró un **Last Will** MQTT para publicar `offline` si pierde la conexión inesperadamente.

---

## 18. Reiniciar el nodo

```powershell
docker compose start sensor
```

o:

```powershell
.\scripts\05_reiniciar_sensor.ps1
```

Observe nuevamente:

```powershell
docker compose logs -f sensor
```

La publicación debe reanudarse.

---

# PARTE H — RELACIONAR EL SISTEMA CON ROLES IoT

## 19. Abrir el mapa

Revise:

```text
docs\MAPA_ROLES.md
```

Relacione:

```text
sensor_simulator.py
        ↓
Percepción / Nodo
        ↓
Embedded Device Engineer
```

```text
MQTT
        ↓
Conectividad / Red
        ↓
IoT Network & Connectivity Engineer
```

```text
Docker / servicio local
        ↓
Edge
        ↓
Edge Computing Developer
```

```text
EMQX
        ↓
Plataforma
        ↓
IoT Platform / Cloud Engineer
```

```text
monitor.py + CSV
        ↓
Aplicación / Analítica
        ↓
IoT Application / Data Engineer
```

```text
autenticación + TLS + permisos
        ↓
Seguridad transversal
        ↓
IoT Security Engineer
```

> El broker se ejecuta localmente. Por tanto, este proyecto **simula** la capa de plataforma; no constituye un despliegue cloud real.

---

# PARTE I — ANÁLISIS PROFESIONAL

## 20. Caso de trabajo

Imagine que esta arquitectura deja de tener:

```text
1 sensor
```

y pasa a:

```text
10 000 sensores
```

distribuidos en distintas ciudades.

Cada equipo debe responder:

1. ¿Qué componente tendría problemas primero?
2. ¿Qué profesional debería intervenir?
3. ¿Qué nuevas habilidades serían necesarias?
4. ¿Qué riesgos de seguridad aparecerían?
5. ¿Qué componente moverías a cloud?
6. ¿Qué datos conservarías en edge?
7. ¿Qué métrica utilizarías para comprobar la calidad de la red?

---

# PARTE J — ROADMAP PROFESIONAL

## 21. Construir el roadmap

Abra:

```text
docs\PLANTILLA_ROADMAP_PROFESIONAL.md
```

Cada estudiante selecciona un rol:

```text
Embedded Device Engineer
IoT Network & Connectivity Engineer
Edge Computing Developer
IoT Platform / Cloud Engineer
IoT Application / Data Engineer
IoT Security Engineer
```

Y completa:

```text
ROL OBJETIVO
      ↓
RESPONSABILIDADES
      ↓
HABILIDADES ACTUALES
      ↓
BRECHAS
      ↓
FORMACIÓN / CERTIFICACIÓN
      ↓
PROYECTO DE PORTAFOLIO
      ↓
PLAN 30-60-90 DÍAS
```

Antes de colocar una certificación en el roadmap, verifique su vigencia en el sitio oficial del proveedor.

---

# PARTE K — SEGURIDAD

## 22. ¿Qué falta para producción?

El laboratorio prioriza comprensión y facilidad de ejecución.

Una arquitectura real debería agregar:

- autenticación de clientes MQTT;
- autorización por topics;
- TLS;
- certificados de dispositivo;
- rotación de credenciales;
- segmentación de red;
- actualización segura;
- auditoría;
- monitoreo;
- gestión de vulnerabilidades.

Actividad:

```text
Identifique tres controles que implementaría primero y justifique el orden.
```

---

# PARTE L — EVIDENCIAS

## 23. Evidencias

Consulte:

```text
docs\EVIDENCIAS.md
```

Como mínimo:

1. `docker compose ps`.
2. Dashboard EMQX.
3. Clientes conectados.
4. Logs del sensor.
5. Logs del monitor.
6. `telemetria.csv`.
7. Prueba de falla y recuperación.
8. Mapa capa → componente → rol.
9. Roadmap profesional.
10. Reflexión final.

---

# PARTE M — FINALIZACIÓN

## 24. Detener el laboratorio

```powershell
docker compose down
```

Esto elimina los contenedores pero conserva:

- volúmenes de EMQX;
- `data\telemetria.csv`.

También puede usar:

```powershell
.\scripts\06_detener_todo.ps1
```

---

## 25. Reiniciar otro día

Simplemente:

```powershell
docker compose up -d
```

Si modificó código:

```powershell
docker compose up -d --build
```

---

## 26. Borrar también los datos de EMQX

Solo si desea empezar completamente desde cero:

```powershell
docker compose down -v
```

o:

```powershell
.\scripts\07_limpiar_total.ps1
```

El CSV local no se borra automáticamente.

---

# 27. Solución de problemas

Consulte:

```text
docs\SOLUCION_PROBLEMAS.md
```

Problemas cubiertos:

- Docker no inicia.
- Compose no existe.
- puerto 1883 ocupado;
- puerto 18083 ocupado;
- EMQX no saludable;
- cliente sensor detenido;
- monitor sin datos;
- CSV no generado.

---

# 28. Relación con las semanas anteriores

```text
SEMANA 08
Node-RED + Mosquitto
Fundamentos y arquitectura

        ↓

SEMANA 09
ESP32/DHT22 virtual
Del sensor al dato

        ↓

SEMANA 10
EMQX + Docker + roles
Del sistema técnico al perfil profesional
```

La Semana 10 no pretende repetir solamente MQTT: utiliza una arquitectura funcional para analizar quién diseña, opera, asegura y escala cada capa.

---

# 29. Tarea Académica 3

**[Información pendiente de confirmar]**

La programación del curso contempla **Tarea Académica 3**, pero este proyecto no inventa su consigna, ponderación, formato ni rúbrica.

Cuando la consigna oficial esté disponible, debe incorporarse como documento separado o reemplazar esta sección.

---

# 30. Checklist

- [ ] Docker Desktop está funcionando.
- [ ] `docker compose up -d --build` termina correctamente.
- [ ] EMQX abre en `localhost:18083`.
- [ ] Sensor publica cada 5 segundos.
- [ ] Monitor recibe mensajes.
- [ ] CSV contiene datos.
- [ ] Se identifica el topic de telemetría.
- [ ] Se comprende QoS 1.
- [ ] Se ejecutó la prueba de falla.
- [ ] Se relacionaron componentes con roles.
- [ ] Se completó el roadmap profesional.
- [ ] Se recopilaron evidencias.

---

## Resultado final esperado

El estudiante no solo debe poder decir:

> “MQTT sirve para enviar mensajes”.

Debe poder explicar:

> qué componente genera el dato, cómo se transporta, quién opera el broker, quién consume los datos, qué controles de seguridad faltan y qué rol profesional se responsabiliza de cada parte.
