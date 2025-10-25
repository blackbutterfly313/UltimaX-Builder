#!/data/data/com.termux/files/usr/bin/python
# web_termux.py — Local Web UI for Termux AI CoPilot (with memory)
# Flask + SQLite memory context + llama.cpp chat API
# Access via http://127.0.0.1:8082

from flask import Flask, request, jsonify, render_template_string
import requests, json, os, sqlite3, time

app = Flask(__name__)

# === CONFIG ===
LLAMA_URL = "http://127.0.0.1:8080/v1/chat/completions"
DB_PATH = os.path.expanduser("~/copilot_memory.db")

# === DATABASE SETUP ===
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            ts REAL
        )
        """)
init_db()

def get_memory(limit=10):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("SELECT role, content FROM memory ORDER BY id DESC LIMIT ?", (limit,))
        data = cur.fetchall()
    return list(reversed(data))

def add_message(role, content):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO memory (role, content, ts) VALUES (?, ?, ?)",
                     (role, content, time.time()))
        conn.commit()

# === FRONTEND HTML ===
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Termux CoPilot</title>
<style>
body { font-family: monospace; background: #0e0e0e; color: #eee; margin: 0; }
#chat { padding: 1em; height: 85vh; overflow-y: auto; white-space: pre-wrap; }
#input { position: fixed; bottom: 0; width: 100%; background: #111; padding: 0.5em; display: flex; }
textarea { flex: 1; background: #000; color: #eee; border: none; resize: none; height: 2.5em; padding: 0.5em; }
button { background: #333; color: #eee; border: none; padding: 0.5em 1em; margin-left: 0.5em; }
button:hover { background: #555; cursor: pointer; }
</style>
</head>
<body>
<div id="chat"></div>
<div id="input">
  <textarea id="user" placeholder="Ask your CoPilot..."></textarea>
  <button onclick="send()">Send</button>
</div>
<script>
async function send() {
  const user = document.getElementById('user');
  const text = user.value.trim();
  if(!text) return;
  user.value = '';
  const chat = document.getElementById('chat');
  chat.innerHTML += "\\n🧑‍💻 You: " + text + "\\n";
  chat.scrollTop = chat.scrollHeight;
  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: text})
    });
    const data = await res.json();
    chat.innerHTML += "🤖 CoPilot: " + data.reply + "\\n";
  } catch(e) {
    chat.innerHTML += "⚠️ Error: " + e + "\\n";
  }
  chat.scrollTop = chat.scrollHeight;
}
window.onload = async () => {
  const res = await fetch('/history');
  const data = await res.json();
  const chat = document.getElementById('chat');
  data.history.forEach(m => {
    const prefix = m.role === 'user' ? '🧑‍💻 You: ' : '🤖 CoPilot: ';
    chat.innerHTML += prefix + m.content + "\\n";
  });
  chat.scrollTop = chat.scrollHeight;
};
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/history")
def history():
    mem = get_memory(30)
    return jsonify({"history": [{"role": r, "content": c} for r, c in mem]})

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    add_message("user", user_message)

    context = get_memory(10)
    messages = [{"role": r, "content": c} for r, c in context]

    payload = {
        "model": "local-copilot",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 512
    }

    try:
        res = requests.post(LLAMA_URL, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        data = res.json()
        reply = data["choices"][0]["message"]["content"]
    except Exception as e:
        reply = f"Error contacting model: {e}"

    add_message("assistant", reply)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8082))
    print(f"🚀 CoPilot Web UI running at http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port)
