from flask import Flask, render_template, g, request, jsonify, session, redirect, url_for
import sqlite3
import os
import uuid
from pathlib import Path
from typing import Optional
from collections import Counter

from user_manager import UserManager

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_NAME = "movies"
USERS_TABLE_NAME = "users"

user_manager: Optional[UserManager] = None

# ----- DATABASE CONNECTION -----

def get_db_path():
    """Databases klasöründeki en güncel 'movies_*.db' dosyasını bulur."""
    base_dir = Path(__file__).parent
    db_dir = base_dir / "../../Data/databases"

    if not db_dir.is_dir():
        db_dir = base_dir

    db_files = list(db_dir.glob(f"{DB_NAME}_*.db"))

    fallback = base_dir / "betterboxd.db"
    if fallback.exists():
        return fallback
    elif db_files:
        latest_db = max(db_files, key=os.path.getmtime)
        return str(latest_db)
    else:
        return None

def get_db():
    """Context Manager: Veritabanı bağlantısını g objesinde saklar ve döndürür."""
    db = getattr(g, '_database', None)
    if db is None:
        db_path = get_db_path()
        if not db_path:
            raise FileNotFoundError("Veritabanı dosyası bulunamadı!")

        db = g._database = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ----- LOGIN - REGISTER -----

def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    wrap.__name__ = f.__name__
    return wrap

@app.route('/')
def index_redirect():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = user_manager.get_user_by_username(username)

        if user_data and user_manager.check_password(user_data, password):
            session['user_id'] = user_data['id']
            session['username'] = user_data['username']
            session['fullname'] = f"{user_data['first_name']} {user_data['last_name']}"
            session['email'] = user_data['email']
            return redirect(url_for('index'))
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

        # 1. Kontrol: Kullanıcı adı alınmış mı?
        if user_manager.get_user_by_username(username):
            error = 'Bu kullanıcı adı zaten alınmış.'

        # 2. Kontrol (YENİ EKLENEN): E-posta adresi sistemde var mı?
        elif user_manager.get_user_by_email(email):
            error = 'Bu e-posta adresiyle zaten bir hesap mevcut.'

        # 3. Kontrol: Alanlar boş mu?
        elif not all([username, password, email, first_name, last_name]):
            error = 'Tüm alanları doldurun.'

        # Her şey tamamsa kullanıcıyı oluştur
        elif user_manager.create_user(username, password, email, first_name, last_name):
            return redirect(url_for('login'))
        else:
            error = 'Kayıt işlemi sırasında bir hata oluştu. Lütfen tekrar deneyin.'

    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    """Kullanıcının oturumunu sonlandırır."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    """Ana Sayfa: Kullanıcı giriş yapmışsa SPA'yı (index.html) yükler."""
    return render_template('index.html', user=session)

# ----- GET -----

@app.route('/api/productions')
def get_all_productions():
    db = get_db()

    page = int(request.args.get('page', 1))
    limit = 50
    offset = (page - 1) * limit

    genres = request.args.get('genres', 'all')
    year = request.args.get('year', 'all')
    sort_by = request.args.get('sort', 'pop')
    letter = request.args.get('letter', 'all')

    count_query_select = """
        SELECT COUNT(*)
    """
    query_select = """
        SELECT p.id, p.title, p.start_year, p.poster_link, 
               p.site_rating
        """
    query = """
        FROM productions p
        """

    params = []
    where_clauses = []

    if letter and letter != 'all':
        if letter == '#':
            where_clauses.append(f"p.title GLOB '[0-9]*'")
        else:
            where_clauses.append("p.title LIKE ?")
            params.append(f"{letter}%")
    if genres and genres != 'all':
        where_clauses.append("p.genres LIKE ?")
        params.append(f'%{genres}%')
    if year and year != 'all':
        where_clauses.append("p.start_year = ?")
        params.append(year)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)


    total_items = db.execute(count_query_select+query, params).fetchone()[0]
    total_pages = (total_items + limit - 1) // limit


    if sort_by == 'rating':
        query += " ORDER BY p.site_rating DESC"
    elif sort_by == 'alpha':
        query += " ORDER BY p.title ASC"
    elif sort_by == 'new':
        query += " ORDER BY p.start_year DESC"
    else:
        query += " ORDER BY p.id DESC"

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    productions = db.execute(query_select+query, params).fetchall()

    return jsonify({
        'productions': [{
            'id': row['id'],
            'title': row['title'],
            'year': row['start_year'],
            'poster': row['poster_link'],
            'rating': round(row['site_rating'], 1) if row['site_rating'] else 0
        } for row in productions],
        'total_pages': total_pages,
        'current_page': page
    })

