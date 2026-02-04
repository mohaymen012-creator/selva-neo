# Selva Panel – Single File Full Script
# Flask + Telethon + Multi Bot Groups (OTP Only)

import os
import re
import sqlite3
import threading
import requests
from datetime import datetime
from flask import Flask, request, redirect, session, render_template_string, abort
from telethon import TelegramClient, events

# ================= CONFIG =================
APP_ID = 39864754
APP_HASH = "254da5354e8595342d963ef27049c772"
CHANNEL_ID = -1003808609180
SESSION_NAME = "ko"
SECRET_KEY = "selva-secret"
DB = "selva.db"
UPLOAD_DIR = "uploads"

OWNER = {"username": "mohaymen", "password": "mohaymen"}
ADMINS = {
    "selvaaapanell": "selvaaapanell",
    "selvaaapanelll": "selvaaapanelll"
}

# ================= INIT =================
app = Flask(__name__)
app.secret_key = SECRET_KEY
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ================= DB =================
def db():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    c = db()
    cur = c.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, content TEXT, last3 TEXT, created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS files(id INTEGER PRIMARY KEY, country TEXT, filename TEXT, path TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS bot_links(id INTEGER PRIMARY KEY, user TEXT, bot_token TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS bot_groups(id INTEGER PRIMARY KEY, bot_id INTEGER, chat_id TEXT)")

    # owner
    cur.execute("INSERT OR IGNORE INTO users(username,password,role) VALUES(?,?,?)",
                (OWNER['username'], OWNER['password'], 'owner'))
    # admins
    for u, p in ADMINS.items():
        cur.execute("INSERT OR IGNORE INTO users(username,password,role) VALUES(?,?,?)", (u, p, 'admin'))
    c.commit()

init_db()

# ================= AUTH =================
def current_user():
    return session.get("user")

def role():
    return session.get("role")

# ================= OTP FILTER =================
OTP_RE = re.compile(r"\b\d{4,8}\b")

def extract_otp(text):
    m = OTP_RE.search(text)
    return m.group(0) if m else None

# ================= TELETHON =================
client = TelegramClient(SESSION_NAME, APP_ID, APP_HASH)

@client.on(events.NewMessage(chats=CHANNEL_ID))
async def handler(event):
    text = event.raw_text
    otp = extract_otp(text)
    if not otp:
        return

    last3 = otp[-3:]
    c = db()
    cur = c.cursor()
    cur.execute("INSERT INTO messages(content,last3,created_at) VALUES(?,?,?)",
                (text, last3, datetime.utcnow().isoformat()))
    c.commit()

    # send to linked bots
    cur.execute("SELECT id, bot_token FROM bot_links")
    bots = cur.fetchall()
    for bot_id, token in bots:
        cur.execute("SELECT chat_id FROM bot_groups WHERE bot_id=?", (bot_id,))
        groups = cur.fetchall()
        for (chat_id,) in groups:
            try:
                requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": text}, timeout=5
                )
            except:
                pass

# ================= WEB =================
HTML = """
<!doctype html>
<html>
<head>
<title>Selva Panel</title>
<style>
body{background:#0b0f19;color:#fff;font-family:sans-serif}
.card{background:#111;padding:20px;margin:20px;border-radius:10px}
input,button{padding:10px;margin:5px;border-radius:5px}
</style>
</head>
<body>
{% if not user %}
<div class=card>
<h2>Login</h2>
<form method=post>
<input name=u placeholder=Username>
<input name=p type=password placeholder=Password>
<button>Login</button>
</form>
</div>
{% else %}
<div class=card>
<h2>Search OTP</h2>
<form method=get action=/search>
<input name=q placeholder="Last 3 digits">
<button>Search</button>
</form>
</div>

<div class=card>
<h3>Link Telegram Bot</h3>
<form method=post action=/bot>
<input name=token placeholder="Bot Token">
<button>Save Bot</button>
</form>
<form method=post action=/group>
<input name=chat placeholder="Chat ID">
<button>Add Group</button>
</form>
</div>

{% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        u = request.form['u']
        p = request.form['p']
        cur = db().cursor()
        cur.execute("SELECT role FROM users WHERE username=? AND password=?", (u,p))
        r = cur.fetchone()
        if r:
            session['user']=u
            session['role']=r[0]
            return redirect('/')
    return render_template_string(HTML, user=current_user())

@app.route('/search')
def search():
    q = request.args.get('q','')
    cur = db().cursor()
    cur.execute("SELECT content FROM messages WHERE last3=? ORDER BY id DESC LIMIT 10", (q,))
    return '<br>'.join([m[0] for m in cur.fetchall()])

@app.route('/bot', methods=['POST'])
def bot():
    if not current_user(): abort(403)
    token = request.form['token']
    c=db();cur=c.cursor()
    cur.execute("DELETE FROM bot_links WHERE user=?", (current_user(),))
    cur.execute("INSERT INTO bot_links(user,bot_token) VALUES(?,?)", (current_user(),token))
    c.commit()
    return redirect('/')

@app.route('/group', methods=['POST'])
def group():
    if not current_user(): abort(403)
    chat = request.form['chat']
    cur=db().cursor()
    cur.execute("SELECT id FROM bot_links WHERE user=?", (current_user(),))
    bot=cur.fetchone()
    if bot:
        cur.execute("INSERT INTO bot_groups(bot_id,chat_id) VALUES(?,?)", (bot[0],chat))
        db().commit()
    return redirect('/')

# ================= RUN =================
def run_web():
    app.run('0.0.0.0',5000)

threading.Thread(target=run_web).start()
client.start()
client.run_until_disconnected()
