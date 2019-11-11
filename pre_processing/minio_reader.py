from os import environ
from minio import Minio
from minio.error import ResponseError
from urllib.parse import urlparse
import zipfile

URL = environ.get('minio_url')
ACCESS_KEY = environ.get('minio_access_key')
SECRET_KEY = environ.get('minio_secret_key')
BUCKET = environ.get("minio_bucket")
TEST = environ.get("minio_test")
PATH_TO_FILE = f'/tmp/{TEST}'
TESTS_PATH = environ.get("tests_path", '/opt/gatling/tests')

if (not all(a for a in [URL, ACCESS_KEY, SECRET_KEY, BUCKET, TEST])):
    exit(0)

parsed = urlparse(URL)

minioClient = Minio(parsed.netloc,
                  access_key=ACCESS_KEY,
                  secret_key=SECRET_KEY,
                  secure=True if parsed.scheme == 'https' else False)

try:
    data = minioClient.get_object(BUCKET, TEST)
    with open(PATH_TO_FILE, 'wb') as file_data:
        for d in data.stream(32*1024):
            file_data.write(d)
    with zipfile.ZipFile(PATH_TO_FILE, 'r') as zip_ref:
        zip_ref.extractall(TESTS_PATH)
except ResponseError as err:
    print(err)