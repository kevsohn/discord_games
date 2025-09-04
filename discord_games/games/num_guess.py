from os import path
from random import randint
from flask import Blueprint, session, request, jsonify
from psycopg2.extras import RealDictCursor
import config
import db
import db_utils

# game id
gid = path.splitext(path.basename(__file__))[0]
guess_bp = Blueprint(f'{gid}', __name__, url_prefix=f'/{gid}')

# game params
max_turn = config.NUM_GUESS['max_score']


# --------------- helper ------------------
def reset_state():
    session['ans'] = randint(1, 100)
    session['score'][gid] = 1


# ---------------- main -------------------
@guess_bp.route('/start', methods=['GET'])
def start():
    reset_state()
    session['hscore'][gid] = db_utils.get_hscore(session['id'], gid, init=max_turn)
    return jsonify(max_turn=max_turn, hscore=session['hscore'][gid])


@guess_bp.route('/verify', methods=['POST'])
def verify_guess():
    guess = request.json.get('guess')
    if not isinstance(guess, int):
        return jsonify(error='Guess should be an integer'), 400
    if guess < 1 or guess > 100:
        return jsonify(error='Guess should be between 1-100'), 400

    ans = session['ans']
    score = session['score'][gid]
    # game over if not correct on max_turn
    # [0, max_turn) amount of tries
    if guess == ans or score == max_turn:
        # update daily score
        db_utils.update_score(score, session['id'], gid)
        hscore = session['hscore'][gid]
        if guess == ans:
            # a lower score is better, so update hscore
            if score < hscore:
                hscore = score
                db_utils.update_hscore(hscore, session['id'], gid)
            return jsonify(status='win', hscore=hscore, final=score)
        # score is 'X'/max_turn on client side
        return jsonify(status='game_over', ans=ans, hscore=hscore)
    # else continue to next turn
    score += 1
    session['score'][gid] = score
    if guess < ans:
        return jsonify(status='continue', hint='higher', score=score)
    else:
        return jsonify(status='continue', hint='lower', score=score)


