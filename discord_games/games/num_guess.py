from os import path
from random import randint
from flask import Blueprint, session, request, jsonify
from psycopg2.extras import RealDictCursor
import config
import db

# globals
game = path.splitext(path.basename(__file__))[0]
gid = config.GAMES[game]

guess_bp = Blueprint(f'{game}', __name__, url_prefix=f'/{game}')

# game params
max_turn = 6

'''
When the game starts, it should display a welcome message along with the rules of the game.
The computer should randomly select a number between 1 and 100.
User should select the difficulty level (easy, medium, hard) which will determine the number of chances they get to guess the number.
The user should be able to enter their guess.
If the user’s guess is correct, the game should display a congratulatory message along with the number of attempts it took to guess the number.
If the user’s guess is incorrect, the game should display a message indicating whether the number is greater or less than the user’s guess.
The game should end when the user guesses the correct number or runs out of chances.
'''
# --------------- helper ------------------
def reset_state():
    session['ans'] = randint(1, 100)
    session['score'][gid] = 1


# ---------------- main -------------------
# just unlocks the user input area
@guess_bp.route('/start', methods=['GET'])
def start():
    reset_state()
    session['hscore'][gid] = db_utils.get_hscore(session['id'], gid, init=max_turn)
    return jsonify(hscore=session['hscore'][gid])


@guess_bp.route('/verify', methods=['POST'])
def verify_num():
    num = request.json.get('guess')
    if not isinstance(num, int):
        return jsonify(error='Guess should be an integer'), 400
    if num < 0 or num > 100:
        return jsonify(error='Number is between 1-100'), 400

    ans = session['ans']
    score = session['score'][gid]
    # game over if went over max turn or got the ans
    # game is scored from [1, max_turn]
    if score == max_turn+1 or num == ans:
        hscore = session['hscore'][gid]
        # a lower score is better
        # if score >= max_turn, hscore stays max_turn
        if score < hscore:
            hscore = score
            db_utils.update_hscore(hscore, session['id'], gid)
        # update daily score
        db_utils.update_score(score, session['id'], gid)
        # change score to 'X/max_turn' like wordle?
        return jsonify(status='game_over', hscore=hscore, final=score)
    # else continue to next turn
    score += 1
    session['score'][gid] = score
    if num < ans:
        return jsonify(status='continue', hint='higher', score=score)
    else:
        return jsonify(status='continue', hint='lower', score=score)


