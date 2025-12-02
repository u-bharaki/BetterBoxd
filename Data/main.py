from datetime import datetime
from pathlib import Path

import requests
import pandas as pd
import sqlite3
import time
import sys
import uuid
import re

API_KEYS_FILE = "api_keys.txt"
SAVE_FILE = "savedene"
LAST_SAVE_FILE = ""
NEW_SAVE_FILE = ""
LOG_FILE = ""
EXCEL_FILE = ""
NEW_EXCEL_FILE = ""
DB_FILE = ""
NEW_DB_FILE = ""

# Database name (.db)
DB_NAME = "movies"

# Table names in database
PRODUCTIONS_TABLE_NAME = "productions"
CONTRIBUTORS_TABLE_NAME = "contributors"
USERS_TABLE_NAME = "users"
FOLLOWS_TABLE_NAME = "follows"
LISTS_TABLE_NAME = "lists"
PRODUCTIONS_IN_LISTS_TABLE_NAME = "productions_in_lists"
REVIEWS_TABLE_NAME = "reviews"

APPROX_FILM_COUNT = 100_000
TOTAL_QUERY_COUNT = 0
current_key_index = 0
START_TERM_INDEX = 0
TERM_INDEX = 0
PAGE_INDEX = 1
ITEM_INDEX = 0
api_keys = []

is_api_keys_finished = False
last_second_letter = None #for auto save

ROLE_ACTOR = "actor"
ROLE_DIRECTOR = "director"
ROLE_WRITER = "writer"

def get_time_str():
    return datetime.now().strftime("%d-%m-%Y__%H-%M-%S")

def load_api_keys():
    """api_keys.txt içindeki anahtarları listeye yükler."""
    global api_keys

    try:
        with open(API_KEYS_FILE, "r") as f:
            api_keys = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("HATA: API KEYS FILE NOT FOUND")
        exit(1)
    except Exception as e:
        print(f"{API_KEYS_FILE}: {e}")
        exit(1)
    if not api_keys:
        print(f"{API_KEYS_FILE} dosyasında hiç API anahtarı yok.")

def get_current_api_key():
    """Şu anda kullanılan API anahtarını döndürür."""
    global current_key_index
    if current_key_index >= len(api_keys):
        print("[WARNING] Tüm API anahtarları kullanıldı.")
        global is_api_keys_finished
        is_api_keys_finished = True
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
    print("[INFO] API key değiştirildi, 5 saniye bekleniyor..")
    time.sleep(5)
    return True

def load_last_session():
    global SAVE_FILE, LAST_SAVE_FILE, NEW_SAVE_FILE
    i = 1
    SAVE_FILES = []
    while(Path(f"{SAVE_FILE}{i}.txt").is_file()):
        SAVE_FILES.append(Path(f"{SAVE_FILE}{i}.txt"))
        i += 1
    if not SAVE_FILES:
        print(f"[INFO] {SAVE_FILE}{i} do not exists")
        print(f"[INFO] Creating {SAVE_FILE}{i}.txt\n")
        LAST_SAVE_FILE = SAVE_FILE+str(i)+".txt"
        return False
    save_file_name = SAVE_FILES[len(SAVE_FILES) - 1].name
    j = 0
    for x in range(0, len(save_file_name)):
        if '0' <= save_file_name[x] <= '9':
            j = x
            break

    LAST_SAVE_FILE = save_file_name[0:j] + str(i-1) + ".txt"
    NEW_SAVE_FILE = save_file_name[0:j] + str(i) + ".txt"

    with open(LAST_SAVE_FILE, "r") as f:
        data = [line.strip() for line in f.readlines() if line.strip()]
    if not data:
        print(f"{LAST_SAVE_FILE} is empty")
        return False
    elif len(data) == 8:
        global DB_FILE, EXCEL_FILE, LOG_FILE, TOTAL_QUERY_COUNT, current_key_index, START_TERM_INDEX, PAGE_INDEX, ITEM_INDEX

        DB_FILE = data[0]
        EXCEL_FILE = data[1]
        LOG_FILE = data[2]

        try:
            TOTAL_QUERY_COUNT = int(data[3])
            current_key_index = int(data[4])
            START_TERM_INDEX = int(data[5])
            PAGE_INDEX = int(data[6])
            ITEM_INDEX = int(data[7])
        except ValueError:
            print(f"[ERROR] {LAST_SAVE_FILE}: {data[3]}, {data[4]}, {data[5]}, {data[6]} and/or {data[7]} are invalid (try int)")
            return False
        return True
    else:
        print(f"[ERROR] {LAST_SAVE_FILE} is not in appropriate format:\ndatabase_folder.db(str)\nexcel_folder.excel(str)\nTotal_Query_Count(int)\nCurrent_Key_Index(int)")
        return False

