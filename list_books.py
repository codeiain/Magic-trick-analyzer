#!/usr/bin/env python3

import sqlite3

def list_books():
    conn = sqlite3.connect('data/magic_tricks.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title, author, character_count FROM books')
    books = cursor.fetchall()
    
    print("Books in database:")
    for book in books:
        print(f"ID: {book[0]}")
        print(f"Title: {book[1]}")
        print(f"Author: {book[2]}")
        print(f"Character count: {book[3]}")
        print("---")
    
    print(f"Total books: {len(books)}")
    conn.close()

if __name__ == "__main__":
    list_books()