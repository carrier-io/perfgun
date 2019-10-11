import csv
from difflib import SequenceMatcher
import datetime
import re


FIELDNAMES = 'error_key', 'request_name', 'method', "status_code", "url", "error_message", "params", "headers", "body"

ERROR_FIELDS = 'Response', 'Request_params', 'Error_message'

PATH = '/opt/gatling/bin/logs/errors/'


class SimulationLogParser(object):
    def __init__(self, arguments):
        self.args = arguments

    def parse_errors(self):
        """Parse line with error and send to database"""
        simulation = self.args['simulation']
        path = PATH + simulation + ".log"
        unparsed_counter = 0
        aggregated_errors = {}
        with open(path, 'r+', encoding="utf-8") as tsv:
            for entry in csv.DictReader(tsv, delimiter="\t", fieldnames=FIELDNAMES, restval="not_found"):
                try:
                    data = {'request_name': entry['request_name'].replace("Request name: ", ""),
                            'response_code': entry['status_code'].replace("Response code: ", ""),
                            'request_url': entry['url'].replace("URL: ", ""),
                            'request_params': entry['params'].replace("Request params: ", ""),
                            'request_method': entry['method'].replace("Method: ", ""),
                            'headers': entry['headers'].replace("Headers: ", ""),
                            'response': entry['body'].replace("Response body: ", ""),
                            'error_message': entry['error_message'].replace("Error message: ", "")}

                    key = entry['error_key'].replace("Error key: ", "")
                    if key not in aggregated_errors:
                        aggregated_errors[key] = {"Request name": data['request_name'],
                                                  "Method": data['request_method'],
                                                  "Request headers": data["headers"], 'Error count': 1,
                                                  "Response code": data['response_code'],
                                                  "Request URL": data['request_url'],
                                                  "Request_params": [data['request_params']],
                                                  "Response": [data['response']],
                                                  "Error_message": [data['error_message']]}
                    else:
                        aggregated_errors[key]['Error count'] += 1
                        for field in ERROR_FIELDS:
                            same = self.check_dublicate(aggregated_errors[key], data, field)
                            if same is True:
                                break
                            else:
                                aggregated_errors[key][field].append(data[field.lower()])
                except Exception as e:
                    print(e)
                    unparsed_counter += 1
                    pass

        if unparsed_counter > 0:
            print("Unparsed errors: %d" % unparsed_counter)
        return aggregated_errors

    @staticmethod
    def check_dublicate(entry, data, field):
        for params in entry[field]:
            if SequenceMatcher(None, str(data[field.lower()]), str(params)).ratio() > 0.7:
                return True
