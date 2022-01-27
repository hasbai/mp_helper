import os

APP_ID = os.environ.get('MP_APP_ID')
APP_SECRET = os.environ.get('MP_APP_SECRET')
DOOCS_MD_URL = os.environ.get('DOOCS_MD_URL', 'https://doocs.github.io/md/')
PROXY = os.environ.get('HTTP_PROXY')
assert APP_ID, 'Environment variable MP_APP_ID must be set.'
assert APP_SECRET, 'Environment variable MP_APP_SECRET must be set.'
