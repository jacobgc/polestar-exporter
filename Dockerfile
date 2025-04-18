FROM python:3.13.3-alpine3.21

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY polestar-exporter/ .

# Environment variables with defaults
ENV POLESTAR_EXPORTER_PORT=9000
ENV POLESTAR_EXPORTER_INTERVAL=60
# Required environment variables (to be provided at runtime):
# ENV POLESTAR_EXPORTER_USERNAME=your-username
# ENV POLESTAR_EXPORTER_PASSWORD=your-password
# ENV POLESTAR_EXPORTER_VIN=your-vehicle-vin

# Expose the metrics port
EXPOSE ${POLESTAR_PORT}

# Run the exporter
CMD ["python", "polestar-exporter.py"]