from os import environ, walk, path
import requests
from urllib.parse import urlparse
import zipfile
from traceback import format_exc

URL = environ.get('galloper_url')
BUCKET = environ.get("bucket")
TEST = environ.get("test")
PATH_TO_FILE = f'/tmp/{TEST}'
TESTS_PATH = environ.get("tests_path", '/opt/gatling')

if (not all(a for a in [URL, BUCKET, TEST])):
    exit(0)

def zipdir(ziph):
    # ziph is zipfile handle
    folders = ['target', 'user-files']
    for folder in folders:
        for root, dirs, files in walk(f'{TESTS_PATH}/{folder}'):
            for f in files:
                ziph.write(path.join(root, f), path.join(root.replace(TESTS_PATH, ''), f))

try:
    ziph = zipfile.ZipFile(PATH_TO_FILE, 'w', zipfile.ZIP_DEFLATED)
    zipdir(ziph)
    ziph.close()
    files = {'file': open(PATH_TO_FILE,'rb')}
    r = requests.post(f'{URL}/artifacts/{BUCKET}/upload', allow_redirects=True, files=files)
except Exception:
    print(format_exc())
