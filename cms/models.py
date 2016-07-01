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
    id = models.AutoField(primary_key=True, auto_created=True)
    s_mac_address = models.CharField(max_length=255)
    s_ssid = models.CharField(max_length=255)
    s_created_at = models.DateTimeField()
    s_rssi = models.FloatField()
    s_sensor_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sensor'


class TimeTable(models.Model):
    id = models.BigIntegerField(db_column='index', primary_key=True)
    dest = models.CharField(max_length=255)
    dep_time = models.TimeField()
    type = models.CharField(max_length=255)
    field_max_num = models.BigIntegerField(db_column=' max_num', blank=True, null=True)  # Field renamed to remove unsuitable characters. Field renamed because it started with '_'.
    seat_num = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'timetable'