@app.route('/api/production/<string:prod_id>')
@login_required
def get_production_detail(prod_id):
    db = get_db()
    production = db.execute('SELECT * FROM productions WHERE id = ?', (prod_id,)).fetchone()

    if production is None:
        return jsonify({'error': 'Yapım bulunamadı'}), 404

    director = db.execute('''
        SELECT first_name, last_name FROM contributors 
        WHERE production_id = ? AND role = 'director' LIMIT 1
    ''', (prod_id,)).fetchone()

    response = {
        'id': production['id'],
        'title': production['title'],
        'year': production['start_year'],
        'plot': production['plot'],
        'poster': production['poster_link'],
        'backdrop': production['poster_link'],
        'director': f"{director['first_name']} {director['last_name']}" if director else "Bilinmiyor",
        'imdb_rating': production['imdb_rating'],
        'imdb_votes': production['imdb_votes'],
        'site_rating': production['site_rating'],
        'site_votes': production['site_votes']
    }
    return jsonify(response)

@app.route('/api/production/<string:prod_id>/cast')
@login_required
def get_production_cast(prod_id):
    db = get_db()
    cast_data = db.execute('''
        SELECT first_name, last_name FROM contributors
        WHERE production_id = ? AND role = 'actor'
    ''', (prod_id,)).fetchall()

    return jsonify({
        'cast': [{
            'name': f"{row['first_name']} {row['last_name']}"
        } for row in cast_data],
    })


@app.route('/api/production/<string:prod_id>/reviews')
@login_required
def get_production_reviews(prod_id):
    db = get_db()
    reviews = db.execute('''
        SELECT r.context, r.score, u.username 
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.production_id = ?
        ORDER BY r.id DESC LIMIT 5
    ''', (prod_id,)).fetchall()

    return jsonify([{'author': r['username'], 'score': r['score'], 'text': r['context']} for r in reviews])

@app.route('/api/feed')
@login_required
def get_feed():
    db = get_db()
    current_user_id = session['user_id']

    sql = '''
        SELECT 
            r.score, r.context, u.username, u.first_name, u.last_name,
            p.id as prod_id, p.title, p.poster_link, p.start_year
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        JOIN productions p ON r.production_id = p.id
        JOIN follows f ON f.followed_user_id = u.id
        WHERE f.follower_user_id = ?
        ORDER BY r.id DESC LIMIT 20
    '''
    feed_items = db.execute(sql, (current_user_id,)).fetchall()

    return jsonify([{
        'user': f"{row['first_name']} {row['last_name']}",
        'title': row['title'],
        'year': row['start_year'],
        'poster': row['poster_link'],
        'score': row['score'],
        'review': row['context'],
        'production_id': row['prod_id']
    } for row in feed_items])

