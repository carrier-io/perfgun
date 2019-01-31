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

INFLUX_HOST = "epuakhaw1400.kyiv.epam.com"
INFLUX_DATABASE = 'comparison'


class SimulationLogParser(object):
    def __init__(self, arguments):
        self.args = arguments

    def parse_log(self):
        """Parse line with error and send to database"""
        simulation = None
        path = self.find_log() if self.args['file'] is None else self.args['file']
        reqs = dict()
        test_time = time()
        build_id = "{}_{}_{}".format(self.args['type'], self.args['count'],
                                     datetime.datetime.fromtimestamp(test_time).strftime('%Y-%m-%dT%H:%M:%SZ'))
        test_start = time()
        test_end = 0
        with open(path) as tsv:
            for entry in csv.DictReader(tsv, delimiter="\t", fieldnames=FIELDNAMES, restval="not_found"):
                if simulation is None:
                    simulation = entry['simulation_name']
                if entry['action'] == "REQUEST":
                    try:
                        test_start = test_start if int(entry['request_start']) > test_start else int(
                            entry['request_start'])
                        test_end = test_end if int(entry['request_end']) < test_end else int(entry['request_end'])
                        data = self.parse_entry(entry)
                        data['simulation'] = simulation
                        data['environment'] = self.args['environment']
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
                    "users": self.args['count'],
                    "test_type": self.args["type"],
                    "build_id": build_id,
                    "request_name": reqs[req]['request_name'],
                    "method": reqs[req]['method'],
                    "duration": self.args['duration']
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
        client = InfluxDBClient(INFLUX_HOST, 8086, username='', password='', database=INFLUX_DATABASE)
        client.write_points(points)
        client.close()

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
        values['user_count'] = self.args['count']
        values['response_time'] = int(values['request_end']) - int(values['request_start'])
        values['response_code'] = self.extract_response_code(values['error'])
        values['request_url'], _, values['request_method'] = self.parse_request(values['error'])
        return values


def parse_args():
    parser = argparse.ArgumentParser(description='Simlog parser.')
    parser.add_argument("-f", "--file", help="file path", required=True, default=None)
    parser.add_argument("-c", "--count", type=int, required=True, help="User count.")
    parser.add_argument("-t", "--type", required=True, help="Test type.")
    parser.add_argument("-e", "--environment", help='Target environment', default=None)
    parser.add_argument("-d", "--duration", help='Test duration', default=None)
    parser.add_argument("-r", "--rumpup", help='Rump up time', default=None)
    parser.add_argument("-u", "--url", help='Environment url', default='')
    parser.add_argument("-s", "--simulation", help='Test simulation', default=None)  # should be the same as on Grafana
    parser.add_argument("-st", "--start_time", help='Test start time', default=None)
    parser.add_argument("-et", "--end_time", help='Test end time', default=None)
    return vars(parser.parse_args())


if __name__ == '__main__':
    print("Parsing simulation log")
    args = parse_args()

    logParser = SimulationLogParser(args)
    logParser.parse_log()
