from __future__ import unicode_literals
from django.db import models


class Result(models.Model):
    id = models.BigIntegerField(db_column='index', primary_key=True)
    dep_time = models.TextField(blank=True, null=True)
    date = models.TextField(blank=True, null=True)
    num_people = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'result'


class Sensor(models.Model):
    s_mac_address = models.CharField(max_length=255)
    s_ssid = models.CharField(max_length=255)
    s_created_at = models.DateTimeField()
    s_rssi = models.FloatField()
    s_sensor_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sensor'
