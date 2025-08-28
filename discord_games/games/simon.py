from os import path
from random import choice

from flask import Blueprint, session, request, jsonify
from psycopg2.extras import RealDictCursor

import config
import db
import db_utils


# globals
game = path.splitext(path.basename(__file__))[0]
gid = config.GAMES[game]

# Blueprints make it modular by being indep of the homepage
simon_bp = Blueprint(f'{game}', __name__, url_prefix=f'/{game}')

# game params
max_seq = 20
colours = ["r", "g", "b", "o"]


# --------------- helper ------------------
def reset_state():
    session['sequence'] = [choice(colours) for _ in range(max_seq)]
    session['turn_num'] = 0
    session['score'][gid] = 0


# ---------------- main -------------------
# GET should be used for safe and idempotent requests
# POST for modifying requests, aka REST principle
# reason: clients can meddle with the state by modifying params in the url,
# not that POST is infallable since all the info is still visible to men-in-the-middle
@simon_bp.route('/start', methods=['GET'])
def start():
    reset_state()
    session['hscore'][gid] = db_utils.get_hscore(session['id'], gid)
    return jsonify(highscore=session['hscore'][gid])


# the current score gives the max turn num
@simon_bp.route('/sequence', methods=['POST'])
def get_sequence():
    seq = session['sequence']
    score = session['score'][gid]
    return jsonify(sequence=seq[:score+1])


# state change driver using status
@simon_bp.route('/verify', methods=['POST'])
def verify_choice():
    colour = request.json.get('choice')
    if colour not in colours:
        return jsonify(error='Unexpected choice'), 400

    turn_num = session['turn_num']
    score = session['score'][gid]
    # game over
    if colour != session['sequence'][turn_num]:
        hscore = session['hscore'][gid]
        # only update hscore if ending score > hscore
        if score > hscore:
            hscore = score
            db_utils.update_hscore(hscore, session['id'], gid)
        # update daily score
        db_utils.update_score(score, session['id'], gid)
        return jsonify(status='game_over', highscore=hscore, final=score)
    # success
    turn_num += 1
    # if last possible turn, continue to next round
    # better than turn_num > score if they somehow get out of sync
    if turn_num == score+1:
        # reset and incr score by 1
        session['turn_num'] = 0
        session['score'][gid] = turn_num
        return jsonify(status='continue', score=turn_num)
    # else goto next colour in seq
    session['turn_num'] = turn_num
    return jsonify(status='next')
