import sqlite3
import os
import re

DB_PATH = "movies_21-11-2025__11-36-42.db"   # BURAYA KENDİ DB DOSYANIN ADINI KOY
TEMPLATE_PATH = "Template.html"                    # Gönderdiğin template
OUTPUT_DIR = "web_pages"

def safe(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)


def generate_star_rating(imdb):
    try:
        rating = float(imdb)
    except:
        rating = 0.0

    stars = int(rating // 2)
    return "★" * stars + "☆" * (5 - stars)


def generate_pages():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Template dosyasını oku
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    cursor.execute("""
        SELECT id, title, poster_link, start_year, imdb_rating, plot
        FROM productions
    """)
    productions = cursor.fetchall()

    for prod in productions:
        pid, title, poster, year, imdb, plot = prod

        # Contributors ---------------------
        cursor.execute("""
            SELECT first_name, last_name, role
            FROM contributors
            WHERE production_id = ?
        """, (pid,))
        rows = cursor.fetchall()

        directors = ", ".join(a + " " + b for a, b, r in rows if r == "director") or "Unknown"
        writers = ", ".join(a + " " + b for a, b, r in rows if r == "writer") or "Unknown"
        actors = ", ".join(a + " " + b for a, b, r in rows if r == "actor") or "Unknown"

        # IMDb visual rating
        star_rating = generate_star_rating(imdb)
        imdb_str = str(imdb) if imdb else "N/A"

        # Template'i doldur
        html = template
        html = html.replace("Wake Up Dead Man", title)
        html = html.replace("2025", str(year))
        html = html.replace(
            'src="https://image.tmdb.org/t/p/w500/ggFHVNu6YYI5L9pCfOacjizRGt.jpg"',
            f'src="{poster}"'
        )
        html = html.replace("Rian Johnson", directors)
        html = html.replace(
            """HE WORKS IN MYSTERIOUS WAYS.""",
            plot.replace("\n", "<br>")
        )
        html = html.replace("★★★★☆", star_rating)
        html = html.replace("3.9", imdb_str)

        # Bu alan ileride DB reviews ile doldurulacak
        # Şimdilik placeholder
        html = html.replace("POPULAR REVIEWS", "POPULAR REVIEWS (auto)")
        html = html.replace("RECENT REVIEWS", "RECENT REVIEWS (auto)")

        # Output file adı
        filename = safe(title) + ".html"
        output_path = os.path.join(OUTPUT_DIR, filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print("✓ Created:", output_path)

    conn.close()


if __name__ == "__main__":
    generate_pages()
