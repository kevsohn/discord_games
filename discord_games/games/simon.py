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
    session['g1_score'] = 0
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
            select hscore from scores
            where player_id = %s and game_id = 1
        """, (session['id'],))
        row = cur.fetchone()
        if row is None:
            # client expects json so can't just return text
            return jsonify(error="User not found"), 400
        session['g1_hscore'] = row['hscore']

    reset_state()
    return jsonify(highscore=session['g1_hscore'])


@simon_bp.route('/sequence', methods=['POST'])
def get_sequence():
    seq = session['sequence']
    score = session['g1_score']
    return jsonify(sequence=seq[:score+1])


# state change driver
@simon_bp.route('/verify', methods=['POST'])
def verify_choice():
    colour = request.json.get('choice')
    if colour not in colours:
        return jsonify(error='Unexpected choice'), 400

    turn_num = session['turn_num']
    score = session['g1_score']
    # if game over
    if colour != session['sequence'][turn_num]:
        conn = db.get_conn()
        hscore = session['g1_hscore']
        if score > hscore:
            hscore = score
            # store all time high score for this game
            with conn.cursor() as cur:
                cur.execute("""
                    update scores
                    set hscore = %s
                    where player_id = %s and game_id = 1;
                """, (hscore, session['id']))
            conn.commit()
        # store daily score
        with conn.cursor() as cur:
            cur.execute("""
                update scores
                set score = %s
                where player_id = %s and game_id = 1;
            """, (score, session['id']))
        conn.commit()
        return jsonify(status='game_over', highscore=hscore, final=score)

    turn_num += 1
    # if last correct turn
    # better than turn_num > score if they somehow get out of sync
    if turn_num == score+1:
        session['turn_num'] = 0
        session['g1_score'] = turn_num
        return jsonify(status='continue', score=turn_num)

    # else goto next turn in seq
    session['turn_num'] = turn_num
    return jsonify(status='next')
