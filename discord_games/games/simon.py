from flask import Blueprint, session, request, jsonify
from psycopg2.extras import RealDictCursor, DictCursor
from random import choice
import db

# Blueprints make it modular by being indep of the homepage
simon_bp = Blueprint('simon', __name__)

# game params
max_seq = 20
colours = ["r", "g", "b", "o"]

"""
# need to init player_id first
conn = db.get_conn()
with conn.get_cursor(cursor_factory=DictCursor) as cur:
    cur.execute("select high_score from players where id = %s", (session['user_id'],))
    row = cur.fetchone()
    if row:
        high_score = row['high_score']
db.close_conn()
"""
high_score = 0


# --------------- helper ------------------
# session vars is local to each user sesh but acts like a global var
def reset_state():
    # db.store(seq)  # all players are given the same sequence
    session['sequence'] = [choice(colours) for _ in range(max_seq)]
    session['score'] = 0
    session['turn_num'] = 0


# ---------------- main -------------------
# GET should be used for safe and idempotent requests
# POST for modifying requests, aka REST principle
# reason: clients can meddle with the state by modifying params in the url,
# not that POST is infallable since all the info is still visible to men-in-the-middle
@simon_bp.route('/start', methods=['GET'])
def start():
    reset_state()
    return jsonify(highscore=high_score)


@simon_bp.route('/sequence', methods=['POST'])
def get_sequence():
    seq = session.get('sequence', [])
    score = session.get('score', 0)
    return jsonify(sequence=seq[:score+1])

# state change driver
@simon_bp.route('/verify', methods=['POST'])
def verify_choice():
    global high_score
    colour = request.json.get('choice')
    # sufficient security?
    if colour not in colours:
        return jsonify(error='Unexpected choice'), 400

    seq = session.get('sequence')
    turn_num = session.get('turn_num')
    score = session.get('score')
    if colour != seq[turn_num]:
        high_score = score if score > high_score else high_score
        # db.store(high_score)
        return jsonify(status='game_over', highscore=high_score, final=score)

    turn_num += 1
    # better than turn_num > score if they somehow get out of sync
    if turn_num == score+1:
        session['turn_num'] = 0
        session['score'] = score+1
        return jsonify(status='continue', score=session.get('score'))

    session['turn_num'] = turn_num
    return jsonify(status='next')
