import os

import diskcache

APP_ID = os.environ.get('MP_APP_ID')
APP_SECRET = os.environ.get('MP_APP_SECRET')
assert APP_ID, 'Environment variable MP_APP_ID must be set.'
assert APP_SECRET, 'Environment variable MP_APP_SECRET must be set.'

db = diskcache.Cache('data/db')
