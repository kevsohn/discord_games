from random import choice
from flask import Blueprint, session, request, jsonify
from psycopg2.extras import RealDictCursor, DictCursor
import db

# Blueprints make it modular by being indep of the homepage
simon_bp = Blueprint('simon', __name__)

# game params
max_seq = 20
colours = ["r", "g", "b", "o"]


# --------------- helper ------------------
def reset_state():
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
    conn = db.get_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            select highscore from players
            where id = %s;
        """, (session['id'],))
        row = cur.fetchone()
        if row is None:
            return "User not found", 400
        session['highscore'] = row.get('highscore')

    reset_state()
    return jsonify(highscore=session['highscore'])


@simon_bp.route('/sequence', methods=['POST'])
def get_sequence():
    seq = session.get('sequence', [])
    score = session.get('score', 0)
    return jsonify(sequence=seq[:score+1])


# state change driver
@simon_bp.route('/verify', methods=['POST'])
def verify_choice():
    colour = request.json.get('choice')
    if colour not in colours:
        return jsonify(error='Unexpected choice'), 400

    turn_num = session.get('turn_num')
    score = session.get('score')
    # if game over
    if colour != session.get('sequence')[turn_num]:
        highscore = session.get('highscore')
        # only update db when new highscore
        if score > highscore:
            highscore = score
            conn = db.get_conn()
            with conn.cursor() as cur:
                cur.execute("""
                    update players
                    set highscore = %s
                    where id = %s;
                """, (highscore, session['id']))
                conn.commit()
        return jsonify(status='game_over', highscore=highscore, final=score)

    turn_num += 1
    # if last correct turn
    # better than turn_num > score if they somehow get out of sync
    if turn_num == score+1:
        session['turn_num'] = 0
        session['score'] = turn_num
        return jsonify(status='continue', score=turn_num)

    # else goto next turn in seq
    session['turn_num'] = turn_num
    return jsonify(status='next')
