#!/usr/bin/env python3
import asyncio
import time
import logging
import os
import traceback
from prometheus_client import start_http_server, Gauge, Info
from pypolestar import PolestarApi

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('polestar-exporter')

# Define metrics
# Car Information metrics
car_info = Info('polestar_vehicle_info', 'Vehicle information', ['vin'])
car_software_version = Info('polestar_software', 'Vehicle software information', ['vin'])
car_torque = Gauge('polestar_torque_nm', 'Vehicle torque in Nm', ['vin'])
car_battery_capacity = Gauge('polestar_battery_capacity_kwh', 'Battery capacity in kWh', ['vin'])
car_battery_voltage = Gauge('polestar_battery_voltage', 'Battery voltage', ['vin'])
car_battery_modules = Gauge('polestar_battery_modules', 'Number of battery modules', ['vin'])
car_battery_cells = Gauge('polestar_battery_cells', 'Number of battery cells', ['vin'])

# Battery metrics
battery_charge_level = Gauge('polestar_battery_charge_level_percentage', 'Battery charge level as a percentage', ['vin'])
battery_charging_power = Gauge('polestar_charging_power_watts', 'Current charging power in watts', ['vin'])
battery_charging_current = Gauge('polestar_charging_current_amps', 'Current charging current in amps', ['vin'])
battery_estimated_range = Gauge('polestar_estimated_range_km', 'Estimated range in kilometers', ['vin'])
battery_estimated_full_range = Gauge('polestar_estimated_full_range_km', 'Estimated range at 100% in kilometers', ['vin'])
battery_energy_consumption = Gauge('polestar_energy_consumption_kwh_per_100km', 'Average energy consumption in kWh/100km', ['vin'])
battery_charging_time_remaining = Gauge('polestar_charging_time_remaining_minutes', 'Estimated time to full charge in minutes', ['vin'])

# Odometer metrics
car_odometer = Gauge('polestar_odometer_km', 'Vehicle odometer in kilometers', ['vin'])
car_trip_auto = Gauge('polestar_trip_meter_automatic_km', 'Trip meter automatic in kilometers', ['vin'])
car_trip_manual = Gauge('polestar_trip_meter_manual_km', 'Trip meter manual in kilometers', ['vin'])
car_average_speed = Gauge('polestar_average_speed_kmh', 'Average speed in km/h', ['vin'])

# Health metrics
car_days_to_service = Gauge('polestar_days_to_service', 'Days remaining until next service', ['vin'])
car_distance_to_service = Gauge('polestar_distance_to_service_km', 'Distance remaining until next service in kilometers', ['vin'])

# Status info metrics
charging_status = Info('polestar_charging_status', 'Vehicle charging status information', ['vin'])
connection_status = Info('polestar_connection_status', 'Charger connection status', ['vin'])
health_warnings = Info('polestar_health_warnings', 'Health warnings from the vehicle', ['vin'])


