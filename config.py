# Define the application directory
import os
from dotenv import load_dotenv

load_dotenv()

# Statement for enabling the development environment
DEBUG = True

# Define the database - we are working with
# SQLite for this example
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


# Database configuration for low level HEROKU database and local sqlite database
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                         'sqlite:///' + os.path.join(BASE_DIR, 'test_new.db')).replace("mysql://",
                                                                                                   "mysql+pymysql://")

# Database configuration for low level HEROKU database and local postgresql database
# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
#                                          'postgresql://yu:'+os.environ.get('YU_POSTGRESQL_PASSWORD')+
#                                          '@postgresql/explore_test')
#SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace("://", "ql://", 1)

# Database configuration for upgraded HEROKU database
# SQLALCHEMY_DATABASE_URI = os.environ.get('HEROKU_POSTGRESQL_MAROON_URL').replace("://", "ql://", 1)

DATABASE_CONNECT_OPTIONS = {}

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "secret"

# Secret key for signing cookies
SECRET_KEY = os.urandom(16)

# set SQLALCHEMY maximum concurrent thread number
# SQLALCHEMY_POOL_SIZE = 20