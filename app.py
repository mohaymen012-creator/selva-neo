from flask import Flask, request, redirect, session, send_from_directory
import sqlite3, os

app = Flask(__name__)
app.secret_key = "SELVA_FULL_PANEL"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DB = "database.db"

# ---------------- DATABASE ----------------
def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS files(
        id INTEGER PRIMARY KEY,
        filename TEXT,
        country TEXT)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY,
        content TEXT)""")

    users = [
        ("mohaymen","mohaymen","owner"),
        ("selvaaapanell","selvaaapanell","admin"),
        ("selvaaapanelll","selvaaapanelll","admin")
    ]

    for u in users:
        cur.execute("SELECT id FROM users WHERE username=?", (u[0],))
        if not cur.fetchone():
            cur.execute("INSERT INTO users(username,password,role) VALUES (?,?,?)", u)

    con.commit()
    con.close()

init_db()

# ---------------- STYLE ----------------
STYLE = """
<style>
body{
background:url('https://i.ibb.co/m1jd1Hx/image.jpg') no-repeat center center fixed;
background-size:cover;
color:#0ff;
font-family:Arial;
margin:0;
}
.overlay{
background:rgba(0,0,0,0.8);
min-height:100vh;
padding:20px;
}
.glass{
background:rgba(0,0,0,0.6);
border-radius:15px;
padding:20px;
box-shadow:0 0 20px #0ff;
margin:20px auto;
max-width:500px;
}
input,button{
width:100%;
padding:12px;
margin-top:10px;
background:#000;
border:1px solid #0ff;
color:#0ff;
border-radius:10px;
}
button{
cursor:pointer;
box-shadow:0 0 15px #0ff;
}
button:hover{
background:#0ff;
color:#000;
}
.card{
border:1px solid #0ff;
padding:10px;
margin-top:10px;
border-radius:10px;
box-shadow:0 0 10px #0ff;
}
.topbar{
display:flex;
justify-content:space-between;
align-items:center;
}
.menu{
display:none;
}
.menu a{
display:block;
margin-top:10px;
}
</style>
<script>
function toggleMenu(){
let m=document.getElementById('menu');
m.style.display = m.style.display=='block'?'none':'block';
}
</script>
"""

# ---------------- SPLASH ----------------
@app.route("/")
def splash():
    return f"""
    <html><head>
    <meta http-equiv="refresh" content="5;url=/login">
    {STYLE}
    </head>
    <body>
    <div class="overlay" style="display:flex;align-items:center;justify-content:center">
        <div align="center">
            <h1>S E L V A Massage ⚡</h1>
        </div>
    </div>
    </body></html>
    """

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["username"]
        p=request.form["password"]

        con=sqlite3.connect(DB)
        cur=con.cursor()
        cur.execute("SELECT role FROM users WHERE username=? AND password=?", (u,p))
        r=cur.fetchone()
        con.close()

        if r:
            session["user"]=u
            session["role"]=r[0]
            return redirect("/dashboard")

    return f"""
    <html><head>{STYLE}</head><body>
    <div class="overlay">
    <div class="glass">
        <h2>Login</h2>
        <form method="post">
            <input name="username" placeholder="Username">
            <input name="password" type="password" placeholder="Password">
            <button>Login</button>
        </form>
        <br>
        <a href="https://t.me/selva_number" target="_blank">Main channel</a>
    </div>
    </div>
    </body></html>
    """

# ---------------- DASHBOARD ----------------
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    con=sqlite3.connect(DB)
    cur=con.cursor()

    # search last 3 digits
    result=""
    if request.method=="POST" and "search" in request.form:
        key=request.form["search"]
        cur.execute("SELECT content FROM messages WHERE content LIKE ?",('%'+key,))
        r=cur.fetchone()
        result=r[0] if r else "No result"

    # files
    cur.execute("SELECT id,filename,country FROM files")
    files=cur.fetchall()

    # users (owner only)
    cur.execute("SELECT id,username,role FROM users")
    users=cur.fetchall()

    con.close()

    files_html=""
    for f in files:
        files_html+=f"""
        <div class="card">
        🌍 {f[2]}<br>
        <a href="/download/{f[1]}">Download</a>
        {"<a href='/delete_file/"+str(f[0])+"'> | Delete</a>" if session['role']=='owner' else ""}
        </div>
        """

    users_html=""
    if session["role"]=="owner":
        for u in users:
            users_html+=f"""
            <div class="card">
            {u[1]} ({u[2]})
            <a href="/delete_user/{u[0]}">Delete</a>
            </div>
            """

    return f"""
    <html><head>{STYLE}</head><body>
    <div class="overlay">

    <div class="topbar">
        <h3>Welcome {session['user']}</h3>
        <button onclick="toggleMenu()">⚙️</button>
    </div>

    <div id="menu" class="glass menu">
        <a href="/my_numbers">My number</a>
        <a href="/files">My number file</a>
    </div>

    <div class="glass">
        <form method="post">
            <input name="search" placeholder="Last 3 digits">
            <button>Search</button>
        </form>
        <p>{result}</p>
    </div>

    <div class="glass">
        <h3>Files</h3>
        {files_html}
    </div>

    {"<div class='glass'><h3>Users</h3>"+users_html+"</div>" if session['role']=='owner' else ""}

    <div class="glass">
        <a href="/logout">Logout</a>
    </div>

    </div>
    </body></html>
    """

# ---------------- MY NUMBER (BY COUNTRY) ----------------
@app.route("/my_numbers")
def my_numbers():
    con=sqlite3.connect(DB)
    cur=con.cursor()
    cur.execute("SELECT country,filename FROM files")
    rows=cur.fetchall()
    con.close()

    data={}
    for c,f in rows:
        data.setdefault(c,[]).append(f)

    html=""
    for c,files in data.items():
        html+=f"<h3>{c}</h3>"
        for f in files:
            path=os.path.join(UPLOAD_FOLDER,f)
            if os.path.exists(path):
                with open(path,errors="ignore") as file:
                    for line in file:
                        html+=f"<div class='card'>{line.strip()}</div>"

    return f"<html><head>{STYLE}</head><body><div class='overlay'>{html}</div></body></html>"

# ---------------- FILES PAGE ----------------
@app.route("/files")
def files_page():
    con=sqlite3.connect(DB)
    cur=con.cursor()
    cur.execute("SELECT filename FROM files")
    files=cur.fetchall()
    con.close()

    html=""
    for f in files:
        html+=f"<div class='card'><a href='/download/{f[0]}'>Download {f[0]}</a></div>"

    return f"<html><head>{STYLE}</head><body><div class='overlay'>{html}</div></body></html>"

# ---------------- DELETE ----------------
@app.route("/delete_user/<int:id>")
def delete_user(id):
    if session.get("role")!="owner":
        return redirect("/dashboard")
    con=sqlite3.connect(DB)
    cur=con.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect("/dashboard")

@app.route("/delete_file/<int:id>")
def delete_file(id):
    if session.get("role")!="owner":
        return redirect("/dashboard")
    con=sqlite3.connect(DB)
    cur=con.cursor()
    cur.execute("SELECT filename FROM files WHERE id=?", (id,))
    f=cur.fetchone()
    if f:
        try: os.remove(os.path.join(UPLOAD_FOLDER,f[0]))
        except: pass
        cur.execute("DELETE FROM files WHERE id=?", (id,))
    con.commit()
    con.close()
    return redirect("/dashboard")

# ---------------- DOWNLOAD ----------------
@app.route("/download/<name>")
def download(name):
    return send_from_directory(UPLOAD_FOLDER,name,as_attachment=True)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- RUN ----------------
if __name__=="__main__":
    import os
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
