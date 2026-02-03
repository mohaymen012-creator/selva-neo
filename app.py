from flask import Flask, request, redirect, session, send_from_directory
import sqlite3, os

app = Flask(__name__)
app.secret_key = "SELVA_NEON_ANIMATIONS"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DB = "database.db"

# ---------------- DATABASE ----------------
def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT,
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

# ---------------- NEON STYLE + ANIMATION ----------------
STYLE = """
<style>
*{box-sizing:border-box}
body{
    margin:0;
    min-height:100vh;
    background:radial-gradient(circle at top,#0ff2,#000 60%);
    color:#0ff;
    font-family:Arial,Helvetica;
    animation:bgMove 8s infinite alternate;
}
@keyframes bgMove{
    from{background-position:0% 0%}
    to{background-position:100% 100%}
}
.center{display:flex;justify-content:center;align-items:center;height:100vh}
.glass{
    background:rgba(0,0,0,.65);
    backdrop-filter:blur(12px);
    border-radius:18px;
    padding:25px;
    width:90%;
    max-width:420px;
    box-shadow:0 0 25px #0ff;
    animation:fadeUp .8s ease;
}
@keyframes fadeUp{
    from{opacity:0;transform:translateY(20px)}
    to{opacity:1;transform:translateY(0)}
}
input,button{
    width:100%;
    padding:13px;
    margin-top:12px;
    background:#000;
    border:1px solid #0ff;
    color:#0ff;
    border-radius:12px;
    outline:none;
    font-size:15px;
}
input:focus{
    box-shadow:0 0 15px #0ff;
}
button{
    cursor:pointer;
    text-transform:uppercase;
    letter-spacing:1px;
    animation:pulse 2s infinite;
}
@keyframes pulse{
    0%{box-shadow:0 0 10px #0ff}
    50%{box-shadow:0 0 25px #0ff}
    100%{box-shadow:0 0 10px #0ff}
}
button:hover{
    background:#0ff;
    color:#000;
}
.card{
    background:#000;
    border:1px solid #0ff;
    border-radius:14px;
    padding:15px;
    margin-top:12px;
    box-shadow:0 0 15px #0ff;
    animation:glow 3s infinite alternate;
}
@keyframes glow{
    from{box-shadow:0 0 10px #0ff}
    to{box-shadow:0 0 30px #0ff}
}
a{color:#0ff;text-decoration:none}
.circle{
    width:160px;height:160px;
    border-radius:50%;
    box-shadow:0 0 35px #0ff;
    animation:spinGlow 6s infinite linear;
}
@keyframes spinGlow{
    0%{transform:rotate(0deg)}
    100%{transform:rotate(360deg)}
}
.result{
    padding:15px;
    border:1px dashed #0ff;
    margin-top:15px;
    animation:flash .5s ease;
}
@keyframes flash{
    from{opacity:0}
    to{opacity:1}
}
</style>
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
    <div class="center">
        <div align="center">
            <img class="circle" src="https://i.ibb.co/m1jd1Hx/image.jpg"><br><br>
            <h2>S E L V A Massage ⚡</h2>
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
    <div class="center">
    <div class="glass">
        <h2>Neon Login</h2>
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

    result=""
    if request.method=="POST":
        key=request.form.get("search","")
        cur.execute("SELECT content FROM messages WHERE content LIKE ?",('%'+key,))
        r=cur.fetchone()
        result=r[0] if r else "❌ No Result Found"

    cur.execute("SELECT filename,country FROM files")
    files=cur.fetchall()
    con.close()

    files_html=""
    for f in files:
        files_html+=f"""
        <div class="card">
            🌍 {f[1]}<br>
            <a href="/download/{f[0]}">⬇ Download</a>
        </div>
        """

    upload=""
    if session["role"]=="owner":
        upload=f"""
        <div class="glass">
            <h3>Owner Upload</h3>
            <form method="post" action="/upload" enctype="multipart/form-data">
                <input name="country" placeholder="Country">
                <input type="file" name="file">
                <button>Upload</button>
            </form>
        </div>
        """

    return f"""
    <html><head>{STYLE}</head><body>

    <div class="glass">
        <h2>Welcome {session['user']}</h2>
        <form method="post">
            <input name="search" placeholder="Last 3 digits">
            <button>Search</button>
        </form>
        {f"<div class='result'>{result}</div>" if result else ""}
    </div>

    <div class="glass">
        <h3>My Number Files</h3>
        {files_html}
    </div>

    {upload}

    <div class="glass">
        <a href="/logout">Logout</a>
    </div>

    </body></html>
    """

# ---------------- UPLOAD ----------------
@app.route("/upload", methods=["POST"])
def upload():
    if session.get("role")!="owner":
        return redirect("/dashboard")

    f=request.files["file"]
    country=request.form["country"]

    f.save(os.path.join(UPLOAD_FOLDER,f.filename))

    con=sqlite3.connect(DB)
    cur=con.cursor()
    cur.execute("INSERT INTO files(filename,country) VALUES (?,?)",(f.filename,country))
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
    app.run(host="0.0.0.0",port=5000)
