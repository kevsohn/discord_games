# native
import time
from datetime import datetime, timezone, timedelta
import requests
from urllib.parse import quote
# extra
from flask import Flask, session, request, render_template, redirect, url_for, jsonify
from flask_session import Session
from psycopg2.extras import RealDictCursor
# custom
import db
import db_utils
from games.simon import simon_bp
from games.minesweeper import mines_bp
from games.num_guess import guess_bp


# can only have 1 app instance, which necessitates Blueprints to keep things modular and organized
app = Flask(__name__)
app.config.from_object('config')
# used to sign cookies
app.secret_key = app.config['SECRET_KEY']
# opts: filesystem, redis, memcached, mongodb, sqlalchemy
app.config['SESSION_TYPE'] = 'filesystem'
# remember to incl url prefix in the JS fetches
app.register_blueprint(simon_bp)
app.register_blueprint(mines_bp)
app.register_blueprint(guess_bp)
# cached data per user session
Session(app)


#============================== INIT ===================================
# init a pool of conns instead of constantly creating and closing new conns
db.init_app(app)
# b/c db code only works inside url methods
with app.app_context():
    try:
        conn = db.get_conn()
        # DictCursor is faster that RealDictCursor but doesnt return a python dict
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                drop table if exists tokens;
                drop table if exists highscores;
                drop table if exists scores;
                drop table if exists players;
                drop table if exists games;
                drop table if exists reset_time;
            """)
            # id: discord id
            # access_t: access token from discord to request info about player
            # refresh_t: use to get a new access_t after expiry
            # expires_at: access_t expiry time [secs since unix epoch UTC]
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    id BIGINT PRIMARY KEY,
                    access_t TEXT UNIQUE NOT NULL,
                    refresh_t TEXT UNIQUE NOT NULL,
                    expires_at BIGINT NOT NULL
                );
            """)
            # id: discord id
            # username: discord username
            cur.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id BIGINT PRIMARY KEY,
                    username TEXT NOT NULL
                );
            """)
            # id: game name ('simon', 'minesweeper', ...)
            # max_score: max possible score per game
            # rank_order: 'asc' or 'desc'
            cur.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id TEXT PRIMARY KEY,
                    max_score INT NOT NULL,
                    rank_order TEXT NOT NULL
                 );
            """)
            # hscore: all-time highscore (IS NULL TO BE INIT'D)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS highscores (
                    player_id BIGINT REFERENCES players(id) ON DELETE CASCADE,
                    game_id TEXT REFERENCES games(id) ON DELETE CASCADE,
                    hscore INT,
                    PRIMARY KEY (player_id, game_id)
                 );
            """)
            # score: daily score that resets every 24h
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    player_id BIGINT REFERENCES players(id) ON DELETE CASCADE,
                    game_id TEXT REFERENCES games(id) ON DELETE CASCADE,
                    score INT DEFAULT 0,
                    PRIMARY KEY (player_id, game_id)
                 );
            """)
            # to track when the rankings should be announced
            # time: TIMESTAMP in UTC for standarization
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reset_time (
                    id INT PRIMARY KEY DEFAULT 1,
                    time TIMESTAMPTZ,
                    streak INT DEFAULT 0
                );
            """)
        conn.commit()
    finally:
        db.close_conn()


#================================= LOGIN/AUTH ====================================
# redirects straight to discord OAuth2
@app.route('/login')
def login():
    init_reset_time()
    # encoded cuz it just be like that
    encoded_url = quote(app.config['REDIR_URI'], safe="")
    # scope: whatever perms selected on the dev website
    # prompt: none/consent, where none doesn't keep asking for auth once auth'd
    return redirect("https://discord.com/oauth2/authorize"
                    f"?client_id={app.config['CLIENT_ID']}"
                    "&response_type=code"
                    f"&redirect_uri={encoded_url}"
                    "&scope=identify"
                    "&prompt=none"
    )


# methods: allowed HTTP requests from client, default 'GET'
# GET contains data in the url (i.e. ?param=data)
# POST sends data through body
# both can be seen if not using HTTPS
@app.route('/auth', methods=['GET'])
def auth():
    session.clear()
    # could have more args so cant use /auth/<code>
    code = request.args.get('code')
    if not code:
        return "Error: No code in given by Discord", 400

    # gets an access token to get user deets
    r = exchange_code(code)
    access_t = r['access_token']
    # access tokens expire so refresh tokens are used to get a new one
    refresh_t = r['refresh_token']
    # expires_in is given in secs so add now in secs
    expires_at = r['expires_in'] + int(time.time())

    r = get_user_deets(access_t)
    session['id'] = r['id']
    session['username'] = r['username']
    store_tokens(r['id'], access_t, refresh_t, expires_at)

    conn = db.get_conn()
    with conn.cursor() as cur:
        # store deets
        # prevents SQL injection this way
        cur.execute("""
            insert into players
            values (%s, %s)
            on conflict (id) do update
            set username = excluded.username;
        """, (r['id'], r['username']))
    conn.commit()

    return redirect(url_for('home'))


"""
return:
{
    access_token: ...
    token_type: 'Bearer'
    expires_in: 604800  #secs (7 days)
    refresh_token: ...
    scope: 'identify'
}
"""
def exchange_code(code):
    # redirect_uri needs to match exactly with the one in the dev page
    # url will get encoded since sending thru body as data
    data = {'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': app.config['REDIR_URI']
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(f'{app.config['API_ENDPOINT']}/oauth2/token',
                      data=data,
                      headers=headers,
                      auth=(app.config['CLIENT_ID'], app.config['CLIENT_SECRET'])
    )
    r.raise_for_status()
    return r.json()


# return: identical to exchange_code()
def refresh_token(refresh_token):
    data = {'grant_type': 'refresh_token',
            'refresh_token': refresh_token
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(f'{app.config['API_ENDPOINT']}/oauth2/token',
                      data=data,
                      headers=headers,
                      auth=(app.config['CLIENT_ID'], app.config['CLIENT_SECRET'])
    )
    r.raise_for_status()
    return r.json()


"""
return:
{
    id: ...
    username: ...
    discriminator: digit that differentiations users w/ same username
    ...
}
"""
def get_user_deets(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{app.config['API_ENDPOINT']}/users/@me",
                     headers=headers
    )
    r.raise_for_status()
    return r.json()


def store_tokens(id, access_t, refresh_t, expires_at):
    conn = db.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tokens
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET access_t = EXCLUDED.access_t,
                    refresh_t = EXCLUDED.refresh_t,
                    expires_at = EXCLUDED.expires_at;
            """, (id, access_t, refresh_t, expires_at))
        conn.commit()
    finally:
        db.close_conn()


