from os import environ
from dotenv import load_dotenv
from secrets import token_urlsafe

# exports .env variables
load_dotenv()

SECRET_KEY = token_urlsafe(32)
BOT_TOKEN = environ.get('BOT_TOKEN')
DB_URL = environ.get('DB_URL')
