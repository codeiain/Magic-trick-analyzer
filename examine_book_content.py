#!/usr/bin/env python3
"""
Examine actual book content to find real tricks
"""

import sqlite3
import re

def main():
    conn = sqlite3.connect('shared/data/magic_tricks.db')
    cursor = conn.cursor()

    # Get the book's text content to examine
    cursor.execute('SELECT text_content FROM books WHERE title LIKE "%Vernon%"')
    book_content = cursor.fetchone()[0]

    print('Book content length:', len(book_content))
    
    # Look for chapter patterns that might indicate actual tricks
    chapter_matches = re.finditer(r'CHAPTER\s+[A-Z]+[\.—]([^\.]+)', book_content, re.IGNORECASE)
    print('\n=== CHAPTERS FOUND ===')
    chapters = []
    for match in chapter_matches:
        chapter_title = match.group(1).strip()
        position = match.start()
        chapters.append((chapter_title, position))
        print(f'Position {position}: CHAPTER - {chapter_title}')
    
    # Look for actual magic trick patterns
    print('\n=== LOOKING FOR ACTUAL TRICKS ===')
    
    # Search for classic Vernon tricks
    classic_tricks = [
        'THE AMBITIOUS CARD', 'TWISTING THE ACES', 'TRIUMPH', 'CUPS AND BALLS', 
        'SPELLBOUND', 'THE FOUR ACES', 'MENTAL SELECTION', 'CARD IN WALLET',
        'TRAVELLERS', 'OIL AND WATER', 'CHINK-A-CHINK'
    ]
    
    found_tricks = []
    for trick_name in classic_tricks:
        pos = book_content.find(trick_name)
        if pos != -1:
            found_tricks.append((trick_name, pos))
            print(f'Found "{trick_name}" at position {pos}')
    
    # Look for patterns that indicate actual trick descriptions
    trick_patterns = [
        r'EFFECT[:\s]+(.*?)(?=METHOD|PREPARATION|PERFORMANCE)',
        r'METHOD[:\s]+(.*?)(?=EFFECT|PRESENTATION|PERFORMANCE)',
        r'The effect is[:\s]+(.*?)(?=The method|Method|Preparation)',
        r'[A-Z][a-z]+ performs? this trick'
    ]
    
    print('\n=== SEARCHING FOR TRICK STRUCTURE PATTERNS ===')
    all_matches = []
    for pattern in trick_patterns:
        matches = re.finditer(pattern, book_content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            all_matches.append((match.start(), match.group(0)[:100]))
    
    # Sort by position and show first few
    all_matches.sort()
    for pos, text in all_matches[:10]:
        print(f'Position {pos}: {text}...')
    
    # Let's also check what's around page 50-100 where tricks might be
    mid_section = book_content[50000:100000]  # Approximately middle section
    print('\n=== SAMPLE FROM MIDDLE SECTION (chars 50000-100000) ===')
    print(mid_section[:1000])
    
    conn.close()

if __name__ == "__main__":
    main()