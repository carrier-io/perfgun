from os import environ
import requests
import zipfile
from traceback import format_exc
from centry_loki import log_loki

URL = environ.get('galloper_url')
BUCKET = environ.get("bucket")
TEST = environ.get("artifact")
PATH_TO_FILE = f'/tmp/{TEST}'
TESTS_PATH = environ.get("tests_path", '/opt/gatling')
PROJECT_ID = environ.get('project_id')
TOKEN = environ.get("token")

if (not all(a for a in [URL, BUCKET, TEST])):
    exit(0)

context = {
    "url": f"{environ.get('loki_host').replace('https://', 'http://')}:{environ.get('loki_port')}/loki/api/v1/push",
    "hostname": environ.get("lg_id"), "labels": {"build_id": environ.get("build_id"),
                                                 "project": environ.get("project_id"),
                                                 "report_id": environ.get("report_id")}}
logger = log_loki.get_logger(context)
try:
    logger.info(f"Download artifacts. Bucket {BUCKET}, file {TEST}")
    endpoint = f'/api/v1/artifacts/artifact/{PROJECT_ID}/{BUCKET}/{TEST}'
    headers = {'Authorization': f'bearer {TOKEN}'} if TOKEN else {}
    r = requests.get(f'{URL}/{endpoint}', allow_redirects=True, headers=headers)
    with open(PATH_TO_FILE, 'wb') as file_data:
        file_data.write(r.content)
    with zipfile.ZipFile(PATH_TO_FILE, 'r') as zip_ref:
        zip_ref.extractall(TESTS_PATH)
except Exception:
    logger.error("Failed download artifacts")
    print(format_exc())

