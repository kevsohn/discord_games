from os import path
from random import sample

from flask import Blueprint, session, request, jsonify
from psycopg2.extras import RealDictCursor

import config
import db
import db_utils


# globals
game = path.splitext(path.basename(__file__))[0]
gid = config.GAMES[game]

mines_bp = Blueprint(f'{game}', __name__, url_prefix=f'/{game}')

# game params
nmines = 10
ndim = 8


# --------------- helper ------------------
def reset_state():
    session['board'] = [[0 for _ in range(ndim)] for _ in range(ndim)]
    session['revealed'] = [[False for _ in range(ndim)] for _ in range(ndim)]
    session['mines'] = gen_mines(nmines, ndim)


def gen_mines(nmines, ndim):
    coords = [(i,j) for i in range(ndim) for j in range(ndim)]
    #coords.remove(avoid)
    return sample(coords, nmines)


def init_board(mines, board, revealed):
    for mine in mines:
        i,j = mine
        board[i][j] = -1
        for r in range(max(i-1, 0), min(i+2, ndim)):
            for c in range(max(j-1, 0), min(j+2, ndim)):
                if board[r][c] != -1:
                    board[r][c] += 1
    print_board(board, ndim)


def print_board(board, ndim):
    for i in range(ndim):
        for j in range(ndim):
            print(board[i][j], end="  ")
        print('\n')


def reveal(i, j, board, revealed):
    if revealed[i][j]:
        return
    revealed[i][j] = True
    # '0' is empty tile (i.e. no mines in nghbrhood)
    if board[i][j] == 0:
        for r in range(max(i-1, 0), min(i+2, ndim)):
            for c in range(max(j-1, 0), min(j+2, ndim)):
                if r == i and c == j:
                    continue
                reveal(r, c, board, revealed)


# ---------------- main -------------------
@mines_bp.route('/start', methods=['GET'])
def start():
    #start_pos = tuple(request.json.get('choice'))
    #reset_state(start_pos)
    reset_state()
    init_board(session['mines'], session['board'], session['revealed'])
    # change score/hscore to TEXT
    session['hscore'][gid] = db_utils.get_hscore(session['id'], gid)
    return jsonify(hscore=session['hscore'][gid], nmines=nmines)


@mines_bp.route('/create_grid', methods=['GET'])
def create_grid():
    return jsonify(ndim=ndim)


@mines_bp.route('/verify', methods=['POST'])
def verify_choice():
    data = request.get_json(silent=True)  # safely parse JSON
    if not data:
        return jsonify(error="Invalid JSON"), 400

    choice = data.get("choice")
    if not isinstance(choice, list) or len(choice) != 2:
        return jsonify(error="Position must be a list of size 2"), 400

    try:
        i,j = map(int, choice)  # ensure coordinates are integers
    except ValueError:
        return jsonify(error="Coordinates must be integers"), 400

    mines = session['mines']
    if (i,j) in mines:
        # return mines to show their pos
        return jsonify(status='game_over', mines=mines)
    # else, flood reveal all non-mine tiles
    board = session['board']
    revealed = session['revealed']
    reveal(i, j, board, revealed)
    revealed_nums = [
        {"r": i, "c": j, "num": board[i][j]}
        for i, row in enumerate(revealed)
        for j, is_revealed in enumerate(row)
        if is_revealed
    ]
    return jsonify(status='continue', revealed=revealed_nums)


@mines_bp.route('/update', methods=['POST'])
def update_scores():
    score = request.json.get('score')
    # less is better since time
    if score < session['hscore'][gid]:
        db_utils.update_hscore(score, session['id'], gid)
    db_utils.update_score(score, session['id'], gid)
    return jsonify(status='success')


