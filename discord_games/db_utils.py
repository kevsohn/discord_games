from flask import current_app
from psycopg2.extras import RealDictCursor

import db


# ensures db is initialized for any API calls
def init_games_db(game_id):
    conn = db.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                insert into games (id, max_score, rank_order)
                values (%s, %s, %s)
                on conflict (id) do nothing;
            """, (game_id,
                  current_app.config[game_id.upper()]['max_score'],
                  current_app.config[game_id.upper()]['rank_order'])
            )
        conn.commit()
    finally:
        db.close_conn()


def init_highscores_db(player_id, game_id):
    conn = db.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                insert into highscores (player_id, game_id)
                values (%s, %s)
                on conflict (player_id, game_id) do nothing;
            """, (player_id, game_id)
            )
        conn.commit()
    finally:
        db.close_conn()


def init_scores_db(player_id, game_id):
    conn = db.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                insert into scores (player_id, game_id)
                values (%s, %s)
                on conflict (player_id, game_id) do nothing;
            """, (player_id, game_id)
            )
        conn.commit()
    finally:
        db.close_conn()


# get highscore or init it
def get_hscore(player_id, game_id, init=0):
    conn = db.get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                select hscore from highscores
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
                UPDATE highscores
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

