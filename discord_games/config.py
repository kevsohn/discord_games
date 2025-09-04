from os import environ
from dotenv import load_dotenv
from secrets import token_urlsafe

# exports .env variables
load_dotenv()

# for bot
BOT_TOKEN = environ.get('BOT_TOKEN')
CHANNEL_ID = environ.get('CHANNEL_ID')
CMD_PREFIX = '!'

# for discord
CLIENT_ID = environ.get('CLIENT_ID')
CLIENT_SECRET = environ.get('CLIENT_SECRET')
REDIR_URI = environ.get('REDIR_URI')
API_ENDPOINT = 'https://discord.com/api/v10'

# for server
SECRET_KEY = token_urlsafe(32)
BASE_URL = environ.get('BASE_URL')
DB_URL = environ.get('DB_URL')
GAMES = [
        'minesweeper',
        'simon',
        'num_guess'
]

# adjustable game params
MINESWEEPER = {
        'ndim': 8,
        'max_score': 10,
        'rank_order': 'desc'
}
SIMON = {
        'max_score': 20,
        'rank_order': 'desc'
}
NUM_GUESS = {
        'max_score': 7,
        'rank_order': 'asc'
}
