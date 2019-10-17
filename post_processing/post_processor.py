import argparse

from error_parser import SimulationLogParser
from perfreporter.post_processor import PostProcessor


def get_args():
    parser = argparse.ArgumentParser(description='Simlog parser.')
    parser.add_argument("-t", "--type", help="Test type.")
    parser.add_argument("-s", "--simulation", help='Test simulation', default=None)  # should be the same as on Grafana
    parser.add_argument("-b", "--build_id", help="build ID", default=None)
    parser.add_argument("-st", "--start_time", help='Test start time', default=None)
    parser.add_argument("-et", "--end_time", help='Test end time', default=None)
    parser.add_argument("-i", "--influx_host", help='InfluxDB host or IP', default=None)
    parser.add_argument("-p", "--influx_port", help='InfluxDB port', default=None)
    parser.add_argument("-iu", "--influx_user", help='InfluxDB user', default="")
    parser.add_argument("-ip", "--influx_password", help='InfluxDB password', default="")
    parser.add_argument("-cm", "--comparison_metric", help='Comparison metric', default="pct95")
    parser.add_argument("-idb", "--influx_database", help='Comparison InfluxDB', default="gatling")
    parser.add_argument("-icdb", "--influx_comparison_database", help='Comparison InfluxDB', default="comparison")
    parser.add_argument("-itdb", "--influx_thresholds_database", help='Thresholds InfluxDB', default="thresholds")
    parser.add_argument("-u", "--users", help='Users count', default=None)
    parser.add_argument("-tl", "--test_limit", help='test_limit', default=5)
    parser.add_argument("-l", "--lg_id", help='Load generator ID', default=None)
    return vars(parser.parse_args())


if __name__ == '__main__':
    args = get_args()

    logParser = SimulationLogParser(args)
    aggregated_errors = logParser.parse_errors()

    post_processor = PostProcessor(args, aggregated_errors)
    post_processor.post_processing()
