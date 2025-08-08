from flask import Flask, session, jsonify, request, render_template_string
import random
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # for session; in prod use a fixed secret

# --- HTML/JS frontend template ---
PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Simon Says (Flask)</title>
  <style>
    body { background: #111; color: #eee; font-family: sans-serif; text-align: center; }
    #board { display: grid; grid-template-columns: repeat(2, 150px); grid-gap: 15px; margin: 20px auto; }
    .pad {
      width: 150px; height: 150px; border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-weight: bold; font-size: 1.1rem; cursor: pointer;
      user-select: none; position: relative;
      box-shadow: 0 0 10px rgba(255,255,255,0.1);
    }
    .flash {
      filter: brightness(2);
      transition: filter 0.2s;
    }
    #controls { margin: 10px; }
    button { padding: 10px 20px; font-size: 1rem; border: none; border-radius: 6px; cursor: pointer; }
    #status { margin-top: 8px; }
  </style>
</head>
<body>
  <h1>Simon Says</h1>
  <div id="score">Score: 0</div>
  <div id="status">Click Start to play</div>
  <div id="board">
    <div class="pad" id="red" style="background: red;">Red</div>
    <div class="pad" id="green" style="background: green;">Green</div>
    <div class="pad" id="blue" style="background: blue;">Blue</div>
    <div class="pad" id="yellow" style="background: yellow;">Yellow</div>
  </div>
  <div id="controls">
    <button id="start">Start Game</button>
  </div>

<script>
const pads = ["red","green","blue","yellow"];
let accepting = false;

function flashPad(color) {
  const el = document.getElementById(color);
  return new Promise(res => {
    el.classList.add("flash");
    setTimeout(() => {
      el.classList.remove("flash");
      setTimeout(res, 150);
    }, 300);
  });
}

async function playSequence(seq) {
  document.getElementById("status").innerText = "Watch the pattern...";
  accepting = false;
  for (const color of seq) {
    await flashPad(color);
  }
  document.getElementById("status").innerText = "Your turn!";
  accepting = true;
}

async function fetchSequence() {
  const resp = await fetch("/sequence");
  return resp.json();
}

async function startGame() {
  const resp = await fetch("/start", {method: "POST"});
  const body = await resp.json();
  document.getElementById("score").innerText = "Score: " + body.score;
  await playSequence(body.sequence);
}

async function submitChoice(color) {
  if (!accepting) return;
  accepting = false;
  const resp = await fetch("/play", {
    method: "POST",
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({choice: color})
  });
  const body = await resp.json();
  document.getElementById("score").innerText = "Score: " + body.score;
  if (body.status === "ok_next") {
    document.getElementById("status").innerText = "Correct! Next round...";
    await new Promise(r => setTimeout(r, 800));
    await playSequence(body.sequence);
  } else if (body.status === "continue") {
    // waiting for more input in current round
    accepting = true;
    document.getElementById("status").innerText = "Keep going...";
  } else if (body.status === "game_over") {
    document.getElementById("status").innerText = "Game Over! Final Score: " + body.score;
  }
}

document.getElementById("start").addEventListener("click", startGame);
pads.forEach(color => {
  document.getElementById(color).addEventListener("click", () => {
    flashPad(color); // immediate feedback
    submitChoice(color);
  });
});

// attempt to sync if page reloads mid-game
window.addEventListener("load", async () => {
  const data = await fetchSequence();
  if (data.sequence && data.sequence.length) {
    document.getElementById("score").innerText = "Score: " + data.score;
    document.getElementById("status").innerText = "Resume playing";
    await playSequence(data.sequence);
  }
});
</script>
</body>
</html>
"""

# --- Helpers ---

def get_state():
    return {
        "sequence": session.get("sequence", []),
        "user_progress": session.get("user_progress", 0),
        "score": session.get("score", 0)
    }

def reset_state():
    session["sequence"] = []
    session["user_progress"] = 0
    session["score"] = 0

# --- Routes ---

@app.route("/")
def index():
    return render_template_string(PAGE)

@app.route("/start", methods=["POST"])
def start():
    reset_state()
    # first round: add one color
    seq = session["sequence"]
    seq.append(random.choice(["red","green","blue","yellow"]))
    session["sequence"] = seq
    session["user_progress"] = 0
    session["score"] = 0
    return jsonify(sequence=seq, score=0)

@app.route("/sequence")
def sequence():
    st = get_state()
    return jsonify(sequence=st["sequence"], score=st["score"])

@app.route("/play", methods=["POST"])
def play():
    data = request.get_json()
    if not data or "choice" not in data:
        return jsonify(error="missing choice"), 400
    choice = data["choice"]
    seq = session.get("sequence", [])
    progress = session.get("user_progress", 0)
    score = session.get("score", 0)

    # Validate current click
    expected = seq[progress]
    if choice != expected:
        # game over
        final = score
        reset_state()
        return jsonify(status="game_over", score=final, sequence=[])
    # correct
    progress += 1
    session["user_progress"] = progress

    if progress == len(seq):
        # round complete, increase score and extend sequence
        score += 1
        session["score"] = score
        session["user_progress"] = 0
        seq.append(random.choice(["red","green","blue","yellow"]))
        session["sequence"] = seq
        return jsonify(status="ok_next", score=score, sequence=seq)
    else:
        # still in current round
        return jsonify(status="continue", score=score)

if __name__ == "__main__":
    app.run(debug=True)