async def update_metrics(api: PolestarApi, VIN: str):
    """Update all metrics with fresh data from the API."""
    try:
        await api.update_latest_data(vin=VIN, update_telematics=False)
        logger.error("UPDATED API DATA")
        # Get vehicle information
        car_info_data = api.get_car_information(VIN)
        logger.error(f"Retrieved car information for VIN {VIN}: {car_info_data}")
        if car_info_data:
            car_info.labels(VIN).info({
                'registration_no': car_info_data.registration_no or '',
                'model_name': car_info_data.model_name or '',
                'registration_date': str(car_info_data.registration_date or ''),
                'factory_complete_date': str(car_info_data.factory_complete_date or '')
            })
            
            if car_info_data.software_version:
                car_software_version.labels(VIN).info({
                    'version': car_info_data.software_version,
                    'update_timestamp': str(car_info_data.software_version_timestamp or '')
                })
                
            if car_info_data.torque_nm:
                car_torque.labels(VIN).set(car_info_data.torque_nm)
                
            if car_info_data.battery_information:
                if car_info_data.battery_information.capacity:
                    car_battery_capacity.labels(VIN).set(car_info_data.battery_information.capacity)
                if car_info_data.battery_information.voltage:
                    car_battery_voltage.labels(VIN).set(car_info_data.battery_information.voltage)
                if car_info_data.battery_information.modules:
                    car_battery_modules.labels(VIN).set(car_info_data.battery_information.modules)
                if car_info_data.battery_information.cells:
                    car_battery_cells.labels(VIN).set(car_info_data.battery_information.cells)

        logger.info("Metrics updated successfully")
        # Get telemetry data
        telemetry_data = api.get_car_telematics(VIN)
        if telemetry_data:
            # Battery data
            if telemetry_data.battery:
                if telemetry_data.battery.battery_charge_level_percentage is not None:
                    battery_charge_level.labels(VIN).set(telemetry_data.battery.battery_charge_level_percentage)
                    
                if telemetry_data.battery.charging_power_watts:
                    battery_charging_power.labels(VIN).set(telemetry_data.battery.charging_power_watts)
                    
                if telemetry_data.battery.charging_current_amps:
                    battery_charging_current.labels(VIN).set(telemetry_data.battery.charging_current_amps)
                    
                if telemetry_data.battery.estimated_distance_to_empty_km:
                    battery_estimated_range.labels(VIN).set(telemetry_data.battery.estimated_distance_to_empty_km)
                    
                if telemetry_data.battery.estimated_full_charge_range_km:
                    battery_estimated_full_range.labels(VIN).set(telemetry_data.battery.estimated_full_charge_range_km)
                    
                if telemetry_data.battery.average_energy_consumption_kwh_per_100km:
                    battery_energy_consumption.labels(VIN).set(telemetry_data.battery.average_energy_consumption_kwh_per_100km)
                    
                if telemetry_data.battery.estimated_charging_time_to_full_minutes:
                    battery_charging_time_remaining.labels(VIN).set(telemetry_data.battery.estimated_charging_time_to_full_minutes)
                    
                # Status information
                charging_status.labels(VIN).info({'status': str(telemetry_data.battery.charging_status)})
                connection_status.labels(VIN).info({'status': str(telemetry_data.battery.charger_connection_status)})
            
            # Odometer data
            if telemetry_data.odometer:
                if telemetry_data.odometer.odometer_meters is not None:
                    car_odometer.labels(VIN).set(telemetry_data.odometer.odometer_meters / 1000)  # Convert to kilometers
                    
                if telemetry_data.odometer.trip_meter_automatic_km is not None:
                    car_trip_auto.labels(VIN).set(telemetry_data.odometer.trip_meter_automatic_km)
                    
                if telemetry_data.odometer.trip_meter_manual_km is not None:
                    car_trip_manual.labels(VIN).set(telemetry_data.odometer.trip_meter_manual_km)
                    
                if telemetry_data.odometer.average_speed_km_per_hour is not None:
                    car_average_speed.labels(VIN).set(telemetry_data.odometer.average_speed_km_per_hour)
            
            # Health data
            if telemetry_data.health:
                if telemetry_data.health.days_to_service is not None:
                    car_days_to_service.labels(VIN).set(telemetry_data.health.days_to_service)
                    
                if telemetry_data.health.distance_to_service_km is not None:
                    car_distance_to_service.labels(VIN).set(telemetry_data.health.distance_to_service_km)
                    
                # Health warnings
                health_warnings.labels(VIN).info({
                    'brake_fluid': str(telemetry_data.health.brake_fluid_level_warning),
                    'engine_coolant': str(telemetry_data.health.engine_coolant_level_warning),
                    'oil_level': str(telemetry_data.health.oil_level_warning),
                    'service': str(telemetry_data.health.service_warning)
                })
                
        logger.info("Metrics updated successfully")
    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        logger.error(f"Exception details: {traceback.format_exc()}")


def main():
    # Get configuration from environment variables with defaults
    port = int(os.environ.get('POLESTAR_EXPORTER_PORT', '9000'))
    interval = int(os.environ.get('POLESTAR_EXPORTER_INTERVAL', '60'))
    username = os.environ.get('POLESTAR_EXPORTER_USERNAME')
    password = os.environ.get('POLESTAR_EXPORTER_PASSWORD')
    vin = os.environ.get('POLESTAR_EXPORTER_VIN')
    
    # Check for required environment variables
    if not all([username, password, vin]):
        logger.error("Missing required environment variables. Please set POLESTAR_USERNAME, POLESTAR_PASSWORD, and POLESTAR_VIN")
        exit(1)
    
    # Log configuration (without sensitive data)
    logger.info(f"Polestar exporter configured with: PORT={port}, INTERVAL={interval}, VIN={vin}")

    # Start Prometheus server
    start_http_server(port)
    logger.info(f"Polestar exporter server started on port {port}")

    # Initialize the API client with correct parameters
    api = PolestarApi(username=username, password=password, vins=[vin])
    
    # Create a new event loop for the entire application
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Initialize the API once outside the loop
        loop.run_until_complete(api.async_init())
        logger.info("API initialized successfully")
        
        # Main loop
        while True:
            try:
                # Create and run the task with timeout protection
                task = loop.create_task(update_metrics(api, vin))
                loop.run_until_complete(asyncio.wait_for(task, timeout=interval-1))
            except asyncio.TimeoutError:
                logger.warning("Update metrics operation timed out, continuing to next cycle")
            except Exception as e:
                logger.error(f"Error in update cycle: {e}")
                logger.error(f"Exception details: {traceback.format_exc()}")
            
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Exporter stopped by user")
    finally:
        # Cancel any pending tasks
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
            
        # Run the event loop until all tasks are cancelled
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
        # Close the loop when we're done
        loop.close()


if __name__ == "__main__":
    main()