# Solución de problemas

## Docker Desktop no inicia
Revise virtualización, WSL 2 y que Docker Desktop esté en ejecución.

## `docker compose` no se reconoce
Actualice Docker Desktop. Compose v2 se incluye con Docker Desktop.

## Puerto 1883 ocupado
En PowerShell:
```powershell
Get-NetTCPConnection -LocalPort 1883 -ErrorAction SilentlyContinue
```
Detenga Mosquitto u otro broker local antes de iniciar EMQX, o cambie el puerto del host sin editar `docker-compose.yml`:
```powershell
$env:MQTT_HOST_PORT="1884"; docker compose up -d
```
También puede definir `MQTT_HOST_PORT=1884` en su archivo `.env`. Los contenedores siguen usando 1883 internamente; solo cambia el puerto expuesto en su PC.

## Puerto 18083 ocupado
Compruebe:
```powershell
Get-NetTCPConnection -LocalPort 18083 -ErrorAction SilentlyContinue
```

## `sensor` o `monitor` no arranca
Revise:
```powershell
docker compose logs sensor
docker compose logs monitor
```

## EMQX no está saludable
Revise:
```powershell
docker compose logs emqx
docker compose ps
```

## No aparece `telemetria.csv`
Espere al menos 10–15 segundos y revise:
```powershell
docker compose logs monitor
```

## El Dashboard pide cambiar contraseña
Es el comportamiento esperado del primer inicio. Use las credenciales iniciales indicadas en el README y defina una contraseña nueva para el laboratorio.

## El sensor se detuvo intencionalmente
Para reiniciarlo:
```powershell
docker compose start sensor
```
