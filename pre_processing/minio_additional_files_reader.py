from os import environ
import requests
from traceback import format_exc
import json

PROJECT_ID = environ.get('project_id')
URL = environ.get('galloper_url')
ADDITIONAL_FILES = environ.get("additional_files")
TOKEN = environ.get("token")

if not all(a for a in [URL, ADDITIONAL_FILES]):
    exit(0)

try:
    files = json.loads(ADDITIONAL_FILES)
    if PROJECT_ID:
        endpoint = f'/api/v1/artifact/{PROJECT_ID}'
    else:
        endpoint = '/artifacts'
    headers = {'Authorization': f'bearer {TOKEN}'} if TOKEN else {}
    for file, path in files.items():
        r = requests.get(f'{URL}/{endpoint}/{file}', allow_redirects=True, headers=headers)
        with open(path, 'wb') as file_data:
            file_data.write(r.content)
except Exception:
    print(format_exc())

