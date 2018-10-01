host = 'localhost'
port = 8000
debug = True

CORS_DESTINATION = r'[.]*'
SQLALCHEMY_DATABASE_URI = 'postgres://pivo:shaurma1337@***REMOVED***'
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = '***REMOVED***'

NAVIADDRESS_SESSION_URL = 'https://staging-api.naviaddress.com/api/v1.5/Sessions'
NAVIADDRESS_ADDRESSES_URL = 'https://staging-api.naviaddress.com/api/v1.5/Addresses'
NAVIADDRESS_ACCEPT_URL = 'https://staging-api.naviaddress.com/api/v1.5/Addresses/accept/{}/{}'
NAVIADDRESS_UPDATE_URL = 'https://staging-api.naviaddress.com/api/v1.5/Addresses/{}/{}'

NAVIADDRESS_DEFAULT_LANG = 'ru'

BOT_EMAIL = '***REMOVED***'
BOT_PASSWORD = '***REMOVED***'

MAX_SEARCH_RADIUS = 10000
