import argparse
import json
import requests
from os import environ
import shutil
from perfreporter.post_processor import PostProcessor
from perfreporter.error_parser import ErrorLogParser
from os import environ


RESULTS_FOLDER = '/opt/gatling/results/'

DATA_FOR_POST_PROCESSING_FOLDER = "/tmp/data_for_post_processing/"


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
    parser.add_argument("-cm", "--comparison_metric", help='Comparison metric', default="pct95")
    parser.add_argument("-idb", "--influx_db", help='Comparison InfluxDB', default="gatling")
    parser.add_argument("-icdb", "--comparison_db", help='Comparison InfluxDB', default="comparison")
    parser.add_argument("-itdb", "--thresholds_db", help='Thresholds InfluxDB', default="thresholds")
    parser.add_argument("-tl", "--test_limit", help='test_limit', default=5)
    parser.add_argument("-l", "--lg_id", help='Load generator ID', default=None)
    parser.add_argument("-el", "--error_logs", help='Path to the error logs', default='/tmp/')
    parser.add_argument("-trl", "--test_results_log", help='Path to the test results log',
                        default='/opt/gatling/bin/logs/test_results.log')
    return vars(parser.parse_args())


def update_test_status():
    headers = {'content-type': 'application/json', 'Authorization': f'bearer {environ.get("token")}'}
    url = f'{environ.get("galloper_url")}/api/v1/backend_performance/report_status/{environ.get("project_id")}/{environ.get("report_id")}'
    response = requests.get(url, headers=headers).json()
    if response["message"] == "In progress":
        data = {"test_status": {"status": "Post processing", "percentage": 90,
                                "description": "Test finished. Results post processing started"}}
        response = requests.put(url, json=data, headers=headers)
        try:
            print(response.json()["message"])
        except:
            print(response.text)


if __name__ == '__main__':
    update_test_status()
    args = get_args()
    logParser = ErrorLogParser(args)
    try:
        aggregated_errors = logParser.parse_errors()
    except Exception as e:
        aggregated_errors = {}
    prefix = environ.get('DISTRIBUTED_MODE_PREFIX')
    save_reports = True if environ.get('save_reports') == "True" else False
    token = environ.get('token')
    if prefix:
        PROJECT_ID = environ.get('project_id')
        URL = environ.get('galloper_url')
        BUCKET = environ.get("results_bucket")
        if not all(a for a in [URL, BUCKET]):
            exit(0)

        # Make archive with gatling reports
        path_to_reports = "/tmp/reports_" + prefix + "_" + str(args['lg_id'])
        shutil.make_archive(path_to_reports, 'zip', RESULTS_FOLDER)

        # Make archive with data for post processing
        with open(DATA_FOR_POST_PROCESSING_FOLDER + "args.json", 'w') as f:
            f.write(json.dumps(args))
        with open(DATA_FOR_POST_PROCESSING_FOLDER + "aggregated_errors.json", 'w') as f:
            f.write(json.dumps(aggregated_errors))
        path_to_test_results = "/tmp/" + prefix + "_" + str(args['lg_id'])
        shutil.make_archive(path_to_test_results, 'zip', DATA_FOR_POST_PROCESSING_FOLDER)

        # Send data to minio
        headers = {'Authorization': f'bearer {token}'} if token else {}
        upload_url = f'{URL}/api/v1/artifacts/artifacts/{PROJECT_ID}/{BUCKET}'
        requests.post(f'{URL}/api/v1/artifacts/buckets/{PROJECT_ID}', data={"name": BUCKET}, allow_redirects=True,
                      headers={**headers, 'Content-type': 'application/json'})
        files = {'file': open(path_to_test_results + ".zip", 'rb')}

        requests.post(upload_url, allow_redirects=True, files=files, headers=headers)
        if save_reports:
            files = {'file': open(path_to_reports + ".zip", 'rb')}
            requests.post(upload_url, allow_redirects=True, files=files, headers=headers)

    else:
        post_processor = PostProcessor()
        post_processor.post_processing(args, aggregated_errors)