@app.route('/api/profile')
@app.route('/api/profile/<string:user_id>')
@login_required
def get_profile(user_id=None):
    if user_id == None:
        user_id = session['user_id']

    db = get_db()

    # 1. Kullanıcı Bilgileri
    user = db.execute(f'SELECT * FROM {USERS_TABLE_NAME} WHERE id = ?', (user_id,)).fetchone()

    if not user:
        return jsonify({'error': 'Kullanıcı bulunamadı'}), 404

    # 2. İstatistikler
    total_watched = db.execute('SELECT COUNT(*) FROM reviews WHERE user_id = ?', (user_id,)).fetchone()[0]
    total_lists = db.execute('SELECT COUNT(*) FROM lists WHERE user_id = ?', (user_id,)).fetchone()[0]

    try:
        followers = db.execute('SELECT COUNT(*) FROM follows WHERE followed_user_id = ?', (user_id,)).fetchone()[0]
        following = db.execute('SELECT COUNT(*) FROM follows WHERE follower_user_id = ?', (user_id,)).fetchone()[0]
    except:
        followers = 0
        following = 0

    # 3. Puan Dağılımı Grafiği İçin Veri
    rating_counts = {i: 0 for i in range(1, 11)}
    ratings_query = db.execute('SELECT score FROM reviews WHERE user_id = ?', (user_id,)).fetchall()
    for row in ratings_query:
        score = int(row['score'])
        if 1 <= score <= 10:
            rating_counts[score] += 1
    rating_distribution = [rating_counts[i] for i in range(1, 11)]

    # 4. Favori Türler Grafiği İçin Veri
    genres_query = db.execute('''
        SELECT p.genres FROM reviews r
        JOIN productions p ON r.production_id = p.id
        WHERE r.user_id = ?
    ''', (user_id,)).fetchall()

    all_genres = []
    for row in genres_query:
        if row['genres']:
            g_list = [g.strip() for g in row['genres'].split(',')]
            all_genres.extend(g_list)

    top_genres = Counter(all_genres).most_common(5)
    genre_labels = [item[0] for item in top_genres]
    genre_data = [item[1] for item in top_genres]

    # 5. Son Aktiviteler
    recent = db.execute('''
        SELECT r.score, r.context, p.title, p.poster_link
        FROM reviews r
        JOIN productions p ON r.production_id = p.id
        WHERE r.user_id = ?
        ORDER BY r.id DESC LIMIT 5
    ''', (user_id,)).fetchall()

    recent_activity = [{'title': r['title'], 'poster': r['poster_link'], 'score': r['score'], 'text': r['context']} for r in recent]

    print(f"""
        'user_id': {user_id},
        'username': {user['username']},
        'fullname': f"{user['first_name']} {user['last_name']}",
        'stats': 'watched': {total_watched}, 'lists': {total_lists}, 'followers': {followers}, 'following': {following},
        'charts': 'rating_data': {rating_distribution}, 'genre_labels': {genre_labels}, 'genre_data': {genre_data},
        'recent_activity': {recent_activity}
    """)

    return jsonify({
        'user_id': user_id,
        'username': user['username'],
        'fullname': f"{user['first_name']} {user['last_name']}",
        'stats': {'watched': total_watched, 'lists': total_lists, 'followers': followers, 'following': following},
        'charts': {'rating_data': rating_distribution, 'genre_labels': genre_labels, 'genre_data': genre_data},
        'recent_activity': recent_activity
    })

@login_required
def get_current_profile():
    return get_profile(session['user_id'])

@app.route('/api/my-lists')
@login_required
def get_my_lists():
    db = get_db()
    current_user_id = session['user_id']

    lists = db.execute('''
        SELECT id, name, production_count
        FROM lists
        WHERE user_id = ?
        ORDER BY name ASC
    ''', (current_user_id,)).fetchall()
    lists_for_json = [dict(row) for row in lists]
    return jsonify([dict(row) for row in lists])

@app.route('/api/list/<list_id>/productions')
@login_required
def get_list_details(list_id):
    db = get_db()
    current_user_id = session['user_id']

    productions = db.execute('''
        SELECT p.id, p.title, p.start_year, p.poster_link, p.imdb_rating
        FROM productions as p 
        JOIN productions_in_lists as pl ON p.id = pl.production_id
        WHERE pl.list_id = ? AND pl.user_id = ?
        GROUP BY p.id
        ORDER BY p.title ASC
    ''', (list_id, current_user_id)).fetchall()

    list_info = db.execute('SELECT name FROM lists WHERE id = ? AND user_id = ?', (list_id, current_user_id)).fetchone()

    return jsonify({
        'list_name': list_info['name'] if list_info else "Unknown List",
        'productions': [{
            'id': row['id'],
            'title': row['title'],
            'year': row['start_year'],
            'poster': row['poster_link'],
            'rating': round(row['imdb_rating'], 1) if row['imdb_rating'] else 0
        } for row in productions]
    })

@app.route('/api/list/<production_id>/lists_status')
@login_required
def get_production_lists_status(production_id):
    try:
        db = get_db()
        current_user_id = session['user_id']

        query = '''
            SELECT
                L.id,
                L.name,
                CASE
                    WHEN PL.list_id IS NOT NULL THEN 1
                    ELSE 0
                END as has_production
            FROM lists L
            LEFT JOIN productions_in_lists as PL 
                ON L.id = PL.list_id AND PL.production_id = ?
            WHERE L.user_id = ?
            ORDER BY L.name ASC
        '''
        results = db.execute(query, (production_id, current_user_id)).fetchall()
        return jsonify([{
            'id': row['id'],
            'name': row['name'],
            'has_production': bool(row['has_production'])
        } for row in results])
    except Exception as e:
        print(f"LİSTE STATUS HATASI: {e}")
        return jsonify({'error': str(e), 'success': False})