def save_session():
    global NEW_SAVE_FILE, NEW_DB_FILE, NEW_EXCEL_FILE, LOG_FILE, TOTAL_QUERY_COUNT, current_key_index, TERM_INDEX

    if is_api_keys_finished:
        current_key_index = 0

    if NEW_SAVE_FILE != "":
        file = NEW_SAVE_FILE
    else:
        file = LAST_SAVE_FILE
    if NEW_DB_FILE:
        db_file = NEW_DB_FILE
    else:
        db_file = DB_FILE

    with open(file, "w") as f:
        f.write(f"{db_file}\n")
        f.write(f"{NEW_EXCEL_FILE}\n")
        f.write(f"{LOG_FILE}\n")
        f.write(f"{TOTAL_QUERY_COUNT}\n")
        f.write(f"{current_key_index}\n")
        f.write(f"{TERM_INDEX}\n")
        f.write(f"{PAGE_INDEX}\n")
        f.write(f"{ITEM_INDEX}\n")
    print(f"Session successfully saved to '{file}'.")

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
    all_data = []

    try:

        # If not exists, create database folder
        Path("logs").mkdir(parents=True, exist_ok=True)
        # Create log file
        global LOG_FILE, TERM_INDEX, PAGE_INDEX, TOTAL_QUERY_COUNT
        LOG_FILE = f"logs/{get_time_str()}.log"
        sys.stdout = DualLogger(LOG_FILE)

        load_api_keys()

        search_terms = []

        # 3 harfli
        for i in range(97, 123):
            for j in range(97, 123):
                for k in range(97, 123):
                    search_terms.append(chr(i) + chr(j) + chr(k))

        query_count = 0
        for TERM_INDEX in range(START_TERM_INDEX, len(search_terms)):
            term = search_terms[TERM_INDEX]
            auto_save_on_term_change(term)
            print(f"\n[INFO] '{term}' ARANIYOR...-----------------------------------------------------------")
            if query_count != 0:
                PAGE_INDEX = 1
            while query_count < approx_film_count:
                query_count += 1
                params = {"s": term, "page": PAGE_INDEX}
                BASE_URL = get_current_api_key()
                if is_api_keys_finished:
                    transfer_to_excel(all_data)
                try:
                    response = requests.get(BASE_URL, params=params)
                    data = response.json()
                except Exception as e:
                    print(f"[ERROR] Request hata verdi: {e}")
                    save_session()
                    conn.commit()
                    continue
                print(f"[INFO - LIST] {query_count} - TERM '{term}' - PAGE '{PAGE_INDEX}' - {data}")

                if data.get("Error") == "Request limit reached!":
                    print(f"[WARNING] Limit doldu -> {BASE_URL}")
                    success = renew_api_key()
                    if success:
                        continue  # Yeni anahtarla tekrar dene
                    else:
                        save_session()
                        transfer_to_excel(all_data)

                if data.get("Error") == "Invalid API key!":
                    print(f"[ERROR] Invalid key: {BASE_URL} - Bir sonraki key'e geçiliyor...")
                    success = renew_api_key()
                    if success:
                        continue
                    else:
                        save_session()
                        transfer_to_excel(all_data)

                if data.get("Response") == "True":

                    search_results = data.get("Search", [])
                    global ITEM_INDEX
                    for item_index in range(0, len(data.get("Search", []))):
                        ITEM_INDEX = item_index
                        item = data.get("Search", [])[item_index]
                        title = item.get("Title")

                        BASE_URL = get_current_api_key()
                        if is_api_keys_finished:
                            transfer_to_excel(all_data)
                        # Detaylı veri çek (Title, Year, Director, vs.)

                        try:
                            detail_resp = requests.get(BASE_URL, params={"t": title})
                            query_count += 1
                            details = detail_resp.json()
                        except Exception as e:
                            print(f"[ERROR] Detail request hata verdi: {e}")
                            save_session()
                            conn.commit()
                            continue

                        print(f"[INFO - FILM] {query_count} - {details}")

                        if details.get("Error") == "Request limit reached!":
                            print(f"[WARNING] Limit doldu -> {BASE_URL}")
                            success = renew_api_key()
                            if success:
                                continue  # Yeni anahtarla tekrar dene
                            else:
                                transfer_to_excel(all_data)

                        if details.get("Error") == "Invalid API key!":
                            print(f"[ERROR] Invalid key (detail lookup): {BASE_URL}")
                            success = renew_api_key()
                            if success:
                                continue
                            else:
                                transfer_to_excel(all_data)

                        if details.get("Response") == "True":
                            insert_to_sql(details, conn, cursor)
                            all_data.append(details)
                    if len(search_results) >= 10:
                        PAGE_INDEX += 1
                    else:
                        break
                else:
                    print("[WARNING] Başarısız! Sonraki term'e geçiliyor.")
                    break
                time.sleep(0.2)  # rate limit'e yakalanmamak için
            if query_count >= approx_film_count:
                TOTAL_QUERY_COUNT += query_count
                break
        transfer_to_excel(all_data)
    except KeyboardInterrupt:
        print("\n[INFO] Kullanıcı Ctrl+C ile programı durdurdu.")
        try:
            conn.commit()
        except Exception as e:
            print(f"[ERROR] Ctrl+C sırasında conn.commit hata verdi: {e}")
        try:
            transfer_to_excel(all_data)
        except Exception as e:
            print(f"[ERROR] Ctrl+C sırasında transfer_to_excel hata verdi: {e}")

    except Exception as e:
        print(f"[FATAL ERROR in get_films]: {e}")
        save_session()
        transfer_to_excel(all_data)

