Write-Host "=== Logs del sensor ===" -ForegroundColor Cyan
docker compose logs --tail=20 sensor
Write-Host "`n=== Logs del monitor ===" -ForegroundColor Cyan
docker compose logs --tail=20 monitor
