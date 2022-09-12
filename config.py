# Define the application directory
import os
from dotenv import load_dotenv

load_dotenv()

# Statement for enabling the development environment
# DEBUG = True

# Define the database - we are working with SQLite for this example
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


# Database configuration for local sqlite database
# SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'test.db').replace("mysql://", "mysql+pymysql://")

# Database configuration for upgraded HEROKU database
# SQLALCHEMY_DATABASE_URI = os.environ.get('HEROKU_POSTGRESQL_MAROON_URL').replace("://", "ql://", 1)
# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace("://", "ql://", 1)

# Database for postgresql
# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
#                                          'postgresql://localhost/dbdw').replace(
#                                          "mysql://", "mysql+pymysql://")

SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                         'postgresql://localhost/long_dump_copy').replace(
                                         "mysql://", "mysql+pymysql://")

DATABASE_CONNECT_OPTIONS = {}

# Application threads. A common general assumption is using 2 per available processor cores - to handle
# incoming requests using one and performing background operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "secret"

# Secret key for signing cookies
# replace with a fixed secret key during stduy
# SECRET_KEY = "~QLoJ[G7c?Kj!)`lXH+Y00Etdu^EnH"
SECRET_KEY = os.urandom(16)

# set SQLALCHEMY maximum concurrent thread number
# SQLALCHEMY_POOL_SIZE = 20

# Mail setting
# MAIL_SERVER = 'smtp.gmail.com'
# MAIL_PORT = 465
# MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
# MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
# MAIL_USE_TLS = False
# MAIL_USE_SSL = True

MAIL_SERVER = "smtp.tue.nl"
MAIL_PORT = 587
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_USE_TLS = True
MAIL_USE_SSL = False

SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')

SPOTIFY_SCRAPE_CLIENT_ID = os.environ.get('SPOTIFY_SCRAPE_CLIENT_ID')
SPOTIFY_SCRAPE_CLIENT_SECRET = os.environ.get('SPOTIFY_SCRAPE_CLIENT_SECRET')