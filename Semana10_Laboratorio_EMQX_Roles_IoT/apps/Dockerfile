FROM python:3.12-slim

WORKDIR /app

# Sin buffer: los print() aparecen al instante en `docker compose logs`.
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sensor_simulator.py monitor.py ./

CMD ["python", "sensor_simulator.py"]
