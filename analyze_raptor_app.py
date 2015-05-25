from influxdb.influxdb08 import InfluxDBClient
from analyze import PerfDatum, TalosAnalyzer
import datetime
import sys

if len(sys.argv) != 5:
    print "USAGE: %s <host> <username> <password> <appName>" % sys.argv[0]
    print "APPNAME: E-Mail, Video, Phone, Settings, FM-Radio, Clock, Camera, Music, Messages, Contacts, Gallery"
    sys.exit(1)

(host, username, password, appName) = sys.argv[1:]

if appName == 'E-Mail':
    contextString = 'email.gaiamobile.org'
elif appName == 'Phone':
    contextString = 'communications.gaiamobile.org'
elif appName == 'FM-Radio':
    appName = 'FM Radio'
    contextString = 'fm.gaiamobile.org'
elif appName == 'Messages':
    contextString = 'sms.gaiamobile.org'
elif appName == 'Contacts':
    contextString = 'communications.gaiamobile.org'
else:
    contextString = appName + '.gaiamobile.org'
    contextString = contextString.lower()

client = InfluxDBClient(host, 8086, username, password, 'raptor')
clocknumbers = client.query("select time, sequence_number, value from coldlaunch.visuallyLoaded where appName = '%s' and context = '%s' and device='flame-kk' and branch='v2.2' and memory='319' and time > now() - 4w;" % (appName, contextString))
revinfo = client.query("select time, sequence_number, text from events where device='flame-kk' and branch='v2.2' and memory='319' and time > now() - 4w;")
sequence_rev_map = {}
for (timestamp, sequence_number, text) in revinfo[0]['points']:
    sequence_rev_map[timestamp] = text
perf_data = []
prev_timestamp = None
values = []
for (timestamp, sequence_number, value) in clocknumbers[0]['points']:
    if prev_timestamp and prev_timestamp == timestamp:
       values.append(value)
    elif prev_timestamp:
        # add everything to perf data
        avg = float(sum(values))/len(values)
        perf_data.append(PerfDatum(prev_timestamp, 0, prev_timestamp, avg,
                                   None, prev_timestamp))
        # start again
        values = [ value ]
        prev_timestamp = timestamp
    else:
        # first value
        prev_timestamp = timestamp
        values = [ value ]

ta = TalosAnalyzer()
ta.addData(perf_data)
for r in ta.analyze_t(5, 5, 3):
  #  if r.state == 'regression':
        if sequence_rev_map.get(r.timestamp):
            print "date: %s" % datetime.datetime.fromtimestamp(
                r.timestamp).strftime('%Y-%m-%d %H:%M:%S')
            print "confidence (higher is more confident): %s" % r.t
            print "revision: %s" % sequence_rev_map[r.timestamp]
            print "old average: %s" % r.historical_stats['avg']
            print "new average: %s" % r.forward_stats['avg']
            print "================================="