def transfer_to_excel(all_data):
    try:
        Path("raw_excels").mkdir(parents=True, exist_ok=True)
        conn.commit()
        df = pd.DataFrame(all_data)
        global NEW_EXCEL_FILE
        NEW_EXCEL_FILE = f"raw_excels/omdb_full_dataset_{get_time_str()}.xlsx"
        df.to_excel(NEW_EXCEL_FILE, index=False)
        print(f"✅ Tüm veriler '{NEW_EXCEL_FILE}' dosyasına kaydedildi.")
    except Exception as e:
        print(f"[ERROR] Excel yazılamadı: {e}")

    try:
        save_session()
    except Exception as e:
        print(f"[ERROR] save_session hata verdi: {e}")

    print("[INFO] Program güvenli bir şekilde kapatılıyor.")
    sys.exit(0)

def get_film_debug(api_key, film_title):
    detail_resp = requests.get(api_key, params={"t": film_title})
    try:
        details = detail_resp.json()
        print(f"[INFO - FILM] {details}")
    except:
        print("[ERROR] 3 -----------------------------------------")

def connect_sqlite():
    Path("databases").mkdir(parents=True, exist_ok=True)
    global DB_FILE, NEW_DB_FILE
    if not DB_FILE:
        print(f"Database file does not exist. Creating databases/{DB_NAME}_{get_time_str()}.db")
        NEW_DB_FILE = f"databases/{DB_NAME}_{get_time_str()}.db"
        conn = sqlite3.connect(NEW_DB_FILE)
    else:
        print(f"Database file exists. Using databases/{DB_FILE}.db")
        conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    return conn, cursor

