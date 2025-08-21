import requests
from urllib.parse import quote

from flask import Flask, session, request, render_template, redirect, url_for
from flask_session import Session

from psycopg2.extras import DictCursor, RealDictCursor
import db

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
            # remove this at some point
            cur.execute("DROP TABLE session_info; DROP TABLE players;")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                discord_id TEXT UNIQUE NOT NULL,
                high_score INT DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS session_info (
                id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                player_id INT REFERENCES players(id),
                score INT DEFAULT 0,
                played_at TIMESTAMP DEFAULT NOW()
             )
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
        return "Error: No code from Discord", 400

    # redirect_uri needs to match exactly with the one in the dev page
    # url will get encoded since sending thru body
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
    #print("status", r.status_code)
    #print("headers", r.headers)
    #print("body", r.text[:500])
    r.raise_for_status()
    r = r.json()

    access_token = r.get('access_token')
    refresh_token = r.get('refresh_token')
    expires_at = r.get('expires_at')

    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{app.config['API_ENDPOINT']}/users/@me",
                     headers=headers
    )
    r.raise_for_status()
    r = r.json()

    session['discord_id'] = r.get('id')
    session['discord_username'] = r.get('username')
    print('id:', r.get('id'), ' user:', r.get('username'))

    #conn = db.get_conn()
    #with conn.cursor(cursor_factory=RealDictCursor) as cur:
    #    cur.execute("""
    #        insert access_token if not exists user_id;
    #        insert refresh_token if not exists;
    #        insert datetime(expires_at) if not exists;
    #    """)
    #    row = cur.fetchone()
    # if row['expires_at'] == datetime.now():
    #   refresh_token(refresh_token)
    #    conn.commit()

    return redirect(url_for('home'))


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

