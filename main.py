from datetime import datetime
import requests
import pandas as pd
import sqlite3
import time
import sys

from matplotlib.pyplot import title
from numpy.ma.core import nomask
from sympy.physics.units import length

API_KEYS_FILE = "api_keys.txt"
DBTABLE_NAME = "movies"
APPROX_FILM_COUNT = 30000
current_key_index = 0
api_keys = []

def get_time_str():
    return datetime.now().strftime("%d-%m-%Y__%H-%M-%S")

def load_api_keys():
    """api_keys.txt içindeki anahtarları listeye yükler."""
    global api_keys
    with open(API_KEYS_FILE, "r") as f:
        api_keys = [line.strip() for line in f.readlines() if line.strip()]
    if not api_keys:
        raise ValueError("api_keys.txt dosyasında hiç API anahtarı yok.")

def get_current_api_key():
    """Şu anda kullanılan API anahtarını döndürür."""
    global current_key_index
    if current_key_index >= len(api_keys):
        raise ValueError("[WARNING] Tüm API anahtarları kullanıldı.")
    return api_keys[current_key_index]

def mark_key_as_used(key):
    """Verilen API key'in yanına #used işaretini ekler."""
    lines = []
    with open(API_KEYS_FILE, "r") as f:
        lines = f.readlines()
    with open(API_KEYS_FILE, "w") as f:
        for line in lines:
            if line.strip() == key:
                f.write(f"{line.strip()} #used\n")
            else:
                f.write(line)

def renew_api_key():
    """
    Bir sonraki API anahtarına geçer.
    Eğer tüm anahtarlar bittiyse hata verir.
    """
    global current_key_index
    mark_key_as_used(get_current_api_key())

    current_key_index += 1
    if current_key_index >= len(api_keys):
        print("\n[ERROR] Tüm API anahtarları kullanıldı.")
        return False
    print(f"\n[INFO] API key yenilendi. Yeni anahtar: {api_keys[current_key_index]}")
    return True

class DualLogger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def get_films(approx_film_count, conn, cursor):

    sys.stdout = DualLogger(f"logs/log_{get_time_str()}.txt")

    load_api_keys()
    BASE_URL = "http://www.omdbapi.com/?i=tt3896198&apikey=efdd0d9b"

    all_data = []

    # Arama kelimeleri: tek harfli + çift harfli kombinasyonlar
    search_terms = [chr(i) for i in range(97, 99)]  # a-z
    search_terms += [chr(i) + chr(j) for i in range(97, 123) for j in range(97, 123)]
    search_terms = [chr(i) + chr(j) + chr(k) for i in range(97, 123) for j in range(97, 123) for k in range(97, 123)]
    x = 0
    for term in search_terms:
        print(f"\n[INFO] '{term}' ARANIYOR...-----------------------------------------------------------")
        page = 1
        while x < approx_film_count:
            x += 1
            params = {"s": term, "page": page}
            BASE_URL = get_current_api_key()
            response = requests.get(BASE_URL, params=params)
            try:
                data = response.json()
            except:
                print("[ERROR] 1 -----------------------------------------")
                continue
            print(f"[INFO - LIST] {x} - TERM '{term}' - PAGE '{page}' - {data}")

            if data.get("Error") == "Request limit reached!":
                print(f"[WARNING] Limit doldu -> {BASE_URL}")
                success = renew_api_key()
                if success:
                    continue  # Yeni anahtarla tekrar dene
                else:
                    transfer_to_excel(all_data)

            if data.get("Response") == "True":

                n = 0
                for item in data.get("Search", []):
                    title = item.get("Title")

                    BASE_URL = get_current_api_key()
                    # Detaylı veri çek (Title, Year, Director, vs.)
                    detail_resp = requests.get(BASE_URL, params={"t": title})
                    x += 1
                    try:
                        details = detail_resp.json()
                    except:
                        print("[ERROR] 2 -----------------------------------------")
                        continue
                    print(f"[INFO - FILM] {x} - {details}")

                    if details.get("Error") == "Request limit reached!":
                        print(f"[WARNING] Limit doldu -> {BASE_URL}")
                        success = renew_api_key()
                        if success:
                            continue  # Yeni anahtarla tekrar dene
                        else:
                            transfer_to_excel(all_data)

                    if details.get("Response") == "True":
                        insert_to_sql(details, conn, cursor)
                        all_data.append(details)
                        n += 1
                if n >= 10:
                    page += 1
                else:
                    break
            else:
                print("[WARNING] Başarısız!")
                break
            time.sleep(0.2)  # rate limit'e yakalanmamak için
        if x >= approx_film_count:
            break

    transfer_to_excel(all_data)

