import sqlite3

conn = sqlite3.connect('data/magic_tricks.db')
cursor = conn.cursor()

# Get Vernon book text content
cursor.execute("SELECT text_content FROM books WHERE title LIKE '%Vernon%'")
book = cursor.fetchone()

if book:
    text_content = book[0]
    
    # Current indicators from AI processor
    trick_indicators = [
        'effect:', 'method:', 'preparation:', 'performance:',
        'the trick', 'the effect', 'the method', 'the secret',
        'vanish', 'appear', 'transform', 'prediction'
    ]
    
    # Check how many paragraphs contain these indicators
    paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
    print(f"Total paragraphs: {len(paragraphs)}")
    
    matches = []
    for i, paragraph in enumerate(paragraphs):
        if len(paragraph) >= 50:  # Same filter as AI
            paragraph_lower = paragraph.lower()
            if any(indicator in paragraph_lower for indicator in trick_indicators):
                matches.append((i, paragraph[:200]))
    
    print(f"Paragraphs matching current indicators: {len(matches)}")
    print("\n=== First 10 matches ===")
    for i, (para_num, preview) in enumerate(matches[:10]):
        print(f"{i+1}. Paragraph {para_num}: {preview}...")
        print()
    
    # Look for better indicators that might be in the Vernon book
    print("\n=== Looking for better indicators ===")
    
    # Count occurrences of potential better indicators
    better_indicators = {
        'routine': text_content.lower().count('routine'),
        'handling': text_content.lower().count('handling'), 
        'technique': text_content.lower().count('technique'),
        'presentation': text_content.lower().count('presentation'),
        'working': text_content.lower().count('working'),
        'procedure': text_content.lower().count('procedure'),
        'explanation': text_content.lower().count('explanation'),
        'approach': text_content.lower().count('approach'),
        'version': text_content.lower().count('version'),
        'variation': text_content.lower().count('variation')
    }
    
    print("Frequency of potential indicators:")
    for indicator, count in sorted(better_indicators.items(), key=lambda x: x[1], reverse=True):
        print(f"  {indicator}: {count} occurrences")

else:
    print("Vernon book not found")

conn.close()