@app.route('/api/user/<user_id>/followers')
@login_required
def get_user_followers(user_id):
    db = get_db()

    query = """
        SELECT f.follower_user_id, u.first_name, u.last_name, u.username
        FROM follows as f
        JOIN users as u ON u.id = f.follower_user_id
        WHERE f.followed_user_id = ?
    """
    params = (user_id,)

    followers = db.execute(query, params).fetchall()

    return jsonify([{
        'id': row['follower_user_id'],
        'first_name': row['first_name'],
        'last_name': row['last_name'],
        'username': row['username']
    } for row in followers])


@app.route('/api/user/<user_id>/following')
@login_required
def get_user_followed(user_id):
    db = get_db()

    query = """
        SELECT f.followed_user_id, u.first_name, u.last_name, u.username
        FROM follows as f
        JOIN users as u ON u.id = f.followed_user_id
        WHERE f.follower_user_id = ?
    """
    params = (user_id,)

    following = db.execute(query, params).fetchall()

    return jsonify([{
                       'id': row['followed_user_id'],
                       'first_name': row['first_name'],
                       'last_name': row['last_name'],
                       'username': row['username']
                   } for row in following])

@app.route('/api/search')
@login_required
def search_productions():
    query = request.args.get('q', '')

    if len(query) < 2:
        return jsonify([])

    db = get_db()

    sql = '''
        SELECT id, title, start_year, poster_link, imdb_rating
        FROM productions
        WHERE title LIKE ?
        ORDER BY title ASC
        LIMIT 50
    '''

    results = db.execute(sql, (f'%{query}%',)).fetchall()
    return jsonify([{
        'id': str(row['id']),
        'title': row['title'],
        'year': row['start_year'],
        'poster': row['poster_link'],
        'imdb_rating': row['imdb_rating']
    } for row in results])

# ----- ADD -----

@app.route('/api/review', methods=['POST'])
@login_required
def add_review():
    data = request.json
    db = get_db()
    current_user_id = session['user_id']

    try:
        db.execute('''
            INSERT INTO reviews (user_id, production_id, score, context)
            VALUES (?, ?, ?, ?)
        ''', (current_user_id, data['productionId'], data['score'], data['text']))

        site_rating_data = db.execute('''
            SELECT SUM(score) as site_rating_sum FROM reviews WHERE production_id = ?
        ''', (data['productionId'],)).fetchone()

        site_rating_sum = site_rating_data['site_rating_sum']
        if site_rating_sum is None:
            site_rating = 0.0

        db.execute('''
            UPDATE productions SET site_rating = ROUND(? / (site_votes+1), 1), site_votes = site_votes + 1
            WHERE id = ?
        ''', (site_rating_sum, data['productionId']))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/list/create', methods=['POST'])
@login_required
def add_list():
    data = request.json
    list_name = data['list_name']
    if not list_name:
        return jsonify({'success': False, 'error': 'List Name is required'})

    db = get_db()
    current_user_id = session['user_id']
    new_list_id = str(uuid.uuid4())
    try:
        db.execute('''
            INSERT INTO lists (id, name, user_id, production_count)
            VALUES (?, ?, ?, 0)
        ''', (new_list_id, list_name, current_user_id))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ----- DELETE -----

@app.route('/api/list/<list_id>/delete', methods=['POST'])
@login_required
def delete_list(list_id):
    db = get_db()
    current_user_id = session['user_id']
    list_id = str(list_id)

    check = db.execute('SELECT 1 FROM lists WHERE id = ? AND user_id = ?', (list_id, current_user_id)).fetchone()
    if not check:
        return jsonify({'success': False, 'error': 'Unauthorized transaction'})

    try:
        db.execute('DELETE FROM productions_in_lists WHERE list_id = ? AND user_id = ?', (list_id, current_user_id))
        db.execute('Delete FROM lists WHERE id = ? AND user_id = ?', (list_id, current_user_id))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ----- UPDATE -----

@app.route('/api/list/<list_id>/update', methods=['POST'])
@login_required
def update_list_name(list_id):
    data = request.json
    new_name = data.get('name')
    current_user_id = session['user_id']
    db = get_db()

    if not new_name:
        return jsonify({'success': False, 'error': 'List name is required'})

    try:
        db.execute('''
            UPDATE lists SET name = ?
            WHERE id = ? AND user_id = ?
        ''', (new_name, list_id, current_user_id))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route("/api/update_settings", methods=["POST"])
