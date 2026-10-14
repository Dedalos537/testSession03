Write-Host "ATENCIÓN: se eliminarán contenedores y volúmenes de EMQX." -ForegroundColor Red
docker compose down -v
Write-Host "Limpieza completada. El archivo data\telemetria.csv no se elimina automáticamente."
