from os import environ
import requests
from urllib.parse import urlparse
import zipfile
from traceback import format_exc

URL = environ.get('galloper_url')
BUCKET = environ.get("bucket")
TEST = environ.get("artifact")
PATH_TO_FILE = f'/tmp/{TEST}'
TESTS_PATH = environ.get("tests_path", '/opt/gatling')

if (not all(a for a in [URL, BUCKET, TEST])):
    exit(0)

try:
    r = requests.get(f'{URL}/artifacts/{BUCKET}/{TEST}', allow_redirects=True)
    with open(PATH_TO_FILE, 'wb') as file_data:
        file_data.write(r.content)
    with zipfile.ZipFile(PATH_TO_FILE, 'r') as zip_ref:
        zip_ref.extractall(TESTS_PATH)
except Exception:
    print(format_exc())

