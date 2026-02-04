# ================== SELVA PANEL – FULL WEBSITE ==================
# Flask single-file project
# Features:
# Intro (5s) – Login – Roles (Owner/Admin/User)
# Search by last 3 digits – File manager – Numbers by country
# Telethon script is NOT included (as requested)

from flask import Flask, request, redirect, url_for, session, render_template_string, send_from_directory
import os

app = Flask(__name__)
app.secret_key = "SELVA_SECRET_KEY"

# ================== USERS ==================
USERS = {
    "mohaymen": {"password": "mohaymen", "role": "owner"},
    "selvaaapanell": {"password": "selvaaapanell", "role": "admin"},
    "selvaaapanelll": {"password": "selvaaapanelll", "role": "admin"},
}

# ================== STORAGE ==================
BASE_DIR = os.path.dirname(__file__)
UPLOADS = os.path.join(BASE_DIR, "uploads")
NUMBERS = os.path.join(BASE_DIR, "numbers")
os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(NUMBERS, exist_ok=True)

MESSAGES = []  # example: {"text": "Your OTP is 123", "last3": "123"}

# ================== INTRO ==================
INTRO = """
<!DOCTYPE html>
<html>
<head>
<title>SELVA</title>
<style>
body{
margin:0;height:100vh;background:url('https://i.ibb.co/m1jd1Hx/image.png') center/cover;
display:flex;align-items:center;justify-content:center;color:white;font-family:Arial;
}
.overlay{background:rgba(0,0,0,0.6);padding:60px;border-radius:20px;box-shadow:0 0 40px #38bdf8;text-align:center}
.logo{width:180px;height:180px;border-radius:50%;background:url('https://i.ibb.co/m1jd1Hx/image.png') center/cover;margin:auto;box-shadow:0 0 30px #38bdf8}
h1{margin-top:20px;letter-spacing:5px}
</style>
<script>
setTimeout(()=>{window.location='/login'},5000)
</script>
</head>
<body>
<div class="overlay">
<div class="logo"></div>
<h1>S E L V A Massage ⚡</h1>
</div>
</body>
</html>
"""

# ================== LOGIN ==================
LOGIN = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body style="background:#020617;color:white;font-family:Arial;text-align:center;padding-top:120px">
<h2>Login</h2>
<form method="post">
<input name="username" placeholder="Username"><br><br>
<input name="password" type="password" placeholder="Password"><br><br>
<button>Login</button>
</form>
<br>
<a href="https://t.me/selva_number" style="color:#38bdf8">Main channel</a>
</body>
</html>
"""

# ================== DASHBOARD ==================
DASH = """
<!DOCTYPE html>
<html>
<head><title>Dashboard</title></head>
<body style="background:#020617;color:white;font-family:Arial;padding:20px">
<h2>Welcome {{user}} ({{role}})</h2>

<form method="get" action="/search">
<input name="q" placeholder="Last 3 digits">
<button>بحث</button>
</form>

<br>
<a href="/files">My number file</a> |
<a href="/numbers">My number</a> |
<a href="/logout">Logout</a>

{% if role in ['owner','admin'] %}
<hr>
<h3>Admin Panel</h3>
<form method="post" action="/add_user">
<input name="u" placeholder="Username">
<input name="p" placeholder="Password">
<button>Add User</button>
</form>
<br>
<form method="post" enctype="multipart/form-data" action="/upload">
<input type="file" name="file">
<button>Upload File</button>
</form>
{% endif %}

{% if role=='owner' %}
<hr>
<h3>All Users</h3>
<ul>{% for u in users %}<li>{{u}}</li>{% endfor %}</ul>
{% endif %}
</body>
</html>
"""

# ================== ROUTES ==================
@app.route('/')
def intro():
    return render_template_string(INTRO)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=request.form['username']; p=request.form['password']
        if u in USERS and USERS[u]['password']==p:
            session['user']=u
            return redirect('/dashboard')
    return render_template_string(LOGIN)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    u=session['user']
    return render_template_string(DASH, user=u, role=USERS[u]['role'], users=USERS.keys())

@app.route('/add_user', methods=['POST'])
def add_user():
    u=session['user']
    if USERS[u]['role'] in ['owner','admin']:
        USERS[request.form['u']]={"password":request.form['p'],"role":"user"}
    return redirect('/dashboard')

@app.route('/upload', methods=['POST'])
def upload():
    u=session['user']
    if USERS[u]['role'] in ['owner','admin']:
        f=request.files['file']
        f.save(os.path.join(UPLOADS,f.filename))
    return redirect('/dashboard')

@app.route('/files')
def files():
    return "<br>".join([f"<a href='/download/{f}'>{f}</a>" for f in os.listdir(UPLOADS)])

@app.route('/download/<name>')
def download(name):
    return send_from_directory(UPLOADS,name,as_attachment=True)

@app.route('/numbers')
def numbers():
    html="<h2>Countries</h2>"
    for c in os.listdir(NUMBERS):
        html+=f"<h3>{c}</h3><pre>{open(os.path.join(NUMBERS,c)).read()}</pre>"
    return html

@app.route('/search')
def search():
    q=request.args.get('q','')
    res=[m['text'] for m in MESSAGES if m['last3']==q]
    return '<br>'.join(res) if res else 'No results'

@app.route('/logout')
def logout():
    session.clear(); return redirect('/login')

# ================== RUN ==================
if __name__=='__main__':
    app.run(host='0.0.0.0',port=5000)
