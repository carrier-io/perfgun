import argparse
import requests
from perfreporter.downsampling import Downsampler
from os import environ


def get_args():
    parser = argparse.ArgumentParser(description='Simlog parser.')
    parser.add_argument("-t", "--type", help="Test type.")
    parser.add_argument("-s", "--simulation", help='Test simulation', default=None)
    parser.add_argument("-b", "--build_id", help="build ID", default=None)
    parser.add_argument("-en", "--env", help="Test type.", default=None)
    parser.add_argument("-i", "--influx_host", help='InfluxDB host or IP', default=None)
    parser.add_argument("-p", "--influx_port", help='InfluxDB port', default=8086)
    parser.add_argument("-iu", "--influx_user", help='InfluxDB user', default="")
    parser.add_argument("-ip", "--influx_password", help='InfluxDB password', default="")
    parser.add_argument("-idb", "--influx_db", help='Test results InfluxDB', default="jmeter")
    parser.add_argument("-l", "--lg_id", help='Load generator ID', default=None)
    return vars(parser.parse_args())

def update_test_status():
    headers = {'content-type': 'application/json', 'Authorization': f'bearer {environ.get("token")}'}
    url = f'{environ.get("galloper_url")}/api/v1/backend_performance/report_status/{environ.get("project_id")}/{environ.get("report_id")}'
    response = requests.get(url, headers=headers).json()
    if response["message"] == "In progress":
        data = {"test_status": {"status": "In progress", "percentage": 10,
                                "description": "Test started. Results will be updated every minute"}}
        response = requests.put(url, json=data, headers=headers)
        try:
            print(response.json()["message"])
        except:
            print(response.text)

if __name__ == '__main__':
    if environ.get("report_id"):
        update_test_status()
    args = get_args()
    Downsampler(args).run()