def api_update_settings():
    if "username" not in session:
        return jsonify({"success": False, "message": "Giriş yapılmamış."}), 401

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Geçersiz istek."})

    current_user = session["username"]

    # Aktif kullanıcıyı DB'den çek
    user = user_manager.get_user_by_username(current_user)
    if not user:
        return jsonify({"success": False, "message": "Kullanıcı bulunamadı."}), 404

    new_username = data.get("new_username", "").strip()
    new_email = data.get("new_email", "").strip()

    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")
    new_password2 = data.get("new_password2", "")

    updated_anything = False

    # ----------- KULLANICI ADI GÜNCELLE -----------------
    if new_username and new_username != current_user:
        if user_manager.get_user_by_username(new_username):
            return jsonify({"success": False, "message": "Bu kullanıcı adı zaten kullanılıyor."})

        try:
            conn = sqlite3.connect(user_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, current_user))
            conn.commit()
            conn.close()

            session["username"] = new_username
            updated_anything = True

        except Exception as e:
            return jsonify({"success": False, "message": f"Kullanıcı adı güncellenemedi: {e}"})

    # ----------- EMAIL GÜNCELLE -----------------
    if new_email and new_email != user["email"]:

        # --- YENİ EKLENEN KONTROL: E-posta formatı (@ var mı?) ---
        if "@" not in new_email:
            return jsonify({"success": False, "message": "Lütfen geçerli bir e-posta adresi giriniz."})

        if user_manager.get_user_by_email(new_email):
            return jsonify({"success": False, "message": "Bu e-posta zaten kullanılıyor."})

        try:
            conn = sqlite3.connect(user_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET email = ? WHERE username = ?", (new_email, session["username"]))
            conn.commit()
            conn.close()

            updated_anything = True

        except Exception as e:
            return jsonify({"success": False, "message": f"E-posta güncellenemedi: {e}"})

    # ----------- ŞİFRE GÜNCELLE -----------------
    if old_password or new_password or new_password2:
        if not old_password:
            return jsonify({"success": False, "message": "Mevcut şifre gerekli."})

        if not user_manager.check_password(user, old_password):
            return jsonify({"success": False, "message": "Mevcut şifre yanlış."})

        if new_password != new_password2:
            return jsonify({"success": False, "message": "Yeni şifreler eşleşmiyor."})

        hashed = user_manager._hash_password(new_password)

        try:
            conn = sqlite3.connect(user_manager.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed, session["username"]))
            conn.commit()
            conn.close()

            updated_anything = True

        except Exception as e:
            return jsonify({"success": False, "message": f"Şifre güncellenemedi: {e}"})

    # -----------------------------------------------------

    if not updated_anything:
        return jsonify({"success": True, "message": "Hiçbir şey değiştirilmedi."})

    return jsonify({"success": True, "message": "Bilgiler başarıyla güncellendi!"})


@app.route('/api/list/<list_id>/toggle_production', methods=['POST'])
@login_required
def toggle_production_in_list(list_id):
    data = request.json
    production_id = data['production_id']
    current_user_id = session['user_id']
    db = get_db()

    # Authorization and existence control for list
    check_list = db.execute('SELECT 1 FROM lists WHERE id = ? AND user_id = ?', (list_id, current_user_id)).fetchone()
    if not check_list:
        return jsonify({'success': False, 'error': 'Unauthorized transaction or list does not exist'})
    try:
        # Check if list includes the production
        exists = db.execute('SELECT 1 FROM productions_in_lists WHERE list_id = ? AND production_id = ?', (list_id, production_id)).fetchone()

        # If exists, remove
        if exists:
            db.execute('DELETE FROM productions_in_lists WHERE list_id = ? AND production_id = ?', (list_id, production_id))
            action = "removed"
            db.execute('UPDATE lists SET production_count = production_count - 1 WHERE id = ? AND user_id = ?', (list_id, current_user_id))
        else:
            db.execute(f'INSERT INTO productions_in_lists (list_id, production_id, user_id) VALUES (?, ?, ?)', (list_id, production_id, current_user_id))
            action = "added"
            db.execute('UPDATE lists SET production_count = production_count + 1 WHERE id = ? AND user_id = ?', (list_id, current_user_id))
        db.commit()
        return jsonify({'success': True, 'action': action})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    path = get_db_path()

    if path:
        print(f"[INFO] Veritabanı bulundu: {path}")

        try:
            user_manager = UserManager(db_path=path, users_table_name=USERS_TABLE_NAME)
            app.run("0.0.0.0", port=6969, debug=True)
        except Exception as e:
            print(f"Uygulama başlatılamadı veya UserManager kurulumunda hata: {e}")

    else:
        print("Veritabanı dosyası bulunamadı!")