def create_tables(cursor):
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {PRODUCTIONS_TABLE_NAME} (
        id TEXT PRIMARY KEY,
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
        genres TEXT,
        site_rating REAL DEFAULT 0,
        site_likes INTEGER DEFAULT 0,
        added_at TIMESTAMP NOT NULL DEFAULT (datetime('now', '+3 hour'))
    )
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {CONTRIBUTORS_TABLE_NAME} (
        production_id TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        role TEXT CHECK(role IN ('director', 'writer', 'actor')),
        
        CONSTRAINT fk_{CONTRIBUTORS_TABLE_NAME}_production_id FOREIGN KEY (production_id) REFERENCES {PRODUCTIONS_TABLE_NAME}(id)
    )
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {USERS_TABLE_NAME} (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        email TEXT NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        last_login TIMESTAMP NOT NULL DEFAULT (datetime('now', '+3 hour')),
        created_at TIMESTAMP NOT NULL DEFAULT (datetime('now', '+3 hour'))
    )
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {FOLLOWS_TABLE_NAME} (
        follower_user_id TEXT NOT NULL,
        followed_user_id TEXT NOT NULL,
        followed_at TIMESTAMP NOT NULL DEFAULT (datetime('now', '+3 hour')),
        
        CONSTRAINT fk_follower_user_id FOREIGN KEY (follower_user_id) REFERENCES {USERS_TABLE_NAME}(id) ON DELETE CASCADE,
        CONSTRAINT fk_followed_user_id FOREIGN KEY (followed_user_id) REFERENCES {USERS_TABLE_NAME}(id) ON DELETE CASCADE    
    )
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {LISTS_TABLE_NAME} (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        user_id TEXT NOT NULL,
        production_count INTEGER NOT NULL,
        
        CONSTRAINT fk_{LISTS_TABLE_NAME}_user_id FOREIGN KEY (user_id) REFERENCES {USERS_TABLE_NAME}(id) ON DELETE CASCADE
    )
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {PRODUCTIONS_IN_LISTS_TABLE_NAME} (
        production_id TEXT NOT NULL,
        list_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        
        CONSTRAINT fk_{PRODUCTIONS_IN_LISTS_TABLE_NAME}_production_id FOREIGN KEY (production_id) REFERENCES {PRODUCTIONS_TABLE_NAME}(id) ON DELETE CASCADE,
        CONSTRAINT fk_{PRODUCTIONS_IN_LISTS_TABLE_NAME}_list_id FOREIGN KEY (list_id) REFERENCES {LISTS_TABLE_NAME}(id) ON DELETE CASCADE,
        CONSTRAINT fk_{PRODUCTIONS_IN_LISTS_TABLE_NAME}_user_id FOREIGN KEY (user_id) REFERENCES {USERS_TABLE_NAME}(id) ON DELETE CASCADE
        
    )
    """)

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {REVIEWS_TABLE_NAME} (
        id TEXT PRIMARY KEY,
        context TEXT NOT NULL,
        score REAL NOT NULL,
        production_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        
        CONSTRAINT fk_{REVIEWS_TABLE_NAME}_production_id FOREIGN KEY (production_id) REFERENCES {PRODUCTIONS_TABLE_NAME}(id) ON DELETE CASCADE,
        CONSTRAINT fk_{REVIEWS_TABLE_NAME}_user_id FOREIGN KEY (user_id) REFERENCES {USERS_TABLE_NAME}(id) ON DELETE CASCADE
    )
    """)

