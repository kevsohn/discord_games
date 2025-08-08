from flask import Flask, request, render_template, redirect, url_for
from games import simon
import secrets

app = Flask(__name__)

# arg is URL path and you define it server-side and match in browser with html id
@app.route('/')
def home():
    return render_template('main.html')

# methods arg defines the allowed HTTP requests from the browser to respond to
# expect POST or GET?
# GET has params in url, POST sends through body, both can be seen if not HTTPS
@app.route('/game_dir', methods=['POST'])
def redirect_to_game():
    game = request.form.get('game')
    # the 1st arg in url_for specifies func name and gets the assoc url
    return redirect(url_for('play', game))

@app.route('games/<game>')
def play(game):
    if game == 'simon_says':
        # now expects async funcs so should this be await?
        # i think simon just takes over
        simon.start()
        return render_template('simon.html')
    #elif game == 'minesweeper':
    #    minesweeper.start()
    else:
        return 'Game not found!', 404

if __name__ == '__main__':
    app.run(debug=True)

