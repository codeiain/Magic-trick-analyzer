#!/usr/bin/env python3
"""
Review and analyze tricks from The Dai Vernon Book of Magic
"""

import sqlite3

def main():
    conn = sqlite3.connect('shared/data/magic_tricks.db')
    cursor = conn.cursor()

    # Get Vernon book ID
    cursor.execute("SELECT id, title FROM books WHERE title LIKE '%Vernon%'")
    vernon_book = cursor.fetchone()
    book_id = vernon_book[0]
    print(f"Book: {vernon_book[1]}")
    print(f"Book ID: {book_id}")

    # Get first 20 tricks to analyze quality
    cursor.execute('''
        SELECT id, name, description, page_start, page_end, effect_type_id, difficulty, confidence 
        FROM tricks 
        WHERE book_id = ? 
        ORDER BY page_start 
        LIMIT 20
    ''', (book_id,))

    tricks = cursor.fetchall()
    print(f'\n=== FIRST 20 VERNON TRICKS ===')
    
    issues = []
    for i, trick in enumerate(tricks, 1):
        print(f'\n{i}. NAME: {trick[1]}')
        print(f'   Pages: {trick[3]}-{trick[4]}')
        print(f'   Effect: {trick[5]}')
        print(f'   Difficulty: {trick[6]}')
        print(f'   Confidence: {trick[7]}')
        print(f'   Description: {trick[2][:200]}...')
        
        # Identify potential issues
        if trick[1].startswith('--- Page'):
            issues.append(f"Trick {i}: Generic page title '{trick[1]}'")
        if len(trick[2]) < 100:
            issues.append(f"Trick {i}: Short description ({len(trick[2])} chars)")
        if not trick[5] or trick[5] == 'unknown':
            issues.append(f"Trick {i}: No effect type")

    # Get effect type distribution
    cursor.execute('''
        SELECT effect_type_id, COUNT(*) 
        FROM tricks 
        WHERE book_id = ? 
        GROUP BY effect_type_id 
        ORDER BY COUNT(*) DESC
    ''', (book_id,))
    
    effects = cursor.fetchall()
    print(f'\n=== EFFECT TYPE DISTRIBUTION ===')
    for effect, count in effects:
        print(f'{effect}: {count} tricks')

    # Check for problematic titles
    cursor.execute('''
        SELECT COUNT(*) FROM tricks 
        WHERE book_id = ? AND name LIKE '--- Page%'
    ''', (book_id,))
    
    page_titles = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM tricks 
        WHERE book_id = ? AND LENGTH(description) < 100
    ''', (book_id,))
    
    short_descriptions = cursor.fetchone()[0]

    print(f'\n=== QUALITY ANALYSIS ===')
    print(f'Total tricks: {len(tricks)} (showing first 20)')
    print(f'Tricks with page-reference titles: {page_titles}')
    print(f'Tricks with short descriptions (<100 chars): {short_descriptions}')
    
    if issues:
        print(f'\n=== IDENTIFIED ISSUES ===')
        for issue in issues:
            print(f'- {issue}')

    # Get some examples of potentially good vs bad tricks
    cursor.execute('''
        SELECT name, description, page_start, confidence
        FROM tricks 
        WHERE book_id = ? AND name NOT LIKE '--- Page%' AND LENGTH(description) > 200
        ORDER BY confidence DESC
        LIMIT 5
    ''', (book_id,))
    
    good_tricks = cursor.fetchall()
    print(f'\n=== BEST QUALITY TRICKS ===')
    for trick in good_tricks:
        print(f'\nNAME: {trick[0]}')
        print(f'PAGE: {trick[2]}')
        print(f'CONFIDENCE: {trick[3]}')
        print(f'DESCRIPTION: {trick[1][:300]}...')

    conn.close()

if __name__ == "__main__":
    main()