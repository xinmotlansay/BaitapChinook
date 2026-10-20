import sqlite3

from config import DB_PATH


class Connector:
    """Quản lý một kết nối SQLite dùng chung cho toàn bộ DAO."""

    _conn = None

    @staticmethod
    def ensureConnection():
        """Trả về kết nối còn dùng được; mở lại nếu chưa có hoặc đã đóng."""
        if Connector._conn is not None:
            try:
                Connector._conn.execute("SELECT 1")
                return Connector._conn
            except sqlite3.ProgrammingError:
                Connector._conn = None

        Connector._conn = sqlite3.connect(DB_PATH)
        return Connector._conn

    @staticmethod
    def close():
        if Connector._conn is not None:
            Connector._conn.close()
            Connector._conn = None
