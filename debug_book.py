import sqlite3

conn = sqlite3.connect('data/magic_tricks.db')
cursor = conn.cursor()

# Find the problem book
cursor.execute("SELECT id, title, file_path, character_count, length(text_content) as text_len FROM books WHERE character_count = 0 OR character_count IS NULL ORDER BY created_at DESC LIMIT 3")
print("Books with missing text:")
for row in cursor.fetchall():
    print(f"ID: {row[0][:8]}...")
    print(f"Title: {row[1]}")
    print(f"File path: {row[2]}")
    print(f"Character count: {row[3]}")
    print(f"Actual text length: {row[4]}")
    print("---")

conn.close()