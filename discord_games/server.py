import time
import requests
from urllib.parse import quote

from flask import Flask, session, request, render_template, redirect, url_for
from flask_session import Session

import db
from psycopg2.extras import DictCursor, RealDictCursor

from games.simon import simon_bp


# can only have 1 app instance, which necessitates Blueprints to keep things modular and organized
app = Flask(__name__)
app.config.from_object('config')
# used to sign cookies
app.secret_key = app.config['SECRET_KEY']
# opts: filesystem, redis, memcached, mongodb, sqlalchemy
app.config['SESSION_TYPE'] = 'filesystem'
# remember to incl url prefix in the JS fetches
app.register_blueprint(simon_bp, url_prefix='/simon')
# cached data per user session
Session(app)


# init a pool of conns instead of constantly creating and closing new conns
db.init_app(app)
# b/c db code only works inside url methods
with app.app_context():
    try:
        conn = db.get_conn()
        # DictCursor is faster that RealDictCursor but doesnt return a python dict
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("drop table tokens; drop table sessions; drop table players;")
            cur.execute("""
            CREATE TABLE tokens (
                id BIGINT PRIMARY KEY,
                access_t TEXT UNIQUE NOT NULL,
                refresh_t TEXT UNIQUE NOT NULL,
                expires_at BIGINT NOT NULL
            );
            CREATE TABLE players (
                id BIGINT PRIMARY KEY,
                username TEXT NOT NULL,
                highscore INT DEFAULT 0
            );
            CREATE TABLE sessions (
                id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                player_id BIGINT REFERENCES players(id),
                score INT DEFAULT 0,
                played_at TIMESTAMP DEFAULT NOW()
             );
            """)
            conn.commit()
    finally:
        db.close_conn()


# redirects straight to discord OAuth2
@app.route('/login')
def login():
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
    # could have more args so cant use /auth/<code>
    code = request.args.get('code')
    if not code:
        return "Error: No code in given by Discord", 400

    # get tokens to access user's deets on their behalf
    r = exchange_code(code)
    access_t = r.get('access_token')
    refresh_t = r.get('refresh_token')
    expires_at = r.get('expires_in') + int(time.time())

    # getting discord id and username
    r = get_user_deets(access_t)
    #session['id'] = r.get('id')
    #session['username'] = r.get('username')
    store_tokens(r.get('id'), access_t, refresh_t, expires_at)

    #store deets
    with conn.cursor() as cur:
        cur.execute("""
            insert into players (id, username)
            values (%s, %s)
            on conflict (id) do update
            set username = excluded.username
        """, (r.get('id'), r.get('username')))
        conn.commit()

    return redirect(url_for('home'))


def store_tokens(id, access_t, refresh_t, expires_at):
    conn = db.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tokens (id, access_t, refresh_t, expires_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET access_t = EXCLUDED.access_t,
                    refresh_t = EXCLUDED.refresh_t,
                    expires_at = EXCLUDED.expires_at;
            """, (id, access_t, refresh_t, expires_at))
            conn.commit()
    finally:
        db.close_conn()


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
            if row['expires_at'] <= int(time.time())-60:
                r = refresh_token(row['refresh_t'])
                access_t = r.get('access_token')
                refresh_t = r.get('refresh_token')
                expires_at = r.get('expires_in') + int(time.time())
                store_tokens(id, access_t, refresh_t, expires_at)
                return access_t
            else:
                return row['access_t']
    finally:
        db.close_conn()


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
def refresh_token(refresh_t):
    data = {'grant_type': 'refresh_token',
            'refresh_token': refresh_t
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(f'{app.config['API_ENDPOINT']}/oauth2/token',
                      data=data,
                      headers=headers,
                      auth=(app.config['CLIENT_ID'], app.config['CLIENT_SECRET'])
    )
    r.raise_for_status()
    return r.json()


# game selection menu
@app.route('/')
def home():
    return render_template('home.html')


# <param> is required in the route to be captured
@app.route('/play/<game>', methods=['GET'])
def play(game):
    if game == 'simon':
        return render_template('simon.html')
    elif game == 'minesweeper':
        return render_template('minesweeper.html')
    else:
        return 'Game not found!', 404


if __name__ == '__main__':
    try:
        # ssl_context makes the app run with HTTPS
        app.run(host='127.0.0.1',
                port=5000,
                ssl_context=('cert/127.0.0.1.pem', 'cert/127.0.0.1-key.pem'),
                debug=True)
    finally:
        db.close_all()

