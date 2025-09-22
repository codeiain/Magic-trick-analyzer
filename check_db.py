#!/usr/bin/env python3
"""
Check database structure and content
"""

import sqlite3

def main():
    conn = sqlite3.connect('data/magic_tricks.db')
    cursor = conn.cursor()

    # Check what tables exist
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    print('Tables in database:')
    for table in tables:
        print(f'- {table[0]}')

    # Check tricks table
    cursor.execute('SELECT COUNT(*) FROM tricks')
    trick_count = cursor.fetchone()[0]
    print(f'\nTotal tricks: {trick_count}')

    # Sample some tricks with more details
    cursor.execute('''SELECT id, title, description, book_id, page_number, effect_type, difficulty 
                     FROM tricks ORDER BY book_id, page_number LIMIT 10''')
    sample_tricks = cursor.fetchall()
    print('\nFirst 10 tricks:')
    for i, trick in enumerate(sample_tricks, 1):
        print(f'\n{i}. ID: {trick[0][:8]}...')
        print(f'   Book ID: {trick[3]}')
        print(f'   Page: {trick[4]}')
        print(f'   Effect: {trick[5]}')
        print(f'   Difficulty: {trick[6]}')
        print(f'   Title: {trick[1][:80]}...')
        print(f'   Description: {trick[2][:150]}...')

    conn.close()

if __name__ == "__main__":
    main()