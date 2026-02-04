from flask import (
    Flask, render_template_string, request,
    redirect, url_for, send_from_directory, jsonify, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)
import os
import re
from datetime import datetime
import telethon
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import threading
import time
import asyncio
import base64

# ================== CONFIG ==================
app = Flask(__name__)
app.secret_key = "SELVA_SUPER_SECRET"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# =============== OWNER ACCOUNT ===============
OWNER_USERNAME = "mohaymen"
OWNER_PASSWORD = "mohaymenn"

# =============== SPECIAL ACCOUNTS ===============
SPECIAL_ACCOUNTS = {
    "selvapanel1": {
        "password": "selvapanel1",
        "permissions": ["create_accounts"]
    },
    "selvapanel2": {
        "password": "selvapanel2",
        "permissions": ["create_accounts"]
    }
}

# =============== TELEGRAM CONFIG ===============
TELEGRAM_API_ID = 39864754
TELEGRAM_API_HASH = "254da5354e8595342d963ef27049c772"
TELEGRAM_CHANNEL_ID = -1003808609180
TELEGRAM_SESSION = "ko"

# Global variable for Telegram client
telegram_client = None
telegram_running = False

# ================== MODELS ==================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    created_by = db.Column(db.String(50))

class NumberFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(50))
    filename = db.Column(db.String(200))

class OTPMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    time = db.Column(db.String(50))
    otp_code = db.Column(db.String(20))
    phone_number = db.Column(db.String(50))

class TelegramBot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bot_token = db.Column(db.String(200))
    group_id = db.Column(db.String(100))
    created_by = db.Column(db.String(50))
    created_at = db.Column(db.String(50))
    status = db.Column(db.String(20), default="stopped")

# ================== LOGIN ==================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================== HELPER FUNCTIONS ==================
def extract_numbers_from_file(file_path):
    """Extract phone numbers from a file"""
    numbers = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            phone_pattern = r'(\+?\d[\d\s\-\(\)]{7,}\d)'
            found_numbers = re.findall(phone_pattern, content)
            numbers = [re.sub(r'\D', '', num) for num in found_numbers if len(re.sub(r'\D', '', num)) >= 10]
    except Exception as e:
        print(f"Error reading file: {e}")
    return numbers

def extract_otp_from_message(message):
    """Extract OTP code from message"""
    otp_pattern = r'\b\d{4,8}\b'
    matches = re.findall(otp_pattern, message)
    return matches[0] if matches else None

def extract_phone_from_message(message):
    """Extract phone number from message"""
    phone_pattern = r'(\+?\d[\d\s\-\(\)]{7,}\d)'
    matches = re.findall(phone_pattern, message)
    return matches[0] if matches else None

