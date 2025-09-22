import sqlite3

conn = sqlite3.connect('data/magic_tricks.db')
cursor = conn.cursor()

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
        
        # Get tricks for this book
        cursor.execute("SELECT id, name, effect_type, description[:100], confidence FROM tricks WHERE book_id = ?", (book_id,))
        tricks = cursor.fetchall()
        print(f"Current tricks found: {len(tricks)}")
        
        if tricks:
            print("\n--- Current Tricks ---")
            for i, trick in enumerate(tricks, 1):
                trick_id, name, effect_type, desc_preview, confidence = trick
                print(f"{i}. {name}")
                print(f"   Type: {effect_type}")
                print(f"   Description: {desc_preview}...")
                print(f"   Confidence: {confidence}")
                print()
        
        print("=" * 50)
else:
    print("No Dai Vernon books found")

conn.close()