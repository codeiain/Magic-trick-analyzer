#!/usr/bin/env python3
"""
Check books in database
"""

import sqlite3

def main():
    conn = sqlite3.connect('data/magic_tricks.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM books')
    books = cursor.fetchall()
    print('Books in database:')
    for book in books:
        trick_count = book[6] if len(book) > 6 else "N/A"
        print(f'ID: {book[0]}, Title: {book[1]}, Tricks: {trick_count}')
    conn.close()

if __name__ == "__main__":
    main()