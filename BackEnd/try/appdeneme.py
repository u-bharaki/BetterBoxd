from flask import Flask, render_template, g, request, jsonify, session, redirect, url_for
import sqlite3
import os
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Güvenli oturum yönetimi için rastgele anahtar

# --- AYARLAR ---
DB_NAME = "movies"  # Veritabanı dosyasının ön eki (movies_2025....db)
USERS_TABLE_NAME = "users"


def get_db_path():
    """Databases klasöründeki en güncel 'movies_*.db' dosyasını bulur."""
    base_dir = Path(__file__).parent
    db_dir = base_dir / "databases"  # Senin klasör yapına göre ayarla

    # Eğer databases klasörü yoksa, scriptin yanına bak
    if not db_dir.is_dir():
        db_dir = base_dir

    # Pattern: movies_*.db
    db_files = list(db_dir.glob(f"{DB_NAME}_*.db"))

    if not db_files:
        # Hiçbir şey bulamazsa manuel bir isim dene (fallback)
        fallback = base_dir / "betterboxd.db"
        if fallback.exists():
            return str(fallback)
        return None

    # En son değiştirilen dosyayı al
    latest_db = max(db_files, key=os.path.getmtime)
    return str(latest_db)


# --- VERİTABANI BAĞLANTISI (Context Manager) ---
def get_db():
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


# --- AUTH DECORATOR ---
# Giriş yapmamış kullanıcıyı login sayfasına yönlendirmek için
def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    wrap.__name__ = f.__name__
    return wrap


