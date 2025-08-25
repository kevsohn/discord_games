from os import path
from flask import Blueprint, session, request, jsonify
import config
import db

game = path.splitext(path.basename(__file__))[0]
gid = config.GAMES[game]

mines_bp = Blueprint(f'{game}', __name__, url_prefix=f'/{game}')


