from flask import Flask, request, redirect
import sqlite3

app = Flask(__name__)

DB_PATH = "movies_21-11-2025__11-36-42.db"   # ← senin DB yolun (gerekirse değiştirirsin)

@app.route("/create_user", methods=["POST"])
def create_user():
    username = request.form["username"]
    email = request.form["email"]
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    password = request.form["password"]   # HASH yapılacak (sonra ekleriz)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

        # Username kontrol
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    existing_username = cursor.fetchone()

    # Email kontrol
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    existing_email = cursor.fetchone()

    if exists_user or exists_email:
        conn.close()
        return {"success": False,
                "message": "Username or Email has already been taken."}

    cursor.execute("""
        INSERT INTO users (username, password, email, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
    """, (username, password, email, first_name, last_name))

    conn.commit()
    conn.close()

    return redirect("/account_created")  # kullanıcıya success ekranı

@app.route("/account_created")
def account_created():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset='UTF-8'>
        <title>Account Created</title>
        <style>
            body {
                background-color: #0d0d0d;
                color: white;
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .box {
                background-color: #141414;
                padding: 40px;
                width: 420px;
                text-align: center;
                border-radius: 10px;
                border: 1px solid #333;
            }
            .title {
                font-size: 26px;
                font-weight: bold;
                margin-bottom: 20px;
            }
            .btn {
                width: 100%;
                padding: 12px;
                background-color: #00cc66;
                border: none;
                color: white;
                font-size: 16px;
                border-radius: 6px;
                cursor: pointer;
                margin-top: 25px;
            }
            .btn:hover {
                background-color: #00e673;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <div class="title">Account created successfully!</div>
            <button class="btn" onclick="window.location.href='login.html'">Login</button>
        </div>
    </body>
    </html>
    """

    
if __name__ == "__main__":
    app.run(debug=True)
