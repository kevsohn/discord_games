from os import path
from random import sample

from flask import Blueprint, session, request, jsonify
from psycopg2.extras import RealDictCursor

import config
import db
import db_utils


# game id
gid = path.splitext(path.basename(__file__))[0]
mines_bp = Blueprint(f'{gid}', __name__, url_prefix=f'/{gid}')

# game params
ndim = config.MINESWEEPER['ndim']
nmines = config.MINESWEEPER['max_score']


# --------------- helper ------------------
def reset_state():
    session['board'] = [[0 for _ in range(ndim)] for _ in range(ndim)]
    session['revealed'] = [[False for _ in range(ndim)] for _ in range(ndim)]
    session['flagged'] = [[False for _ in range(ndim)] for _ in range(ndim)]
    session['mines'] = []
    session['nflags'] = nmines
    session['finished'] = False


# generate mine coords excluding start tile
def gen_mines(nmines, ndim, safe_tile):
    coords = [(i,j) for i in range(ndim) for j in range(ndim)]
    coords.remove(safe_tile)
    return sample(coords, nmines)


def init_board(mines, board):
    for mine in mines:
        i,j = mine
        # mines are '-1'
        board[i][j] = -1
        # loop thru all 8 neighbours of each mine
        # and incr mine counter to all neighbouring non-mines
        for r in range(max(i-1, 0), min(i+2, ndim)):
            for c in range(max(j-1, 0), min(j+2, ndim)):
                if board[r][c] != -1:
                    board[r][c] += 1


def print_board(board, ndim):
    for i in range(ndim):
        for j in range(ndim):
            print(board[i][j], end="  ")
        print('\n')


# score == nmines correctly flagged
def tally_score(mines, flagged):
    score = 0
    for (i,j) in mines:
        if flagged[i][j]:
            score += 1
    return score


def reveal_tiles(i, j, board, revealed, flagged):
    flood_reveal(i, j, board, revealed, flagged)
    return [
        {"r": r, "c": c, "num": board[r][c]}
        for r, row in enumerate(revealed)
        for c, is_revealed in enumerate(row)
        if is_revealed
    ]


# flood reveal empty tiles (no neighbouring mines)
def flood_reveal(i, j, board, revealed, flagged):
    # do nothing if already revealed or flagged
    if revealed[i][j] or flagged[i][j]:
        return
    revealed[i][j] = True
    # '0' is empty tile
    if board[i][j] == 0:
        for r in range(max(i-1, 0), min(i+2, ndim)):
            for c in range(max(j-1, 0), min(j+2, ndim)):
                if r == i and c == j:
                    continue
                if flagged[i][j]:
                    continue
                flood_reveal(r, c, board, revealed, flagged)


# only need to check if all non-mine tiles are revealed
# b/c win is checked after if mine was tripped
def won(board, revealed):
    for i in range(ndim):
        for j in range(ndim):
            if board[i][j] == -1:
                continue
            if not revealed[i][j]:
                return False
    return True


# ---------------- main -------------------
'''
Called on page load/reload.
Either resets the board to a fresh state or restores board state from today.
'''
@mines_bp.route('/init', methods=['GET'])
def init():
    # only reset if 1st time loading for the day
    # else finished stays True so verify() does nothing
    if not session['played'][gid]:
        reset_state()
    # else load prev board state
    session['score'][gid] = db_utils.get_score(session['id'], gid)
    session['hscore'][gid] = db_utils.get_hscore(session['id'], gid)
    return jsonify(ndim=ndim,
                   board=session['board'],
                   revealed=session['revealed'],
                   flagged=session['flagged'],
                   mines=session['mines'],
                   nflags=session['nflags'],
                   finished=session['finished'],
                   score=session['score'][gid],
                   hscore=session['hscore'][gid],
                   played=session['played'][gid])


'''
Only called on the 1st move of the day.
The 1st tile clicked becomes safe and is excluded in mine coord gen.
session['played'][gid] = True here so unfinished boards don't get reset.
'''
def start(safe_tile):
    # start tile is always safe
    session['mines'] = gen_mines(nmines, ndim, safe_tile)
    init_board(session['mines'], session['board'])
    session['played'][gid] = True


'''
Called after every tile click.
'''
@mines_bp.route('/verify', methods=['POST'])
def verify():
    # clicks do nothing once game done
    if session['finished']:
        return jsonify(status='finished')

    choice = request.json.get("choice")
    if not isinstance(choice, list) or len(choice) != 2:
        return jsonify(error="Coordinate must be a list of size 2"), 400
    try:
        i,j = map(int, choice)  # ensure coordinates are integers
    except ValueError:
        return jsonify(error="Coordinate must be a pair of integers"), 400

    board = session['board']
    revealed = session['revealed']
    flagged = session['flagged']

    # if 1st time playing for the day, start
    if not session['played'][gid]:
        start(tuple(choice))
        revealed_tiles = reveal_tiles(i, j, board, revealed, flagged)
        return jsonify(status='started', revealed=revealed_tiles)

    # order matters!
    # clicked flag, do nothing
    if flagged[i][j]:
        return jsonify(status='flagged')

    # clicked mine, game over
    mines = session['mines']
    if (i,j) in mines:
        session['finished'] = True
        score = tally_score(mines, flagged)
        return jsonify(status='game_over', mines=mines, score=score)

    # else flood reveal tiles if necessary EXCEPT flags & mines
    revealed_tiles = reveal_tiles(i, j, board, revealed, flagged)

    # check win after revealing
    if won(board, revealed):
        session['finished'] = True
        return jsonify(status='won', revealed=revealed_tiles, score=nmines)

    return jsonify(status='continue', revealed=revealed_tiles)


@mines_bp.route('/flag', methods=['POST'])
def toggle_flag():
    # stop responding after gg
    if session['finished']:
        return jsonify(status='finished')

    choice = request.json.get("choice")
    if not isinstance(choice, list) or len(choice) != 2:
        return jsonify(error="Coordinate must be a list of size 2"), 400
    try:
        i,j = map(int, choice)  # ensure coordinates are integers
    except ValueError:
        return jsonify(error="Coordinate must be a pair of integers"), 400

    flagged = session['flagged']
    nflags = session['nflags']
    # if flagged, unflag and incr counter
    if (flagged[i][j]):
        flagged[i][j] = False
        nflags += 1
    # else, vice versa but dont decr if nflags == 0
    else:
        if (nflags == 0):
            return jsonify(toggle=False)
        flagged[i][j] = True
        nflags -= 1

    session['flagged'][i][j] = flagged[i][j]
    session['nflags'] = nflags
    return jsonify(toggle=True, nflags=nflags)


@mines_bp.route('/update', methods=['POST'])
def update_scores():
    score = request.json.get('score')
    if score > session['hscore'][gid]:
        db_utils.update_hscore(score, session['id'], gid)
    db_utils.update_score(score, session['id'], gid)
    return jsonify(status='success')


