from os import environ
from dotenv import load_dotenv
from secrets import token_urlsafe

# exports .env variables
load_dotenv()

# for bot
BOT_TOKEN = environ.get('BOT_TOKEN')
CMD_PREFIX = '!'

# for discord
CLIENT_ID = environ.get('CLIENT_ID')
CLIENT_SECRET = environ.get('CLIENT_SECRET')
API_ENDPOINT = 'https://discord.com/api/v10'
REDIR_URI = environ.get('REDIR_URI')

# for server
SECRET_KEY = token_urlsafe(32)
BASE_URL = environ.get('BASE_URL')
DB_URL = environ.get('DB_URL')
# rank them in order of desired gauntlet seq
GAMES = {
        'minesweeper': 1,
        'simon': 2,
        'num_guess': 3
}
# adjustable game params
MINESWEEPER = {
        'ndim': 8,
        'nmines': 10
}
SIMON = {
        'max_seq': 20
}
GUESS = {
        'max_turn': 7
}
