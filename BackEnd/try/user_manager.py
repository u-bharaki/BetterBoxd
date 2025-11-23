# user_manager.py

import sqlite3
import hashlib
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

    def create_user(self, username: str, password: str, email: str, first_name: str, last_name: str) -> bool:
        """Yeni kullanıcıyı hashlenmiş şifreyle kaydeder."""
        if self.get_user_by_username(username):
            return False # Kullanıcı zaten var (IntegrityError'ı manuel kontrol ettik)

        hashed_password = self._hash_password(password)

        try:
            conn = _get_db_connection(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f'''
            INSERT INTO {self.users_table_name} (username, password, email, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
            ''', (username, hashed_password, email, first_name, last_name))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"UserManager DB Hatası (create_user): {e}")
            return False

    def check_password(self, user: Dict[str, Any], password: str) -> bool:
        """Girilen şifrenin hashlenmiş şifreyle eşleşip eşleşmediğini kontrol eder."""
        return user['password'] == self._hash_password(password)