def insert_to_sql(data, conn, cursor):

    Title = data.get("Title")

    year_str = data.get("Year", "")
    years_found = re.findall(r"(\d{4})", year_str)
    start_year = None
    end_year = None

    if len(years_found) == 1:
        start_year = int(years_found[0])
        if "-" not in year_str:
            end_year = int(years_found[0])
        else:
            end_year = None
    elif len(years_found) >= 2:
        start_year = int(years_found[0])
        end_year = int(years_found[1])

    if start_year is None:
        print(f"[WARNING] '{Title}' invalid start_year ('{year_str}'), therefore can not add to database")
        return

    cursor.execute(
        f"SELECT 1 FROM {PRODUCTIONS_TABLE_NAME} WHERE Title = ? AND start_year = ? AND end_year = ?;",
        (Title, start_year, end_year)
    )

    film_exists = cursor.fetchone()

    if film_exists:
        print(f"[WARNING] {Title} already exists")
        return

    runtime_str = data.get("Runtime", "N/A")
    runtime = 0
    if runtime_str != "N/A":
        parts = runtime_str.split(" ")
        if parts and parts[0].isdigit():
            runtime = int(parts[0])

    awards = data.get("Awards", "N/A")
    wins = 0
    nominations = 0

    if awards and awards != "N/A":

        if "total" in awards.lower():
            wins_match = re.search(r"(\d+)\s+win", awards, re.IGNORECASE)
            if wins_match:
                wins = int(wins_match.group(1))

            noms_match = re.search(r"(\d+)\s+nomination", awards, re.IGNORECASE)
            if noms_match:
                nominations = int(noms_match.group(1))

        else:

            won_matches = re.findall(r"won\s+(\d+)", awards, re.IGNORECASE)
            wins_text_matches = re.findall(r"(\d+)\s+win", awards, re.IGNORECASE)

            for w in won_matches + wins_text_matches:
                wins += int(w)

            nom_for_matches = re.findall(r"nominated\s+for\s+(\d+)", awards, re.IGNORECASE)
            noms_text_matches = re.findall(r"(\d+)\s+nomination", awards, re.IGNORECASE)

            for n in nom_for_matches + noms_text_matches:
                nominations += int(n)

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

    totalSeasons = 0
    ts_str = data.get("totalSeasons", "N/A")
    if ts_str != "N/A" and ts_str.isdigit():
        totalSeasons = int(ts_str)

    imdbRating = 0.0
    ir_str = data.get("imdbRating", "N/A")
    if ir_str != "N/A":
        try:
            imdbRating = float(ir_str)
        except ValueError:
            imdbRating = 0.0

    imdbVotes = 0
    iv_str = data.get("imdbVotes", "N/A")
    if iv_str != "N/A":
        try:
            imdbVotes = int(iv_str.replace(",", ""))
        except ValueError:
            imdbVotes = 0

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

    genres_data = data.get("Genre", "N/A")
    if genres_data == "N/A":
        genres = ""
    else:
        genres = genres_data

    production_id = str(uuid.uuid4())

    cursor.execute(f"""
    INSERT INTO {PRODUCTIONS_TABLE_NAME} (
        id,
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
        type,
        genres,
        site_rating,
        site_likes
        )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (production_id, Title, Country, Language, Poster, totalSeasons, start_year, end_year, wins, nominations, imdbRating, imdbVotes, Plot, Rated, runtime, Type, genres, 0, 0))

    directors = data.get("Director")
    if directors:
        directors_splitted = directors.split(",")
        for director in directors_splitted:
            director = director.strip()
            if director is None or director == "N/A":
                continue
            words = director.split(" ")
            surname = words[-1].title()
            if len(words) != 1:
                name = " ".join(words[:-1]).title()
            else:
                name = surname

            cursor.execute(f"""
            INSERT INTO {CONTRIBUTORS_TABLE_NAME} (
                production_id,
                first_name,
                last_name,
                role)
            VALUES (?, ?, ?, ?)
            """, (production_id, name, surname, ROLE_DIRECTOR))

    writers = data.get("Writer")
    if writers:
        writers_splitted = writers.split(",")
        for writer in writers_splitted:
            writer = writer.strip()
            if writer is None or writer == "N/A":
                continue
            words = writer.split(" ")
            surname = words[-1].title()
            if len(words) != 1:
                name = " ".join(words[:-1]).title()
            else:
                name = surname

            cursor.execute(f"""
            INSERT INTO {CONTRIBUTORS_TABLE_NAME} (
                production_id,
                first_name,
                last_name,
                role)
            VALUES (?, ?, ?, ?)
            """, (production_id, name, surname, ROLE_WRITER))

    actors = data.get("Actors")
    if actors:
        actors_splitted = actors.split(",")
        for actor in actors_splitted:
            actor = actor.strip()
            if actor is None or actor == "N/A":
                continue
            words = actor.split(" ")
            surname = words[-1].title()
            if len(words) != 1:
                name = " ".join(words[:-1]).title()
            else:
                name = surname

            cursor.execute(f"""
            INSERT INTO {CONTRIBUTORS_TABLE_NAME} (
                production_id,
                first_name,
                last_name,
                role)
            VALUES (?, ?, ?, ?)
            """, (production_id, name, surname, ROLE_ACTOR))

    conn.commit()

def auto_save_on_term_change(term):
    global last_second_letter
    if last_second_letter is None:
        last_second_letter = term[1]
        save_session()
        print(f"[AUTO-SAVE] İlk TERM için save yapıldı ({term})")
        return

    if term[1] != last_second_letter:
        save_session()
        print(f"[AUTO-SAVE] 2. harf değiştiği için save yapıldı ({last_second_letter} → {term[1]})")
        last_second_letter = term[1]

try:
    load_last_session()
    conn, cursor = connect_sqlite()
    create_tables(cursor)
    get_films(APPROX_FILM_COUNT, conn, cursor)

except KeyboardInterrupt:
    print("\n[INFO] Kullanıcı Ctrl+C ile programı durdurdu (main).")
    try:
        save_session()
    except:
        print("[ERROR]: save_session() Ctrl+C sırasında hata verdi")
    try:
        conn.commit()
    except:
        pass
    try:
        transfer_to_excel([])
    except:
        print("[ERROR] transfer_to_excel Ctrl+C sırasında çalışmadı")

except Exception as e:
    print(f"[FATAL ERROR]: {e}")
    try:
        save_session()
    except:
        print("[ERROR]: save_session() çağrılırken hata oluştu")
    try:
        conn.commit()
    except:
        pass

    try:
        transfer_to_excel([])
    except:
        print("[ERROR] transfer_to_excel çalışmadı")
finally:
    try:
        conn.close()
    except:
        pass
