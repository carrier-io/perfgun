from os import environ
import requests
from traceback import format_exc
import json
from centry_loki import log_loki

PROJECT_ID = environ.get('project_id')
URL = environ.get('galloper_url')
ADDITIONAL_FILES = environ.get("additional_files")
TOKEN = environ.get("token")

if not all(a for a in [URL, ADDITIONAL_FILES]):
    exit(0)

context = {
        "url": f"{environ.get('loki_host').replace('https://', 'http://')}:{environ.get('loki_port')}/loki/api/v1/push",
        "hostname": environ.get("lg_id"), "labels": {"build_id": environ.get("build_id"),
                                                     "project": environ.get("project_id"),
                                                     "report_id": environ.get("report_id")}}
logger = log_loki.get_logger(context)
try:
    files = json.loads(ADDITIONAL_FILES)
    logger.info(f"Download extensions: {files}")
    endpoint = f'/api/v1/artifacts/artifact/{PROJECT_ID}'
    headers = {'Authorization': f'bearer {TOKEN}'} if TOKEN else {}
    for file, path in files.items():
        r = requests.get(f'{URL}/{endpoint}/{file}', allow_redirects=True, headers=headers)
        with open(path, 'wb') as file_data:
            file_data.write(r.content)
except Exception:
    logger.error("Failed download extensions")
    print(format_exc())

