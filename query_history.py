import sqlite3
from datetime import datetime
import os


class QueryHistory:
    def __init__(self):
        self.db_path = "query_history.db"
        self._initialize_db()

    def _initialize_db(self):
        """Create the database and tables if they don't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT NOT NULL,
            execution_time TIMESTAMP NOT NULL,
            execution_duration REAL NOT NULL,
            success BOOLEAN NOT NULL
        )
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(create_table_sql)
            conn.commit()

    def add_query(self, query_text, duration, success):
        """Add a query to the history"""
        insert_sql = """
        INSERT INTO query_history (query_text, execution_time, execution_duration, success)
        VALUES (?, ?, ?, ?)
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                insert_sql, (query_text, datetime.now().isoformat(), duration, success)
            )
            conn.commit()

    def get_query_history(self, limit=100):
        """Retrieve the most recent queries"""
        select_sql = """
        SELECT query_text, execution_time, execution_duration, success
        FROM query_history
        ORDER BY execution_time DESC
        LIMIT ?
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(select_sql, (limit,))
            return cursor.fetchall()

    def get_full_query(self, partial_query):
        """Retrieve the full query text given a partial match"""
        select_sql = """
        SELECT query_text
        FROM query_history
        WHERE query_text LIKE ?
        ORDER BY execution_time DESC
        LIMIT 1
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(select_sql, (partial_query.replace("...", "") + "%",))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_history(self):
        """Return the full query history"""
        return self.get_query_history()

    def clear_history(self):
        """Clear all query history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM query_history")
            conn.commit()
