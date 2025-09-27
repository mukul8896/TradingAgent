import sqlite3
from datetime import datetime

class PortfolioStore:
    def __init__(self, db_path="portfolio/portfolio.db"):
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            side TEXT,
            qty REAL,
            price REAL,
            strategy TEXT,
            timestamp TEXT
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            ticker TEXT PRIMARY KEY,
            qty REAL,
            avg_price REAL,
            strategy TEXT
        )""")
        self.conn.commit()

    def save_trade(self, ticker, side, qty, price, strategy):
        ts = datetime.utcnow().isoformat()
        self.conn.execute(
            "INSERT INTO trades (ticker, side, qty, price, strategy, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (ticker, side, qty, price, strategy, ts)
        )
        self.conn.commit()

    def update_position(self, ticker, side, qty, price, strategy):
        cur = self.conn.cursor()
        cur.execute("SELECT qty, avg_price FROM positions WHERE ticker=?", (ticker,))
        row = cur.fetchone()

        if side == "BUY":
            if row:
                old_qty, old_price = row
                new_qty = old_qty + qty
                new_avg = (old_qty * old_price + qty * price) / new_qty
                cur.execute("UPDATE positions SET qty=?, avg_price=? WHERE ticker=?",
                            (new_qty, new_avg, ticker))
            else:
                cur.execute("INSERT INTO positions (ticker, qty, avg_price, strategy) VALUES (?, ?, ?, ?)",
                            (ticker, qty, price, strategy))
        elif side == "SELL" and row:
            old_qty, old_price = row
            new_qty = max(old_qty - qty, 0)
            if new_qty == 0:
                cur.execute("DELETE FROM positions WHERE ticker=?", (ticker,))
            else:
                cur.execute("UPDATE positions SET qty=? WHERE ticker=?", (new_qty, ticker))
        self.conn.commit()

    def load_positions(self):
        cur = self.conn.cursor()
        cur.execute("SELECT ticker, qty, avg_price, strategy FROM positions")
        return cur.fetchall()
