import psycopg2 as psql
from psycopg2.extras import DictCursor, RealDictCursor

from flask import Flask, session, request, render_template, redirect, url_for
from flask_session import Session

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
# groups data per sesh
Session(app)

# init a pool of conns instead of constantly creating and closing new conns
db.init_app(app)

with app.app_context():
    try:
        conn = db.get_conn()
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("DROP TABLE session_info; DROP TABLE players;")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                discord_id TEXT UNIQUE NOT NULL,
                high_score INT DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS session_info (
                id SERIAL PRIMARY KEY,
                player_id INT REFERENCES players(id),
                score INT DEFAULT 0,
                played_at TIMESTAMP DEFAULT NOW()
             )
            """)
            conn.commit()
    finally:
        db.close_conn()


# arg: URL path the client-side calls to perform said action
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login')
def login():
    return


# methods: allowed HTTP requests from client
# GET contains data in the url (i.e. ?param1=data1&param2=data2)
# POST sends data through body
# both can be seen if not using HTTPS
@app.route('/get_game', methods=['GET'])
def get_game():
    game = request.args.get('game')
    return redirect(url_for('play', game=game))


# arg: <__param__> in the url is a must otherwise param isnt captured
@app.route('/play/<game>')
def play(game):
    if game == 'simon':
        return render_template('simon.html')
    elif game == 'minesweeper':
        return render_template('minesweeper.html')
    else:
        return 'Game not found!', 404


if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        db.close_all()

