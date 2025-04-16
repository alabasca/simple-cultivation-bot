# database/db_handler.py
import sqlite3
from datetime import datetime
import os


class Database:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_file = os.path.join(current_dir, "cultivator.db")
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)

    def connect(self):
        return sqlite3.connect(self.db_file)

    def setup(self):
        """Khởi tạo database với đầy đủ các bảng và cột"""
        conn = self.connect()
        c = conn.cursor()

        try:
            # Tạo bảng players với đầy đủ các cột
            c.execute('''CREATE TABLE IF NOT EXISTS players
                        (user_id INTEGER PRIMARY KEY,
                         level TEXT,
                         exp INTEGER,
                         sect TEXT,
                         hp INTEGER,
                         attack INTEGER,
                         defense INTEGER,
                         last_train TEXT,
                         last_monster TEXT,
                         last_boss TEXT,
                         last_daily TEXT,
                         daily_streak INTEGER DEFAULT 0)''')

            # Tạo bảng combat_history nếu cần
            c.execute('''CREATE TABLE IF NOT EXISTS combat_history
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         attacker_id INTEGER,
                         defender_id INTEGER,
                         winner_id INTEGER,
                         exp_gained INTEGER,
                         timestamp TEXT)''')

            conn.commit()
            print("✓ Đã tạo database thành công!")

        except sqlite3.Error as e:
            print(f"❌ Lỗi khi tạo database: {e}")
        finally:
            conn.close()

    def create_player(self, user_id, sect):
        """Tạo người chơi mới với đầy đủ thông tin"""
        conn = self.connect()
        c = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            c.execute("""INSERT INTO players 
                        (user_id, level, exp, sect, hp, attack, defense,
                         last_train, last_monster, last_boss, last_daily, daily_streak)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (user_id, "Phàm Nhân", 0, sect, 100, 10, 5,
                       current_time, current_time, current_time, current_time, 0))

            conn.commit()
            print(f"✓ Đã tạo người chơi mới: {user_id}")

        except sqlite3.Error as e:
            print(f"❌ Lỗi khi tạo người chơi: {e}")
            raise e
        finally:
            conn.close()

    def get_player(self, user_id):
        """Lấy thông tin người chơi"""
        conn = self.connect()
        c = conn.cursor()
        try:
            c.execute("SELECT * FROM players WHERE user_id=?", (user_id,))
            return c.fetchone()
        finally:
            conn.close()

    def update_player(self, user_id, **kwargs):
        """Cập nhật thông tin người chơi"""
        conn = self.connect()
        c = conn.cursor()

        try:
            updates = []
            values = []
            for key, value in kwargs.items():
                if key in ['last_train', 'last_monster', 'last_boss', 'last_daily']:
                    if isinstance(value, datetime):
                        value = value.strftime('%Y-%m-%d %H:%M:%S')
                updates.append(f"{key}=?")
                values.append(value)

            if updates:
                query = f"UPDATE players SET {', '.join(updates)} WHERE user_id=?"
                values.append(user_id)
                c.execute(query, values)
                conn.commit()

        except sqlite3.Error as e:
            print(f"❌ Lỗi khi cập nhật người chơi: {e}")
            raise e
        finally:
            conn.close()

    def get_time_from_db(self, time_str):
        """Chuyển đổi thời gian từ database sang datetime"""
        try:
            return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return datetime.now()

    def get_daily_data(self, user_id):
        """Lấy thông tin điểm danh của người chơi"""
        conn = self.connect()
        c = conn.cursor()
        try:
            c.execute("SELECT last_daily, daily_streak FROM players WHERE user_id=?", (user_id,))
            data = c.fetchone()
            return data if data else (None, 0)
        finally:
            conn.close()

    def update_daily_streak(self, user_id, streak):
        """Cập nhật chuỗi điểm danh"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.update_player(user_id, last_daily=current_time, daily_streak=streak)

    def get_all_players(self):
        """Lấy thông tin tất cả người chơi"""
        conn = self.connect()
        c = conn.cursor()
        try:
            c.execute("SELECT * FROM players")
            return c.fetchall()
        finally:
            conn.close()

    def get_top_players(self, limit=10):
        """Lấy top người chơi theo exp"""
        conn = self.connect()
        c = conn.cursor()
        try:
            c.execute("SELECT * FROM players ORDER BY exp DESC LIMIT ?", (limit,))
            return c.fetchall()
        finally:
            conn.close()
