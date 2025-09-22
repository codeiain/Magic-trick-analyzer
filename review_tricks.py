#!/usr/bin/env python3
"""
Review tricks in the database and compare with actual content
"""

import sqlite3
import json

def main():
    # Connect to the database
    conn = sqlite3.connect('data/magic_tricks.db')
    cursor = conn.cursor()

    # Get the Vernon book info
    cursor.execute("SELECT * FROM books WHERE title LIKE '%Vernon%'")
    book = cursor.fetchone()
    print(f'Book: {book[1]} (ID: {book[0]})')
    print(f'Tricks in book: {book[6]}')

    # Get some sample tricks
    cursor.execute('''
        SELECT id, title, description, page_number, effect_type, difficulty 
        FROM tricks 
        WHERE book_id = ? 
        ORDER BY page_number 
        LIMIT 15
    ''', (book[0],))

    tricks = cursor.fetchall()
    print('\n=== FIRST 15 TRICKS IN DATABASE ===')
    for i, trick in enumerate(tricks, 1):
        print(f'\n{i}. ID: {trick[0][:8]}...')
        print(f'   Title: {trick[1][:100]}...')
        print(f'   Page: {trick[3]}')
        print(f'   Effect: {trick[4]}')
        print(f'   Difficulty: {trick[5]}')
        print(f'   Description: {trick[2][:300]}...')

    # Get some statistics
    cursor.execute('''
        SELECT effect_type, COUNT(*) 
        FROM tricks 
        WHERE book_id = ? 
        GROUP BY effect_type 
        ORDER BY COUNT(*) DESC
    ''', (book[0],))
    
    effects = cursor.fetchall()
    print('\n=== EFFECT TYPE DISTRIBUTION ===')
    for effect, count in effects:
        print(f'{effect}: {count} tricks')

    # Check for issues
    cursor.execute('''
        SELECT COUNT(*) FROM tricks 
        WHERE book_id = ? AND (title IS NULL OR title = '' OR title LIKE '--- Page%')
    ''', (book[0],))
    
    bad_titles = cursor.fetchone()[0]
    print(f'\n=== POTENTIAL ISSUES ===')
    print(f'Tricks with poor titles (page references): {bad_titles}')

    conn.close()

if __name__ == "__main__":
    main()