import sqlite3

conn = sqlite3.connect('backend/satquery.db')
c = conn.cursor()
try:
    c.execute("ALTER TABLE users ADD COLUMN full_name VARCHAR DEFAULT 'SatQuery User';")
    c.execute("ALTER TABLE users ADD COLUMN username VARCHAR DEFAULT '@satquery_user';")
    conn.commit()
    print("Columns added successfully.")
except Exception as e:
    print("Error or already exists:", e)
conn.close()
