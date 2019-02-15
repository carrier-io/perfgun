import argparse
import csv
import re
import os
from time import time
import datetime
import numpy as np
from influxdb import InfluxDBClient


UNDEFINED = "undefined"

RESULTS_FOLDER = '/opt/gatling/results/'
SIMLOG_NAME = 'simulation.log'

FIELDNAMES = 'action', 'simulation', 'thread', "simulation_name", "request_name", \
             "request_start", "request_end", "status", "gatling_error", "error"


class SimulationLogParser(object):
    def __init__(self, arguments):
        self.args = arguments

    def parse_log(self):
        """Parse line with error and send to database"""
        simulation = self.args['simulation']
        path = self.find_log() if self.args['file'] is None else self.args['file']
        reqs = dict()
        test_time = time()
        test_start = time()
        test_end = 0
        user_count = 0
        try:
            client = InfluxDBClient(self.args["influx_host"], self.args['influx_port'], username='', password='',
                                    database=self.args['gatling_db'])
            raws = client.query("SELECT * FROM " + self.args['type'] + " WHERE simulation=\'" + simulation +
                                "\' and status='ok' and time >= " + str(self.args['start_time']) + "ms and time <= "
                                + str(self.args['end_time']) + "ms limit 1")
            for raw in list(raws.get_points()):
                user_count = int(raw['user_count'])
            client.close()
        except:
            print("Failed connection to " + self.args["influx_host"] + ", database - " + self.args['gatling_db'])
        build_id = "{}_{}_{}".format(self.args['type'], user_count,
                                     datetime.datetime.fromtimestamp(test_time).strftime('%Y-%m-%dT%H:%M:%SZ'))
        with open(path) as tsv:
            for entry in csv.DictReader(tsv, delimiter="\t", fieldnames=FIELDNAMES, restval="not_found"):
                if entry['action'] == "REQUEST":
                    try:
                        test_start = test_start if int(entry['request_start']) > test_start else int(
                            entry['request_start'])
                        test_end = test_end if int(entry['request_end']) < test_end else int(entry['request_end'])
                        data = self.parse_entry(entry)
                        data['simulation'] = simulation
                        data['user_count'] = user_count
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
                        reqs[key]['times'].append(data['response_time'])
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
                    "test_type": self.args["type"],
                    "build_id": build_id,
                    "request_name": reqs[req]['request_name'],
                    "method": reqs[req]['method'],
                    "duration": int(self.args['end_time'])/1000 - int(self.args['start_time'])/1000
                },
                "time": datetime.datetime.fromtimestamp(test_time).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields": {
                    "throughput": round(float(len(reqs[req]["times"])*1000)/float(test_end-test_start), 3),
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
                    "pct50": np.percentile(np_arr, 50, interpolation="higher"),
                    "pct75": np.percentile(np_arr, 75, interpolation="higher"),
                    "pct90": np.percentile(np_arr, 90, interpolation="higher"),
                    "pct95": np.percentile(np_arr, 95, interpolation="higher"),
                    "pct99": np.percentile(np_arr, 99, interpolation="higher")
                }

            }
            points.append(influx_record)
        try:
            client = InfluxDBClient(self.args["influx_host"], self.args['influx_port'],
                                username='', password='', database=self.args['comparison_db'])
            client.write_points(points)
            client.close()
        except:
            print("Failed connection to " + self.args["influx_host"] + ", database - comparison")

    @staticmethod
    def escape_for_json(string):
        if isinstance(string, str):
            return string.replace('"', '&quot;') \
                .replace("\\", "&#92;") \
                .replace("/", "&#47;") \
                .replace("<", "&lt;") \
                .replace(">", "&gt;")
        return string

    @staticmethod
    def extract_error_code(error_code):
        """Extract code of error from response body"""
        error_code_regex = re.search(r'("code"|"Code"): ?"?(-?\d+)"?,', error_code)
        if error_code_regex and error_code_regex.group(2):
            return error_code_regex.group(2)
        return UNDEFINED

    @staticmethod
    def remove_session_id(param):
        sessionid_regex = re.search(r'(SessionId|sessionID|sessionId|SessionID)=(.*?&|.*)', param)
        if sessionid_regex and sessionid_regex.group(2):
            return param.replace(sessionid_regex.group(2), '_...')
        return param

    @staticmethod
    def extract_response_code(error):
        """Extract response code"""
        code_regexp = re.search(r"HTTP Code: ?([a-zA-Z]*?\(?(\d+)\)?),", error)
        if code_regexp and code_regexp.group(2):
            return code_regexp.group(2)
        return UNDEFINED

    @staticmethod
    def find_log():
        """Walk file tree to find simulation log"""
        for d, dirs, files in os.walk(RESULTS_FOLDER):
            for f in files:
                if f == SIMLOG_NAME:
                    simlog_folder = os.path.basename(d)
                    return os.path.join(RESULTS_FOLDER, simlog_folder, SIMLOG_NAME)
        print("error no simlog")

    def parse_request(self, param):
        regex = re.search(r"Request: ?(.+?) ", param)
        if regex and regex.group(1):
            request_parts = regex.group(1).split("?")
            url = request_parts[0]
            params = request_parts[len(request_parts) - 1] if len(request_parts) >= 2 else ''
            url = self.escape_for_json(url)
            params = self.escape_for_json(params)
            method = re.search(r" ([A-Z]+) headers", param).group(1)
            return url, params, method
        return UNDEFINED, UNDEFINED, UNDEFINED

    def parse_entry(self, values):
        """Parse error entry"""
        values['test_type'] = self.args['type']
        values['response_time'] = int(values['request_end']) - int(values['request_start'])
        values['response_code'] = self.extract_response_code(values['error'])
        values['request_url'], _, values['request_method'] = self.parse_request(values['error'])
        return values


def parse_args():
    parser = argparse.ArgumentParser(description='Simlog parser.')
    parser.add_argument("-f", "--file", help="file path", default=None)
    parser.add_argument("-t", "--type", help="Test type.", default="test")
    parser.add_argument("-s", "--simulation", help='Test simulation', default=None)  # should be the same as on Grafana
    parser.add_argument("-st", "--start_time", help='Test start time', default=None)
    parser.add_argument("-et", "--end_time", help='Test end time', default=None)
    parser.add_argument("-i", "--influx_host", help='InfluxDB host or IP', default=None)
    parser.add_argument("-p", "--influx_port", help='InfluxDB port', default=None)
    parser.add_argument("-gdb", "--gatling_db", help='Gatling DB', default=None)
    parser.add_argument("-cdb", "--comparison_db", help='Comparison DB', default=None)
    return vars(parser.parse_args())


if __name__ == '__main__':
    print("Parsing simulation log")
    args = parse_args()
    if not str(args['file']).__contains__("//"):
        args['file'] = None
    logParser = SimulationLogParser(args)
    logParser.parse_log()
