from modules.database import Database

db = Database()

rows = db.cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()

print("========== DATABASE TABLES ==========")

for row in rows:
    print(row[0])

print(f"\nTOTAL TABLES: {len(rows)}")