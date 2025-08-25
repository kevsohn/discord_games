from os import environ
from dotenv import load_dotenv
from secrets import token_urlsafe

# exports .env variables
load_dotenv()

# for discord
BOT_TOKEN = environ.get('BOT_TOKEN')
CLIENT_ID = environ.get('CLIENT_ID')
CLIENT_SECRET = environ.get('CLIENT_SECRET')
API_ENDPOINT = environ.get('API_ENDPOINT')
REDIR_URI = environ.get('REDIR_URI')

# for server
SECRET_KEY = token_urlsafe(32)
BASE_URL = environ.get('BASE_URL')
DB_URL = environ.get('DB_URL')
# rank them in order of desired gauntlet seq
GAMES = {
        'simon': 1,
        'minesweeper': 2
}