async def telegram_listener():
    """Listen to Telegram channel and extract OTP messages"""
    global telegram_client, telegram_running
    
    try:
        client = TelegramClient(StringSession(TELEGRAM_SESSION), 
                               TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await client.start()
        telegram_client = client
        
        entity = await client.get_entity(TELEGRAM_CHANNEL_ID)
        
        while telegram_running:
            messages = await client.get_messages(entity, limit=10)
            
            for message in reversed(messages):
                if message.text:
                    existing = OTPMessage.query.filter_by(message=message.text).first()
                    if not existing:
                        otp_code = extract_otp_from_message(message.text)
                        phone_number = extract_phone_from_message(message.text)
                        
                        db.session.add(OTPMessage(
                            message=message.text,
                            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            otp_code=otp_code,
                            phone_number=phone_number
                        ))
                        db.session.commit()
            
            await asyncio.sleep(5)
            
    except Exception as e:
        print(f"Telegram error: {e}")
        telegram_running = False

def run_telegram_listener():
    """Run Telegram listener in background"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_listener())

async def send_to_telegram_bot(bot_token, group_id, message):
    """Send message to Telegram bot"""
    try:
        bot_client = TelegramClient(StringSession(f"bot_{bot_token[:10]}"), 
                                   TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await bot_client.start(bot_token=bot_token)
        
        await bot_client.send_message(int(group_id), message)
        await bot_client.disconnect()
        return True
    except Exception as e:
        print(f"Bot sending error: {e}")
        return False

# ================== HTML TEMPLATES ==================
LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
        .login-box { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); width: 300px; }
        h2 { text-align: center; color: #333; margin-bottom: 30px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #5a67d8; }
        .error { color: red; text-align: center; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🔐 Login</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="error">
                    {% for message in messages %}
                        {{ message }}
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
    </div>
</body>
</html>
'''

ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
    <style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: auto; }
        .section { background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2, h3 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; }
        input, select { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 8px 15px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #5a67d8; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        .logout { text-align: right; margin: 20px 0; }
        .logout a { color: #dc3545; text-decoration: none; }
        .flash-message { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logout">
            <a href="/logout">Logout</a>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash-message {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="section">
            <h2>👑 Admin Panel - Welcome {{ current_user.username }}</h2>
        </div>
        
        <div class="section">
            <h3>👤 Create User Account</h3>
            <form method="POST">
                <input type="text" name="new_username" placeholder="Username" required>
                <input type="password" name="new_password" placeholder="Password" required>
                <button type="submit" name="create_account" class="btn-success">Create Account</button>
            </form>
        </div>
        
        <div class="section">
            <h3>🗑️ Delete User Account</h3>
            <form method="POST">
                <select name="user_id">
                    {% for user in users %}
                        {% if user.username != owner_username and user.username not in special_accounts %}
                            <option value="{{ user.id }}">{{ user.username }}</option>
                        {% endif %}
                    {% endfor %}
                </select>
                <button type="submit" name="delete_account" class="btn-danger">Delete Account</button>
            </form>
        </div>
        
        <div class="section">
            <h3>📁 Upload Number File</h3>
            <form method="POST" enctype="multipart/form-data">
                <input type="text" name="country" placeholder="Country" required>
                <input type="file" name="file" required>
                <button type="submit" name="upload_file" class="btn-success">Upload File</button>
            </form>
        </div>
        
        <div class="section">
            <h3>📋 Files List</h3>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Country</th>
                        <th>Filename</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for file in files %}
                    <tr>
                        <td>{{ file.id }}</td>
                        <td>{{ file.country }}</td>
                        <td>{{ file.filename }}</td>
                        <td>
                            <form method="POST" style="display: inline;">
                                <input type="hidden" name="file_id" value="{{ file.id }}">
                                <button type="submit" name="delete_file" class="btn-danger">Delete</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% if files %}
            <form method="POST">
                <button type="submit" name="delete_all" class="btn-danger">Delete All Files</button>
            </form>
            {% endif %}
        </div>
        
        <div class="section">
            <h3>👥 Users List</h3>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Created By</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ user.id }}</td>
                        <td>{{ user.username }}</td>
                        <td>{{ user.created_by if user.created_by else 'System' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: auto; }
        .header { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .section { background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        .file-list, .otp-list { margin: 15px 0; }
        .file-item, .otp-item { padding: 10px; border: 1px solid #ddd; margin: 5px 0; border-radius: 5px; }
        .download-btn { background: #4CAF50; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; }
        .logout { text-align: right; }
        .logout a { color: #dc3545; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logout">
                <a href="/logout">Logout</a>
            </div>
            <h2>📊 Dashboard - Welcome {{ current_user.username }}</h2>
        </div>
        
        <div class="section">
            <h3>📁 Available Files</h3>
            <div class="file-list">
                {% if files %}
                    {% for file in files %}
                    <div class="file-item">
                        <strong>{{ file.filename }}</strong> ({{ file.country }})
                        <a href="/download/{{ file.filename }}" class="download-btn">Download</a>
                    </div>
                    {% endfor %}
                {% else %}
                    <p>No files available.</p>
                {% endif %}
            </div>
        </div>
        
        <div class="section">
            <h3>📨 Recent OTP Messages</h3>
            <div class="otp-list">
                {% if otps %}
                    {% for otp in otps %}
                    <div class="otp-item">
                        <div><strong>Time:</strong> {{ otp.time }}</div>
                        <div><strong>OTP:</strong> {{ otp.otp_code if otp.otp_code else 'N/A' }}</div>
                        <div><strong>Phone:</strong> {{ otp.phone_number if otp.phone_number else 'N/A' }}</div>
                        <div>{{ otp.message }}</div>
                    </div>
                    {% endfor %}
                {% else %}
                    <p>No OTP messages received yet.</p>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
'''

SETTINGS_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Settings Panel</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); min-height: 100vh; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; }
        .settings-menu { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .welcome { text-align: center; margin-bottom: 30px; }
        .menu-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .menu-item { background: #f8f9fa; padding: 25px; border-radius: 10px; text-align: center; border: 2px solid transparent; transition: all 0.3s; cursor: pointer; }
        .menu-item:hover { border-color: #667eea; transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .menu-item a { text-decoration: none; color: #333; display: block; }
        .menu-icon { font-size: 40px; margin-bottom: 15px; }
        .menu-title { font-size: 20px; font-weight: bold; margin-bottom: 10px; }
        .menu-desc { color: #666; font-size: 14px; }
        .logout { text-align: center; margin-top: 30px; }
        .logout a { color: #dc3545; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="settings-menu">
            <div class="welcome">
                <h1>⚙️ Settings Panel</h1>
                <p>Welcome, <strong>{{ current_user.username }}</strong></p>
            </div>
            
            <div class="menu-grid">
                <div class="menu-item" onclick="window.location.href='/my_numbers'">
                    <div class="menu-icon">📱</div>
                    <div class="menu-title">My Numbers</div>
                    <div class="menu-desc">Extract and view phone numbers from files</div>
                </div>
                
                <div class="menu-item" onclick="window.location.href='/my_number_files'">
                    <div class="menu-icon">📁</div>
                    <div class="menu-title">My Number Files</div>
                    <div class="menu-desc">Manage and download number files</div>
                </div>
                
                <div class="menu-item" onclick="window.location.href='/my_otp'">
                    <div class="menu-icon">📨</div>
                    <div class="menu-title">My OTP</div>
                    <div class="menu-desc">Telegram OTP listener and messages</div>
                </div>
                
                <div class="menu-item" onclick="window.location.href='/create_bot'">
                    <div class="menu-icon">🤖</div>
                    <div class="menu-title">Create Bot</div>
                    <div class="menu-desc">Create Telegram bot for OTP forwarding</div>
                </div>
                
                <div class="menu-item" onclick="window.location.href='/create_user'">
                    <div class="menu-icon">👤</div>
                    <div class="menu-title">Create User</div>
                    <div class="menu-desc">Create new user accounts</div>
                </div>
            </div>
            
            <div class="logout">
                <a href="/logout">Logout</a>
            </div>
        </div>
    </div>
</body>
</html>
'''

MY_NUMBERS_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>My Numbers</title>
    <style>
        body { font-family: Arial; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: auto; }
        .header { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .back-btn { background: #6c757d; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; display: inline-block; margin-bottom: 20px; }
        .country-section { background: white; padding: 20px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .numbers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin-top: 15px; }
        .number-item { background: #e9ecef; padding: 10px; border-radius: 5px; font-family: monospace; }
        .country-header { display: flex; justify-content: space-between; align-items: center; }
        .count
