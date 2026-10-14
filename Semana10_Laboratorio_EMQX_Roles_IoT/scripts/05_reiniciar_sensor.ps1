Write-Host "Reiniciando nodo sensor..." -ForegroundColor Green
docker compose start sensor
docker compose logs --tail=10 sensor
