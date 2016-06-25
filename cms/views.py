from django.shortcuts import render, render_to_response
from django.template import RequestContext
from cms.models import Sensor, TimeTable
from django.db import connection
import datetime
import pandas as pd


def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
        ]


def fix_id(s):
    s = str(s)
    return s.strip()

global t
def add_bus_interval(d):
    for i in range(len(t)):
        if i < t.shape[0] - 1:
            start = t['dep_time'].ix[i]
            end = t['dep_time'].ix[i+1]

            if start <= d and end  >= d:
                return t['dep_time'].ix[i+1]
        else:
            return None


def add_comment(d):
    seat_ratio = d['count'] / d['seat_num']
    all_ratio = d['count'] / d['max_num']

    if seat_ratio < 1.0:
        return 1
    else:
        return 2


def top_page(request):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            *
        FROM
            sensor
        WHERE
            s_created_at::date = '2016-06-25' and s_ssid = '' and s_rssi <= -25 and s_rssi >= -90 and s_sensor_id = 1
    """)
    sensor = pd.DataFrame(list(dictfetchall(cursor)))
    timeTable = pd.DataFrame(list(TimeTable.objects.filter(dest='shonandai').values()))
    timeTable_all = pd.DataFrame(list(TimeTable.objects.all().values()))

    sensor['s_ssid'] = sensor['s_ssid'].apply(fix_id)
    sensor['s_mac_address'] = sensor['s_mac_address'].apply(fix_id)

    # Count Number of People each Bus Stops
    timeTable['dep_time'] = pd.to_datetime(timeTable['dep_time'])
    global t
    t = timeTable
    sensor['ride_bus'] = sensor['s_created_at'].apply(add_bus_interval)

    mobile_list = sensor.groupby(['s_mac_address', 'ride_bus']).count().reset_index()
    bus_count = mobile_list.groupby(['ride_bus']).count().reset_index()

    bus_count2 = bus_count[['ride_bus', 's_mac_address']]
    bus_count2.columns = ['dep_time', 'count']

    features = pd.merge(bus_count2, timeTable, left_on=['dep_time'], right_on=['dep_time'])
    # ADD Comment
    features['comment'] = features.apply(add_comment, axis=1)

    features['dep_time'] = features['dep_time'].astype(str)
    timeTable['dep_time'] = timeTable['dep_time'].astype(str)
    return render_to_response('bus_line/index.html',
                              {'result': features.to_json(orient='records'),
                               'timeTable': timeTable_all.to_json(orient='records')},
                              context_instance=RequestContext(request))
