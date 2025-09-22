import sqlite3

conn = sqlite3.connect('data/magic_tricks.db')
cursor = conn.cursor()

# Get Dai Vernon book text content
cursor.execute("SELECT id, text_content FROM books WHERE title LIKE '%Vernon%'")
book = cursor.fetchone()

if book:
    book_id, text_content = book
    print(f"Book ID: {book_id}")
    print(f"Text length: {len(text_content) if text_content else 0}")
    print("\n=== First 1000 characters ===")
    print(text_content[:1000] if text_content else "No text content")
    print("\n=== Last 1000 characters ===")
    print(text_content[-1000:] if text_content else "No text content")
    
    # Look for potential trick names or sections
    print("\n=== Sample sections (looking for potential tricks) ===")
    lines = text_content.split('\n') if text_content else []
    trick_indicators = ['trick', 'effect', 'routine', 'method', 'handling', 'technique']
    
    sample_lines = []
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(indicator in line_lower for indicator in trick_indicators) and len(line.strip()) > 10:
            sample_lines.append(f"Line {i+1}: {line.strip()[:100]}")
            if len(sample_lines) >= 10:
                break
    
    for sample in sample_lines:
        print(sample)
        
else:
    print("Vernon book not found")

conn.close()