# returns either the old access_t or a new one if expired by refreshing
def get_access_token(id):
    conn = db.get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                select access_t, refresh_t, expires_at from tokens
                where id = %s;
            """, (id,))
            row = cur.fetchone()
            if row is None:
                return "Discord user not found", 400
            # if now has passed expire time - 60s
            if row['expires_at'] - 60 <= int(time.time()):
                r = refresh_token(row['refresh_t'])
                access_t = r['access_token']
                expires_at = r['expires_in'] + int(time.time())
                store_tokens(id, access_t, r['refresh_token'], expires_at)
                return access_t
            else:
                return row['access_t']
    finally:
        db.close_conn()


#================================= GAME =================================
# game selection menu
@app.route('/')
def home():
    return render_template('home.html')


# <param> is required in the route to be captured
@app.route('/play/<game_id>', methods=['GET'])
def play(game_id):
    if game_id not in app.config['GAMES']:
        return 'Game not found', 404
    db_utils.init_games_db(game_id)
    db_utils.init_highscores_db(session['id'], game_id)
    db_utils.init_scores_db(session['id'], game_id)
    init_scores(game_id)
    init_hscores(game_id)
    return render_template(f'{game_id}.html')


# ensures 2d session vars are initialized since not automatic
def init_scores(game_id):
    if 'score' not in session:
        session['score'] = {}
    if game_id not in session['score']:
        session['score'][game_id] = {}


def init_hscores(game_id):
    if 'hscore' not in session:
        session['hscore'] = {}
    if game_id not in session['hscore']:
        session['hscore'][game_id] = {}


# =================================== API ===================================
# UPSERT: successive calls shouldnt do anything
def init_reset_time():
    conn = db.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                insert into reset_time (id, time)
                values (1, now() + interval '2 hours')
                on conflict (id) do nothing;
            """)
            conn.commit()
        return jsonify(None)
    finally:
        db.close_conn()


# bot has a background scheduler that pings every hour for rankings
# pinging method only accepts status 200
@app.route('/api/rankings')
def get_daily_rankings():
    conn = db.get_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("select time from reset_time;")
        row = cur.fetchone()
        # reset time only exists if user clicked on login
        # so return 404 Not Found so bot can ignore
        if row is None:
            return jsonify(error='Reset time uninitialized'), 404

        # if before reset time, 204 No Content
        reset_t = row['time']
        if datetime.now(timezone.utc) <= reset_t:
            return jsonify(None), 204

        # else do things
        cur.execute("""
            select
                game_id,
                player_id,
                score,
                dense_rank() over (
                    partition by game_id
                    order by
                        case
                            when rank_order = 'asc' then score
                            else -score
                        end
                ) as rank
            from scores join games g
            on game_id = g.id;
        """)
        # fetchall returns [] or [...], never None
        rows = cur.fetchall()
        # if rows == [], not a single soul has played a game today
        # b/c scores db gets deleted every 24h to be refilled
        # so delete reset time to be init'd later
        if not rows:
            cur.execute("truncate table reset_time;")
            conn.commit()
            return jsonify(None), 204

        # else structure rankings in appropriate format
        games = {}
        for r in rows:
            games.setdefault(r['game_id'], []).append({
                'id': r['player_id'],
                'score': r['score'],
                'rank': r['rank'],
            })
        rankings = [{'game': gid, 'players': plist} for gid, plist in games.items()]

        # delete daily scores
        cur.execute("truncate table scores;")
        # update daily reset time & streak
        cur.execute("""
            update reset_time
            set time = now() + interval '2 hours',
                streak = streak + 1;
        """)
        conn.commit()

        # get max scores per game
        cur.execute("select id, max_score from games;")
        games = cur.fetchall()
        if not games:
            return jsonify(error='No games found'), 404
        max_scores = {}
        for game in games:
            max_scores[game['id']] = game['max_score']

        # by this point, streak should be init'd
        cur.execute("select streak from reset_time;")
        streak = cur.fetchone()['streak']

        return jsonify(rankings=rankings, max_scores=max_scores, streak=streak)


#=============================== MAIN ================================
if __name__ == '__main__':
    try:
        # ssl_context makes the app run with HTTPS
        app.run(host='127.0.0.1',
                port=5000,
                ssl_context=('cert/127.0.0.1.pem', 'cert/127.0.0.1-key.pem'),
                debug=True)
    finally:
        db.close_all()

