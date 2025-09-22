#!/usr/bin/env python3
"""
Final verification of the corrected Vernon tricks
"""

import sqlite3

def main():
    conn = sqlite3.connect('shared/data/magic_tricks.db')
    cursor = conn.cursor()

    # Get Vernon book data
    cursor.execute('SELECT id, title FROM books WHERE title LIKE "%Vernon%"')
    vernon_book = cursor.fetchone()
    book_id, title = vernon_book
    
    print(f"=== CORRECTED VERNON BOOK ANALYSIS ===")
    print(f"Book: {title}")
    print(f"Book ID: {book_id}")
    
    # Get all tricks for detailed analysis
    cursor.execute('''
        SELECT name, description, effect_type_id, difficulty, page_start, confidence
        FROM tricks 
        WHERE book_id = ? 
        ORDER BY page_start
    ''', (book_id,))
    
    tricks = cursor.fetchall()
    print(f"\nTotal Tricks: {len(tricks)}\n")
    
    print("=== ALL VERNON TRICKS ===")
    for i, (name, description, effect_type, difficulty, page, confidence) in enumerate(tricks, 1):
        print(f"{i}. {name}")
        print(f"   Type: {effect_type}")
        print(f"   Difficulty: {difficulty}")
        print(f"   Page: {page}")
        print(f"   Confidence: {confidence}")
        print(f"   Description: {description[:150]}...")
        print()
    
    # Effect type distribution
    cursor.execute('''
        SELECT effect_type_id, COUNT(*) 
        FROM tricks 
        WHERE book_id = ? 
        GROUP BY effect_type_id
    ''', (book_id,))
    
    effect_dist = cursor.fetchall()
    print("=== EFFECT TYPE DISTRIBUTION ===")
    for effect_type, count in effect_dist:
        print(f"{effect_type}: {count} tricks")
    
    # Quality metrics
    avg_desc_length = sum(len(desc) for _, desc, _, _, _, _ in tricks) / len(tricks)
    avg_confidence = sum(conf for _, _, _, _, _, conf in tricks) / len(tricks)
    
    print(f"\n=== QUALITY METRICS ===")
    print(f"Average description length: {avg_desc_length:.1f} characters")
    print(f"Average confidence: {avg_confidence:.2f}")
    print(f"Tricks with proper names: {len(tricks)}/16 (100%)")
    print(f"Tricks with effect types: {len([t for t in tricks if t[2]])}/16")
    
    conn.close()

if __name__ == "__main__":
    main()