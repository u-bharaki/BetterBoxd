# user_manager.py

import sqlite3
import hashlib
import uuid
from typing import Optional, Dict, Any, List

# ana uygulamanızdaki get_db_path fonksiyonunun bir kopyası olarak kabul edin.

def _get_db_connection(db_path: str) -> sqlite3.Connection:
    """Tek bir DB bağlantısı oluşturur."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

class UserManager:
    def __init__(self, db_path: str, users_table_name: str = "users"):
        self.db_path = db_path
        self.users_table_name = users_table_name

    def _hash_password(self, password: str) -> str:
        """Parolayı SHA256 ile hashler."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Kullanıcı adıyla veritabanından kullanıcıyı getirir."""
        try:
            conn = _get_db_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"""
            SELECT id, username, password, email, first_name, last_name
            FROM "{self.users_table_name}"
            WHERE username = ?
            """, (username,))
            user = cursor.fetchone()
            conn.close()
            return dict(user) if user else None
        except Exception as e:
            print(f"UserManager DB Hatası (get_user): {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """E-posta adresiyle veritabanından kullanıcıyı kontrol eder."""
        try:
            conn = _get_db_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"""
            SELECT id, username, email
            FROM "{self.users_table_name}"
            WHERE email = ?
            """, (email,))
            user = cursor.fetchone()
            conn.close()
            return dict(user) if user else None
        except Exception as e:
            print(f"UserManager DB Hatası (get_user_by_email): {e}")
            return None

    def create_user(self, username: str, password: str, email: str, first_name: str, last_name: str) -> bool:
        """Yeni kullanıcıyı hashlenmiş şifreyle kaydeder."""
        if self.get_user_by_username(username):
            return False # Kullanıcı zaten var (IntegrityError'ı manuel kontrol ettik)

        hashed_password = self._hash_password(password)

        try:
            conn = _get_db_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f'''
            INSERT INTO {self.users_table_name} (id, username, password, email, first_name, last_name)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), username, hashed_password, email, first_name, last_name))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"UserManager DB Hatası (create_user): {e}")
            return False

    def check_password(self, user: Dict[str, Any], password: str) -> bool:
        """Girilen şifrenin hashlenmiş şifreyle eşleşip eşleşmediğini kontrol eder."""
        return user['password'] == self._hash_password(password)

    def username_exists(self, username: str) -> bool:
        user = self.get_user_by_username(username)
        return user is not None


    def email_exists(self, email: str) -> bool:
        user = self.get_user_by_email(email)
        return user is not None

    def update_username(self, old_username: str, new_username: str) -> bool:
        if self.username_exists(new_username):
            return False

        try:
            conn = _get_db_connection(self.db_path)
            cur = conn.cursor()
            cur.execute(f"""
            UPDATE {self.users_table_name}
            SET username = ?
            WHERE username = ?
            """, (new_username, old_username))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print("Username update error:", e)
            return False



    def update_email(self, username: str, new_email: str) -> bool:
        if self.email_exists(new_email):
            return False

        try:
            conn = _get_db_connection(self.db_path)
            cur = conn.cursor()
            cur.execute(f"""
            UPDATE {self.users_table_name}
            SET email = ?
            WHERE username = ?
            """, (new_email, username))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print("Email update error:", e)
            return False

    def update_password(self, username: str, new_pass: str) -> bool:
        hashed = self._hash_password(new_pass)

        try:
            conn = _get_db_connection(self.db_path)
            cur = conn.cursor()
            cur.execute(f"""
            UPDATE {self.users_table_name}
            SET password = ?
            WHERE username = ?
            """, (hashed, username))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print("Password update error:", e)
            return False