def transfer_to_excel(all_data):
    df = pd.DataFrame(all_data)
    df.to_excel(f"omdb_full_dataset_{get_time_str()}.xlsx", index=False)
    print(f"✅ Tüm veriler 'omdb_full_dataset_{get_time_str()}.xlsx' dosyasına kaydedildi.")

def get_film_debug(api_key, film_title):
    detail_resp = requests.get(api_key, params={"t": film_title})
    try:
        details = detail_resp.json()
        print(f"[INFO - FILM] {details}")
    except:
        print("[ERROR] 2 -----------------------------------------")

def connect_sqlite():
    conn = sqlite3.connect(f"databases/{DBTABLE_NAME}_{get_time_str()}.db")
    cursor = conn.cursor()
    return conn, cursor

def create_table(cursor):
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {DBTABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        country TEXT,
        language TEXT,
        poster_link TEXT,
        total_seasons INTEGER,
        start_year INTEGER CHECK(start_year >= 1000 AND start_year <= 9999),
        end_year INTEGER CHECK(end_year >= 1000 AND end_year <= 9999),
        wins INTEGER,
        nominations INTEGER,
        imdb_rating REAL CHECK(imdb_rating >= 0.0 AND imdb_rating <= 10.0),
        imdb_votes INTEGER,
        plot TEXT,
        rated TEXT,
        runtime INTEGER,
        type TEXT CHECK(type IN ('movie', 'series')),
        added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """)

def insert_to_sql(data, conn, cursor):
    years = data.get("Year")
    if len(years) == 4:
        start_year = years
        end_year = years
    elif len(years) == 5:
        start_year = years[:4]
        end_year = years[:4]
    elif len(years) > 5:
        start_year = years[:4]
        end_year = years[5:9]
    else:
        start_year = ""
        end_year = ""

    runtime = data.get("Runtime")
    runtime = runtime.split(" ")
    if len(runtime) > 0 and runtime[0] != "N/A":
        runtime = runtime[0]
    else:
        runtime = ""
    awards = data.get("Awards")

    wins = 0
    nominations = 0
    if awards and awards != "N/A":
        parts = awards.split("&")
        for part in parts:
            part = part.strip()
            number_str = part.split(" ")[0]
            try:
                number = int(number_str)
            except ValueError:
                number = 0
            if "win" in part.lower():
                wins = number
            elif "nomination" in part.lower():
                nominations = number

        #print(f"Start year: {start_year}  End year: {end_year}  Runtime: {runtime}  Awards: {awards}  Wins: {wins}")

    if data.get("Country") == "N/A":
        Country = ""
    else:
        Country = data.get("Country")
    if data.get("Language") == "N/A":
        Language = ""
    else:
        Language = data.get("Language")
    if data.get("Poster") == "N/A":
        Poster = ""
    else:
        Poster = data.get("Poster")
    if data.get("totalSeasons") == "N/A":
        totalSeasons = 0
    else:
        totalSeasons = data.get("totalSeasons")
    if data.get("imdbRating") == "N/A" or not data.get("imdbRating"):
        imdbRating = 0
    else:
        imdbRating = data.get("imdbRating")
    if data.get("imdbVotes") == "N/A":
        imdbVotes = 0
    else:
        imdbVotes = data.get("imdbVotes")
    if data.get("Plot") == "N/A":
        Plot = ""
    else:
        Plot = data.get("Plot")
    if data.get("Rated") == "N/A":
        Rated = ""
    else:
        Rated = data.get("Rated")
    if data.get("Type") == "N/A":
        Type = "movie"
    else:
        Type = data.get("Type")

    cursor.execute(f"""
    INSERT INTO {DBTABLE_NAME} (
        title,
        country,
        language,
        poster_link,
        total_seasons,
        start_year,
        end_year,
        wins,
        nominations,
        imdb_rating,
        imdb_votes,
        plot,
        rated,
        runtime,
        type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data.get("Title"), Country, Language, Poster, totalSeasons, start_year, end_year, wins, nominations, imdbRating, imdbVotes, Plot, Rated, runtime, Type))

    conn.commit()

conn, cursor = connect_sqlite()
create_table(cursor)

get_films(APPROX_FILM_COUNT, conn, cursor)
