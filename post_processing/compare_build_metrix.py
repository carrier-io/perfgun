import argparse
import csv
import re
import os
from time import time
import datetime
import numpy as np
from influxdb import InfluxDBClient


UNDEFINED = "undefined"

PATH = '/opt/gatling/bin/logs/comparison.log'

FIELDNAMES = "request_name", "response_time", "method", "url", "status", "status_code"


class SimulationLogParser(object):
    def __init__(self, arguments):
        self.args = arguments

    def parse_log(self):
        simulation = self.args['simulation']
        test_type = self.args['type']
        reqs = dict()
        timestamp = time()
        user_count = 0 if self.args['users'] is None else self.args['users']
        build_id = args['build_id']
        with open(PATH, 'r+', encoding="utf-8") as tsv:
            for entry in csv.DictReader(tsv, delimiter="\t", fieldnames=FIELDNAMES, restval="not_found"):
                try:
                    data = {'simulation': simulation, 'test_type': test_type, 'user_count': user_count,
                            'request_name': entry['request_name'], 'response_time': entry['response_time'],
                            'status': entry['status'], 'response_code': entry['status_code'],
                            'request_url': entry['url'], 'request_method': entry['method']}
                    key = '{} {}'.format(data["request_method"].upper(), data["request_name"])
                    if key not in reqs:
                        reqs[key] = {
                            "times": [],
                            "KO": 0,
                            "OK": 0,
                            "1xx": 0,
                            "2xx": 0,
                            "3xx": 0,
                            "4xx": 0,
                            "5xx": 0,
                            'NaN': 0,
                            "method": data["request_method"].upper(),
                            "request_name": data['request_name']
                        }
                    reqs[key]['times'].append(int(data['response_time']))
                    if "{}xx".format(str(data['response_code'])[0]) in reqs[key]:
                        reqs[key]["{}xx".format(str(data['response_code'])[0])] += 1
                    else:
                        reqs[key]["NaN"] += 1
                    reqs[key][data['status']] += 1
                except:
                    pass

        if not reqs:
            exit(0)
        points = []
        for req in reqs:
            np_arr = np.array(reqs[req]["times"])
            influx_record = {
                "measurement": "api_comparison",
                "tags": {
                    "simulation": simulation,
                    "users": user_count,
                    "test_type": test_type,
                    "build_id": build_id,
                    "request_name": reqs[req]['request_name'],
                    "method": reqs[req]['method'],
                    "duration": int(self.args['end_time'])/1000 - int(self.args['start_time'])/1000
                },
                "time": datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields": {
                    "throughput": round(float(len(reqs[req]["times"])*1000)/float(int(self.args['end_time'])-int(self.args['start_time'])), 3),
                    "total": len(reqs[req]["times"]),
                    "ok": reqs[req]["OK"],
                    "ko": reqs[req]["KO"],
                    "1xx": reqs[req]["1xx"],
                    "2xx": reqs[req]["2xx"],
                    "3xx": reqs[req]["3xx"],
                    "4xx": reqs[req]["4xx"],
                    "5xx": reqs[req]["5xx"],
                    "NaN": reqs[req]["NaN"],
                    "min": round(np_arr.min(), 2),
                    "max": round(np_arr.max(), 2),
                    "mean": round(np_arr.mean(), 2),
                    "pct50": int(np.percentile(np_arr, 50, interpolation="linear")),
                    "pct75": int(np.percentile(np_arr, 75, interpolation="linear")),
                    "pct90": int(np.percentile(np_arr, 90, interpolation="linear")),
                    "pct95": int(np.percentile(np_arr, 95, interpolation="linear")),
                    "pct99": int(np.percentile(np_arr, 99, interpolation="linear"))
                }
            }
            points.append(influx_record)
        try:
            client = InfluxDBClient(self.args["influx_host"], self.args['influx_port'],
                                    username='', password='', database=self.args['comparison_db'])
            client.write_points(points)
            client.close()
        except Exception as e:
            print(e)
            print("Failed connection to " + self.args["influx_host"] + ", database - comparison")


def parse_args():
    parser = argparse.ArgumentParser(description='Simlog parser.')
    parser.add_argument("-b", "--build_id", help="build ID", default=None)
    parser.add_argument("-l", "--lg_id", help="load generator ID", default=None)
    parser.add_argument("-t", "--type", help="Test type.", default="test")
    parser.add_argument("-s", "--simulation", help='Test simulation', default=None)  # should be the same as on Grafana
    parser.add_argument("-st", "--start_time", help='Test start time', default=None)
    parser.add_argument("-et", "--end_time", help='Test end time', default=None)
    parser.add_argument("-u", "--users", help='Users count', default=None)
    parser.add_argument("-i", "--influx_host", help='InfluxDB host or IP', default=None)
    parser.add_argument("-p", "--influx_port", help='InfluxDB port', default=None)
    parser.add_argument("-gdb", "--gatling_db", help='Gatling DB', default=None)
    parser.add_argument("-cdb", "--comparison_db", help='Comparison DB', default=None)
    return vars(parser.parse_args())


if __name__ == '__main__':
    args = parse_args()
    logParser = SimulationLogParser(args)
    logParser.parse_log()
