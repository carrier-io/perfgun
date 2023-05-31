from os import environ, walk, path
import requests
import json
from urllib.parse import urlparse
import zipfile
from traceback import format_exc

URL = environ.get('galloper_url')
BUCKET = environ.get("bucket")
TEST = environ.get("artifact")
PATH_TO_FILE = f'/tmp/{TEST}'
TESTS_PATH = environ.get("tests_path", '/opt/gatling')
PROJECT_ID = environ.get('project_id')
TOKEN = environ.get("token")

integrations = json.loads(environ.get("integrations", '{}'))
s3_config = integrations.get('system', {}).get('s3_integration', {})

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
    headers = {'Authorization': f'bearer {TOKEN}'} if TOKEN else {}
    upload_url = f'{URL}/api/v1/artifacts/artifacts/{PROJECT_ID}/{BUCKET}'
    r = requests.post(upload_url, params=s3_config, allow_redirects=True, files=files, headers=headers)
except Exception:
    print(format_exc())
