import sqlite3

def init_db():
    conn = sqlite3.connect("scrim_handler.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS scrims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team1 TEXT,
        team2 TEXT,
        tier TEXT,
        maps TEXT,
        rounds INTEGER,
        format TEXT,
        status TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        manager_id INTEGER,
        ceo_id INTEGER,
        captain_id INTEGER,
        players TEXT,
        tier TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_id INTEGER,
        target TEXT,
        reason TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()
