from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime


class InfluxDb:
    def __init__(
        self,
        org: str,
        token: str,
        url: str,
        bucket_name: str,
        measurement_name: str,
        tags: list[(str, str)],
    ) -> None:
        self.org = org
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.bucket_name = bucket_name
        self.measurement_name = measurement_name
        self.tags = tags
        self.query_api = self.client.query_api()
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.create_bucket_if_not_exist()

    def create_bucket_if_not_exist(self):
        buckets_api = self.client.buckets_api()
        bucket = buckets_api.find_bucket_by_name(bucket_name=self.bucket_name)
        if not bucket:
            return buckets_api.create_bucket(bucket_name=self.bucket_name, org=self.org)
        else:
            return bucket

    def write(
        self,
        fields: list[(str, str)],
        datetime: datetime,
    ):
        p = Point(self.measurement_name)
        for k, v in self.tags:
            p = p.tag(k, v)
        for k, v in fields:
            p = p.field(k, v)
        p = p.time(datetime)
        self.write_api.write(bucket=self.bucket_name, org=self.org, record=p)

    def get_last(self):
        query = "\n|> ".join(
            [
                f'from(bucket:"{self.bucket_name}")',
                "range(start: 0)",
                f'filter(fn:(r) => r._measurement == "{self.measurement_name}")',
                *[f'filter(fn:(r) => r.{k} == "{v}")' for k, v in self.tags],
                "last()",
            ]
        )
        result = self.query_api.query(org=self.org, query=query)

        results = []
        for table in result:
            for record in table.records:
                results.append((record.get_field(), record.get_value()))
        return {k: v for k, v in results}
