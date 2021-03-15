import argparse
from perfreporter.downsampling import Downsampler


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


if __name__ == '__main__':
    args = get_args()
    Downsampler(args).run()
