from flask import Flask, session, request, render_template, redirect, url_for
from flask_session import Session
from secrets import token_urlsafe
import os
import psycopg2 as psql
from psycopg2.extras import RealDictCursor

from games.simon import simon_bp


# can only have 1 app instance, which necessitates Blueprints
# to keep things modular and organized
app = Flask(__name__)
# remember to incl url prefix in the JS fetches
app.register_blueprint(simon_bp, url_prefix='/simon')
# used to sign cookies
app.secret_key = token_urlsafe(16)
# opts: filesystem, redis, memcached, mongodb, sqlalchemy
app.config['SESSION_TYPE'] = 'filesystem'
# groups data per sesh
Session(app)

# portable way to get relative path
dname = os.path.dirname(__file__)
fname = os.path.join(dname, 'config.txt')
with open(fname, 'r') as file:
    db_user = file.readline().strip()
db_host = 'localhost'

conn = psql.connect(
        dbname='game_db',
        user=db_user,
        host=db_host,
        cursor_factory=RealDictCursor
)

cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    discord_id TEXT UNIQUE NOT NULL,
    high_score INT DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS session_info (
    id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(id),
    score INT NOT NULL,
    played_at TIMESTAMP DEFAULT NOW()
 )
""")
conn.commit()


# arg: URL path the client-side calls to perform said action
@app.route('/')
def home():
    return render_template('home.html')

# methods: allowed HTTP requests from client
# GET contains data in the url (i.e. ?param1=data1&param2=data2)
# POST sends data through body
# both can be seen if not using HTTPS
@app.route('/get_game', methods=['GET'])
def get_game():
    game = request.args.get('game')
    return redirect(url_for('play', game=game))

# arg: <__param__> in the url is a must
# otherwise, param isnt captured
@app.route('/play/<game>')
def play(game):
    if game == 'simon':
        return render_template('simon.html')
    elif game == 'minesweeper':
        return render_template('minesweeper.html')
    else:
        return 'Game not found!', 404


if __name__ == '__main__':
    app.run(debug=True)

