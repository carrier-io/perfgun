import argparse
import json
import redis
import shutil
from perfreporter.post_processor import PostProcessor
from perfreporter.error_parser import ErrorLogParser


RESULTS_FOLDER = '/opt/gatling/results/'


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
    parser.add_argument("-r", "--redis_connection", help="redis_connection", default=None)
    parser.add_argument("-l", "--lg_id", help='Load generator ID', default=None)
    parser.add_argument("-el", "--error_logs", help='Path to the error logs', default='/opt/gatling/bin/logs/errors/')
    parser.add_argument("-trl", "--test_results_log", help='Path to the test results log',
                        default='/opt/gatling/bin/logs/test_results.log')
    return vars(parser.parse_args())


if __name__ == '__main__':
    args = get_args()
    logParser = ErrorLogParser(args)
    aggregated_errors = logParser.parse_errors()
    if args['redis_connection']:
        redis_client = redis.Redis.from_url(args['redis_connection'])
        redis_client.set("Errors_" + str(args['lg_id']), json.dumps(aggregated_errors))
        redis_client.set("Arguments", json.dumps(args))
        zip_file = shutil.make_archive("/tmp/" + str(args['lg_id']), 'zip', RESULTS_FOLDER)
        if zip_file:
            with open(zip_file, 'rb') as f:
                redis_client.set("reports_" + str(args['lg_id']) + ".zip", f.read())

    else:
        post_processor = PostProcessor(args, aggregated_errors)
        post_processor.post_processing()
