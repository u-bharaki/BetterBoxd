from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from pathlib import Path

DB_NAME = "movies"
USERS_TABLE_NAME = "users"

def get_db_path():
    db_dir = Path("databases")
    if not db_dir.is_dir():
        return None # Dizin yoksa hata

    db_files = list(db_dir.glob(f"{DB_NAME}_*.db"))

    if not db_files:
        print("[HATA] Veritabanı dosyası bulunamadı.")
        return None

    latest_db = max(db_files, key=os.path.getmtime)
    return str(latest_db)


app = Flask(__name__)
app.secret_key = os.urandom(24)


def get_db_connection():
    db_path = get_db_path()
    if not db_path:
        raise FileNotFoundError("Veritabanı yolu bulunamadı.")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_username(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
        SELECT id, username, password, email, first_name, last_name
        FROM {USERS_TABLE_NAME}
        WHERE username = ?
        """, (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"DB Hatası (get_user): {e}")
        return None

def create_user(username, password, email, first_name, last_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
        INSERT INTO {USERS_TABLE_NAME} (username, password, email, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
        """, (username, password, email, first_name, last_name))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"DB Hatası (create_user): {e}")
        return False

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user_by_username(username)

        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            error = 'Hatalı kullanıcı adı veya şifre.'

    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        if get_user_by_username(username):
            error = 'Invalid.'
        elif not all([username, password, email, first_name, last_name]):
            error = 'Tüm alanları doldurun.'
        elif create_user(username, password, email, first_name, last_name):
            return redirect(url_for('login'))
        else:
            error = 'Lütfen tekrar deneyin.'

    return render_template('register.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    username = session['username']

    return f"""
    <!doctype html>
    <title>Ana Sayfa</title>
    <style>
        body {{ font-family: sans-serif; text-align: center; margin-top: 50px; }}
        h1 {{ color: #2ecc71; }}
    </style>
    <p>...</p>
    <br>
    <a href="{url_for('logout')}">Çıkış Yap</a>
    """

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    if get_db_path():
        print(f"[INFO] Kullanılan DB Yolu: {get_db_path()}")
        app.run(debug=True)
    else:
        print("[HATA] Veritabanı dosyası bulunamadı.")