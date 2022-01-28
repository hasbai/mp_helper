import os

import diskcache

db = diskcache.Cache('data/db')

APP_ID = os.environ.get('MP_APP_ID')
APP_SECRET = os.environ.get('MP_APP_SECRET')
PROXY = os.environ.get('HTTP_PROXY')
AUTHOR = os.environ.get('AUTHOR')
TOKEN = os.environ.get('TOKEN', '')
assert APP_ID, 'Environment variable MP_APP_ID must be set.'
assert APP_SECRET, 'Environment variable MP_APP_SECRET must be set.'
if not TOKEN:
    print('[W] Environment variable TOKEN not set, should not use in production environment.')
