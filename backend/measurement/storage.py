"""Time-series storage for measurements."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from backend.core.config import settings
from backend.core.models.schemas import MeasurementData, S11Data
from backend.core.exceptions import MeasurementError

try:
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False


class MeasurementStorage:
    """Store measurements in time-series database (InfluxDB)."""
    
    def __init__(self):
        """Initialize storage client."""
        if not INFLUXDB_AVAILABLE:
            raise MeasurementError("InfluxDB client not available. Install influxdb-client.")
        
        self.client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.bucket = settings.INFLUXDB_BUCKET
    
    def store_measurement(self, measurement: MeasurementData) -> None:
        """
        Store measurement in InfluxDB.
        
        Args:
            measurement: MeasurementData to store
        """
        # Store S11 data as time series
        if measurement.s11:
            for freq, mag in zip(measurement.s11.frequency, measurement.s11.s11_magnitude):
                point = Point("s11_measurement") \
                    .tag("antenna_instance_id", measurement.antenna_instance_id) \
                    .tag("measurement_id", measurement.measurement_id) \
                    .field("frequency", freq) \
                    .field("s11_magnitude", mag) \
                    .time(measurement.timestamp)
                
                self.write_api.write(bucket=self.bucket, record=point)
        
        # Store scalar measurements
        point = Point("antenna_measurement") \
            .tag("antenna_instance_id", measurement.antenna_instance_id) \
            .tag("measurement_id", measurement.measurement_id) \
            .field("gain", measurement.gain) if measurement.gain else None
        
        if point:
            if measurement.efficiency:
                point = point.field("efficiency", measurement.efficiency)
            if measurement.temperature:
                point = point.field("temperature", measurement.temperature)
            if measurement.humidity:
                point = point.field("humidity", measurement.humidity)
            
            point = point.time(measurement.timestamp)
            self.write_api.write(bucket=self.bucket, record=point)
    
    def query_measurements(
        self,
        antenna_instance_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query measurements from InfluxDB.
        
        Args:
            antenna_instance_id: Antenna instance ID
            start_time: Start time for query
            end_time: End time for query
            limit: Maximum number of results
            
        Returns:
            List of measurement dictionaries
        """
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(days=30)
        if end_time is None:
            end_time = datetime.utcnow()
        
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
          |> filter(fn: (r) => r["_measurement"] == "antenna_measurement")
          |> filter(fn: (r) => r["antenna_instance_id"] == "{antenna_instance_id}")
          |> limit(n: {limit})
        '''
        
        result = self.query_api.query(query)
        
        measurements = []
        for table in result:
            for record in table.records:
                measurements.append({
                    "time": record.get_time(),
                    "field": record.get_field(),
                    "value": record.get_value(),
                    "antenna_instance_id": record.values.get("antenna_instance_id"),
                    "measurement_id": record.values.get("measurement_id")
                })
        
        return measurements
    
    def close(self):
        """Close InfluxDB client."""
        self.client.close()



















