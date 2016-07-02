from django.shortcuts import render, render_to_response
from cms.models import TimeTable
from django.http import HttpResponse, Http404
from django.db import connection
import pandas as pd


def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
        ]


def add_time(d):
    return d.time()


def fix_id(s):
    s = str(s)
    return s.strip()

global t
def add_bus_interval(d):
    for i in range(len(t)):
        if i < t.shape[0] - 1:
            start = t['dep_time'].ix[i].time()
            end = t['dep_time'].ix[i+1].time()

            if start <= d.time() and end  >= d.time():
                return t['dep_time'].ix[i+1]
        else:
            return None


def add_comment(d):
    seat_ratio = float(d['count']) / float(d['seat_num'])
    all_ratio = float(d['count']) / float(d['field_max_num'])
    if seat_ratio < 1.0:
        return 1
    elif seat_ratio > 1.0 and all_ratio < 1.0:
        return 2
    else:
        return 3


def remove_noize(d):
    if d['dest'] == 'tujido' and d['count'] is not None:
        return None
    else:
        return d['count']


def top_page(request):
    return render(request, 'bus_line/index.html')


def get_count(request):
    if request.method == 'GET':
        cursor = connection.cursor()
        cursor.execute("""
          SELECT * FROM timetable WHERE dep_time::time <= now()::time + interval '9 hour' and dest='shonandai' ORDER BY dep_time::time DESC LIMIT 1
        """)
        last_timetable = pd.DataFrame(list(dictfetchall(cursor)))['dep_time'][0]

        cursor = connection.cursor()
        cursor.execute("""
          SELECT * FROM timetable WHERE dep_time::time >= now()::time + interval '9 hour' and dest='shonandai' ORDER BY dep_time::time ASC LIMIT 1
        """)
        next_timetable = pd.DataFrame(list(dictfetchall(cursor)))['dep_time'][0]

        # Get the sensor data between last stop and now

        cursor.execute("""
          SELECT
            *,
            s_created_at::date || ' ' || extract('hour' from s_created_at) || ':' || extract('minute' from s_created_at) || ':'  || trunc(extract('seconds' from s_created_at)/10)*10 AS Interval
          FROM
            sensor
          WHERE
            s_created_at::date = '2016-07-02' and s_created_at::time <= '""" + next_timetable + """' and s_created_at::time >= '""" + last_timetable + """'::time and s_ssid = '' and s_rssi <= -25 and s_rssi >= -90 and s_sensor_id = 1
        """)
        sensor = pd.DataFrame(list(dictfetchall(cursor)))
        timeTable = pd.DataFrame(list(TimeTable.objects.filter(dest='shonandai').values()))

        # Get bus-stop timetable
        cursor = connection.cursor()
        cursor.execute("""
          SELECT * FROM timetable WHERE dep_time::time >= now()::time + interval '9 hour'ORDER BY dep_time::time DESC
        """)
        timeTable_all = pd.DataFrame(list(dictfetchall(cursor)))

        if sensor.shape[0] == 0:


            timeTable_all = timeTable_all.sort('dep_time').reset_index(drop=True)
            timeTable_all['count'] = None
            timeTable_all['count'].ix[0:1] = 0
            timeTable_all['comment'] = 1
            timeTable_all['count'] = timeTable_all.apply(remove_noize, axis=1)
            timeTable_all['dep_time'] = timeTable_all['dep_time'].astype(str)
            return HttpResponse(timeTable_all.to_json(orient='records'), content_type="application/json")
        # Fix dtypes
        sensor['s_ssid'] = sensor['s_ssid'].apply(fix_id)
        sensor['s_mac_address'] = sensor['s_mac_address'].apply(fix_id)

        # Filtering
        sensor_grp = sensor.groupby(['s_mac_address', 'interval']).count().reset_index()
        sensor_grp2 = sensor_grp[sensor_grp['s_ssid'] >= 2]
        sensor_grp2 = sensor_grp2[['s_mac_address', 'interval']]

        sensor = pd.merge(sensor, sensor_grp2, left_on=['s_mac_address', 'interval'], right_on=['s_mac_address', 'interval'], how='inner')
        # Count Number of People each Bus Stops
        timeTable['dep_time'] = pd.to_datetime(timeTable['dep_time'])
        global t
        t = timeTable
        sensor['ride_bus'] = sensor['s_created_at'].apply(add_bus_interval)

        mobile_list = sensor.groupby(['s_mac_address', 'ride_bus']).count().reset_index()
        bus_count = mobile_list.groupby(['ride_bus']).count().reset_index()

        bus_count2 = bus_count[['ride_bus', 's_mac_address']]
        bus_count2.columns = ['dep_time', 'count']

        timeTable_all['dep_time'] = timeTable_all['dep_time'].astype(str)
        timeTable_all.columns = ['max_num', 'time', 'dest', 'index', 'seat_num', 'type']

        features = pd.merge(bus_count2, timeTable, left_on=['dep_time'], right_on=['dep_time'])
        features['time'] = features['dep_time'].apply(add_time)
        print(features)

        features['comment'] = features.apply(add_comment, axis=1)

        # For Merge
        features['time'] = features['time'].astype(str)
        timeTable_all['time'] = timeTable_all['time'].astype(str)
        features2 = pd.merge(features, timeTable_all, left_on=['time'], right_on=['time'], how='right')

        # Reforming Data Set
        features3 = features2[['time', 'dest_y', 'count', 'type_y', 'max_num', 'seat_num_y', 'comment']]
        features3.columns = ['dep_time', 'dest', 'count', 'type', 'max_num', 'seat_num', 'comment']
        features3['dep_time'] = features3['dep_time'].astype(str)
        features3 = features3.sort(['dep_time']).reset_index(drop=True)

        # Check Noise
        features3['count'] = features3.apply(remove_noize, axis=1)

        return HttpResponse(features3.to_json(orient='records'), content_type="application/json")
    else:
        return Http404


def get_timetable(request):
    # Get bus-stop timetable
    cursor = connection.cursor()
    cursor.execute("""
    SELECT * FROM timetable WHERE dep_time::time >= now()::time + interval '9 hour'ORDER BY dep_time::time DESC
    """)
    timeTable_all = pd.DataFrame(list(dictfetchall(cursor)))
    timeTable_all['dep_time'] = timeTable_all['dep_time'].astype(str)
    timeTable_all.columns = ['max_num', 'dep_time', 'dest', 'index', 'seat_num', 'type']

    return HttpResponse(timeTable_all.to_json(orient='records'), content_type="application/json")
