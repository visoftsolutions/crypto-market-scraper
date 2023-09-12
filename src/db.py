from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime


class InfluxDb:
    def __init__(self, org: str, token: str, url: str) -> None:
        self.org = org
        self.client = InfluxDBClient(url=url, token=token, org=org)

    def create_bucket_if_not_exist(self, bucket_name: str):
        buckets_api = self.client.buckets_api()
        bucket = buckets_api.find_bucket_by_name(bucket_name=bucket_name)
        if not bucket:
            return buckets_api.create_bucket(bucket_name=bucket_name, org=self.org)
        else:
            return bucket

    def write(
        self,
        bucket: str,
        measurement_name: str,
        tags: list[(str, str)],
        fields: list[(str, str)],
        datetime: datetime,
    ):
        # Write script
        write_api = self.client.write_api(write_options=SYNCHRONOUS)

        p = Point(measurement_name)
        for k, v in tags:
            p = p.tag(k, v)
        for k, v in fields:
            p = p.field(k, v)
        p = p.time(datetime)

        write_api.write(bucket=bucket, org=self.org, record=p)

    def get_last(self, bucket: str, measurement_name: str, symbol: str):
        query = f'from(bucket:"{bucket}")\
            |> range(start: 0)\
            |> filter(fn:(r) => r._measurement == "{measurement_name}")\
            |> filter(fn:(r) => r.symbol == "{symbol}")\
            |> last()'
        query_api = self.client.query_api()
        result = query_api.query(org=self.org, query=query)

        results = []
        for table in result:
            for record in table.records:
                results.append((record.get_field(), record.get_value()))
        return {k: v for k, v in results}

    def read(self, query: str):
        # Query script
        query_api = self.client.query_api()
        # query = f'from(bucket:"{bucket}")\
        # |> range(start: -10m)\
        # |> filter(fn:(r) => r._measurement == "my_measurement")\
        # |> filter(fn:(r) => r.location == "Prague")\
        # |> filter(fn:(r) => r._field == "temperature")'
        result = query_api.query(org=self.org, query=query)

        results = []
        for table in result:
            for record in table.records:
                results.append((record.get_field(), record.get_value()))

        return results
