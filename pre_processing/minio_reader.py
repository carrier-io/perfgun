from os import environ
import requests
import zipfile
from traceback import format_exc

URL = environ.get('galloper_url')
BUCKET = environ.get("bucket")
TEST = environ.get("artifact")
PATH_TO_FILE = f'/tmp/{TEST}'
TESTS_PATH = environ.get("tests_path", '/opt/gatling')
PROJECT_ID = environ.get('project_id')
TOKEN = environ.get("token")

if (not all(a for a in [URL, BUCKET, TEST])):
    exit(0)

try:
    if PROJECT_ID:
        endpoint = f'/api/v1/artifacts/{PROJECT_ID}/{BUCKET}/{TEST}'
    else:
        endpoint = f'/artifacts/{BUCKET}/{TEST}'
    headers = {'Authorization': f'bearer {TOKEN}'} if TOKEN else {}
    r = requests.get(f'{URL}/{endpoint}', allow_redirects=True, headers=headers)
    with open(PATH_TO_FILE, 'wb') as file_data:
        file_data.write(r.content)
    with zipfile.ZipFile(PATH_TO_FILE, 'r') as zip_ref:
        zip_ref.extractall(TESTS_PATH)
except Exception:
    print(format_exc())
