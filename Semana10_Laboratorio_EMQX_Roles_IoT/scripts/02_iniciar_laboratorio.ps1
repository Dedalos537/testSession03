Write-Host "=== Iniciando laboratorio Semana 10 ===" -ForegroundColor Green
docker compose up -d --build
Write-Host "`nEstado:"
docker compose ps
Write-Host "`nDashboard EMQX: http://localhost:18083"
Write-Host "MQTT: localhost:1883"
