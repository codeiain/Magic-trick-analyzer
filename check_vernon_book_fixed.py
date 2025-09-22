import sqlite3

conn = sqlite3.connect('data/magic_tricks.db')
cursor = conn.cursor()

# Check tricks table structure
cursor.execute("PRAGMA table_info(tricks)")
columns = cursor.fetchall()
print("=== Tricks Table Structure ===")
for col in columns:
    print(f"{col[1]}: {col[2]}")

print("\n" + "="*50)

# Find Dai Vernon book
cursor.execute("SELECT id, title, author, character_count, processed_at FROM books WHERE title LIKE '%Vernon%' OR title LIKE '%Dai%'")
books = cursor.fetchall()

if books:
    print("=== Dai Vernon Books Found ===")
    for book in books:
        book_id, title, author, char_count, processed_at = book
        print(f"ID: {book_id}")
        print(f"Title: {title}")
        print(f"Author: {author}")
        print(f"Character count: {char_count}")
        print(f"Processed at: {processed_at}")
        
        # Get tricks for this book using correct column names
        cursor.execute("SELECT id, name, description FROM tricks WHERE book_id = ? LIMIT 10", (book_id,))
        tricks = cursor.fetchall()
        print(f"Current tricks found: {len(tricks)}")
        
        if tricks:
            print("\n--- Current Tricks ---")
            for i, trick in enumerate(tricks, 1):
                trick_id, name, description = trick
                desc_preview = description[:100] if description else "No description"
                print(f"{i}. {name}")
                print(f"   Description: {desc_preview}...")
                print()
        
        print("=" * 50)
else:
    print("No Dai Vernon books found")

conn.close()