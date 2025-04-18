# Polestar Exporter

A Prometheus exporter for Polestar vehicle data. This exporter collects metrics from the Polestar API and exposes them for Prometheus to scrape.

## Features

- Battery status monitoring (charge level, range, etc.)
- Vehicle information export
- Health metrics
- Odometer readings
- Charging status

## Running with Docker

### Build the Docker image

```bash
docker build -t polestar-exporter .
```

### Run the container

```bash
docker run -d \
  --name polestar-exporter \
  -p 9000:9000 \
  -e POLESTAR_USERNAME='your-polestar-username' \
  -e POLESTAR_PASSWORD='your-polestar-password' \
  -e POLESTAR_VIN='your-vehicle-vin' \
  polestar-exporter
```

### Optional environment variables

- `POLESTAR_PORT`: Port to expose metrics on (default: 9000)
- `POLESTAR_INTERVAL`: Scrape interval in seconds (default: 60)

Example with custom settings:

```bash
docker run -d \
  --name polestar-exporter \
  -p 9123:9123 \
  -e POLESTAR_USERNAME='your-polestar-username' \
  -e POLESTAR_PASSWORD='your-polestar-password' \
  -e POLESTAR_VIN='your-vehicle-vin' \
  -e POLESTAR_PORT=9123 \
  -e POLESTAR_INTERVAL=120 \
  polestar-exporter
```

## Prometheus Configuration

Add the following to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'polestar'
    static_configs:
      - targets: ['polestar-exporter:9000']
```

## Docker Compose Example

```yaml
version: '3'

services:
  polestar-exporter:
    build: .
    container_name: polestar-exporter
    ports:
      - "9000:9000"
    environment:
      - POLESTAR_USERNAME=your-polestar-username
      - POLESTAR_PASSWORD=your-polestar-password
      - POLESTAR_VIN=your-vehicle-vin
    restart: unless-stopped
```

## Available Metrics

The exporter provides numerous metrics including:

- `polestar_battery_charge_level_percentage`
- `polestar_estimated_range_km`
- `polestar_charging_power_watts`
- `polestar_odometer_km`
- And many more

Each metric is labeled with the vehicle's VIN, allowing monitoring of multiple vehicles from a single exporter instance.