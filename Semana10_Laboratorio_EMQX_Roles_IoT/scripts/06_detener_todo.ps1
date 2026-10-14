Write-Host "Deteniendo laboratorio..." -ForegroundColor Yellow
docker compose down
Write-Host "Se conservarán los volúmenes de EMQX y el CSV local."
