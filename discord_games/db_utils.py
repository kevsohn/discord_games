from psycopg2.extras import RealDictCursor
import db

# get highscore or init it
def get_hscore(player_id, game_id, init=0):
    conn = db.get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                select hscore from scores
                where player_id = %s and game_id = %s;
            """, (player_id, game_id))
            hscore = cur.fetchone()['hscore']
            # server inits others so only hscore can be none
            if hscore is None:
                return init
            return hscore
    finally:
        db.close_conn()


# update all-time high score
def update_hscore(hscore, player_id, game_id):
    conn = db.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE scores
                SET hscore = %s
                WHERE player_id = %s AND game_id = %s;
            """, (hscore, player_id, game_id))
            conn.commit()
    finally:
        db.close_conn()


# update daily score
def update_score(score, player_id, game_id):
    conn = db.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE scores
                SET score = %s
                WHERE player_id = %s AND game_id = %s;
            """, (score, player_id, game_id))
            conn.commit()
    finally:
        db.close_conn()