# --- AUTH ROUTES (Giriş/Kayıt) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute(f'SELECT * FROM {USERS_TABLE_NAME} WHERE username = ?', (username,)).fetchone()

        # NOT: Gerçek projede şifreler hash'lenerek saklanmalıdır (örn: werkzeug.security)
        # Şimdilik düz metin kontrolü yapıyoruz.
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['fullname'] = f"{user['first_name']} {user['last_name']}"
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

        db = get_db()

        # Kullanıcı var mı kontrol et
        existing_user = db.execute(f'SELECT id FROM {USERS_TABLE_NAME} WHERE username = ?', (username,)).fetchone()

        if existing_user:
            error = 'Bu kullanıcı adı zaten alınmış.'
        elif not all([username, password, email, first_name, last_name]):
            error = 'Lütfen tüm alanları doldurun.'
        else:
            try:
                db.execute(f'''
                    INSERT INTO {USERS_TABLE_NAME} (username, password, email, first_name, last_name)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, password, email, first_name, last_name))
                db.commit()
                return redirect(url_for('login'))
            except Exception as e:
                error = f'Kayıt sırasında hata oluştu: {str(e)}'

    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- ANA SAYFA (SPA) ---

@app.route('/')
@login_required
def index():
    """
    Ana Sayfa: Kullanıcı giriş yapmışsa SPA'yı (index.html) yükler.
    """
    return render_template('index.html', user=session)


# --- API UÇ NOKTALARI (ENDPOINTS) ---

@app.route('/api/productions')
def get_all_productions():
    db = get_db()

    # 1. URL Parametrelerini Al (Varsayılan değerlerle)
    page = int(request.args.get('page', 1))
    limit = 20  # Her sayfada kaç film olacak
    offset = (page - 1) * limit

    genre = request.args.get('genre')
    year = request.args.get('year')
    sort_by = request.args.get('sort', 'pop')  # pop, rating, alpha, new

    # 2. Dinamik SQL Sorgusu İnşa Et
    # Temel sorgumuz bu, filtreler geldikçe üzerine ekleyeceğiz.
    # NOT: Puanı hesaplamak için reviews tablosuyla JOIN yapıyoruz.
    query = """
        SELECT p.id, p.title, p.start_year, p.poster_link, 
               AVG(r.score) as avg_score
        FROM productions p
        LEFT JOIN reviews r ON p.id = r.production_id
    """
    params = []
    where_clauses = []

    # Filtre: Tür (Genre)
    if genre and genre != 'all':
        # SQL'de genre sütunu "Action, Drama" gibiyse LIKE kullanırız
        where_clauses.append("p.genre LIKE ?")
        params.append(f'%{genre}%')

    # Filtre: Yıl (Year)
    if year and year != 'all':
        where_clauses.append("p.start_year = ?")
        params.append(year)

    # WHERE koşullarını birleştir
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    # Gruplama (Her film için tek satır ve ortalama puan)
    query += " GROUP BY p.id"

    # Sıralama (Sort)
    if sort_by == 'rating':
        query += " ORDER BY avg_score DESC"
    elif sort_by == 'alpha':
        query += " ORDER BY p.title ASC"
    elif sort_by == 'new':
        query += " ORDER BY p.start_year DESC"
    else:  # default: popülarite (veya ID sırası)
        query += " ORDER BY p.id DESC"

    # 3. Sayfalama (Pagination)
    # Önce toplam film sayısını (filtreli haliyle) bulmalıyız ki sayfa sayısını hesaplayalım.
    # Bu biraz trick gerektirir, performans için basitçe filtered results count yapılır.
    # Şimdilik basitlik adına, limit/offset eklemeden önceki sorguyu saydırabiliriz
    # ama bu karmaşık olabilir. Basit bir yol izleyelim:

    # Sayfalama komutlarını ekle
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    productions = db.execute(query, params).fetchall()

    # Toplam sayfa sayısı için basit bir count sorgusu (Filtresiz toplamı alalım şimdilik)
    # İdeal dünyada filtreli count alınır.
    total_items = db.execute("SELECT COUNT(*) FROM productions").fetchone()[0]
    total_pages = (total_items + limit - 1) // limit

    return jsonify({
        'productions': [{
            'id': row['id'],
            'title': row['title'],
            'year': row['start_year'],
            'poster': row['poster_link'],
            'rating': round(row['avg_score'], 1) if row['avg_score'] else 0
        } for row in productions],
        'total_pages': total_pages,
        'current_page': page
    })

@app.route('/api/production/<int:prod_id>')
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

    rating_data = db.execute('''
        SELECT AVG(score) as average, COUNT(*) as count 
        FROM reviews WHERE production_id = ?
    ''', (prod_id,)).fetchone()

    # Puanı 10 üzerinden hesapla ve yuvarla
    avg_rating = round(rating_data['average'], 1) if rating_data['average'] else 0

    response = {
        'id': production['id'],
        'title': production['title'],
        'year': production['start_year'],
        'plot': production['plot'],
        'poster': production['poster_link'],
        'backdrop': production['poster_link'],
        'director': f"{director['first_name']} {director['last_name']}" if director else "Bilinmiyor",
        'rating': avg_rating,
        'rating_count': rating_data['count']
    }
    return jsonify(response)


@app.route('/api/production/<int:prod_id>/reviews')
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
@login_required
def get_profile():
    db = get_db()
    current_user_id = session['user_id']

    user = db.execute(f'SELECT * FROM {USERS_TABLE_NAME} WHERE id = ?', (current_user_id,)).fetchone()
    total_watched = db.execute('SELECT COUNT(*) FROM reviews WHERE user_id = ?', (current_user_id,)).fetchone()[0]

    # (İsteğe bağlı) Takipçi sayıları için 'follows' tablosu varsa:
    try:
        followers = \
        db.execute('SELECT COUNT(*) FROM follows WHERE followed_user_id = ?', (current_user_id,)).fetchone()[0]
        following = \
        db.execute('SELECT COUNT(*) FROM follows WHERE follower_user_id = ?', (current_user_id,)).fetchone()[0]
    except:
        followers = 0
        following = 0

    return jsonify({
        'username': user['username'],
        'fullname': f"{user['first_name']} {user['last_name']}",
        'stats': {
            'watched': total_watched,
            'followers': followers,
            'following': following
        }
    })


@app.route('/api/review', methods=['POST'])
@login_required
def add_review():
    data = request.json
    db = get_db()
    current_user_id = session['user_id']

    try:
        # score artık 1 ile 10 arasında geliyor
        db.execute('''
            INSERT INTO reviews (user_id, production_id, score, context)
            VALUES (?, ?, ?, ?)
        ''', (current_user_id, data['productionId'], data['score'], data['text']))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    path = get_db_path()
    if path:
        print(f"[INFO] Veritabanı bulundu: {path}")
        app.run(debug=True)
    else:
        print("[HATA] Veritabanı dosyası bulunamadı! Lütfen 'movies_*.db' dosyasını kontrol et.")