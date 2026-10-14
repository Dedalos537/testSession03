Write-Host "Deteniendo SOLO el nodo sensor..." -ForegroundColor Yellow
docker compose stop sensor
Write-Host "Revise EMQX Dashboard y el topic de estado."
