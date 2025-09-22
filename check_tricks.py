#!/usr/bin/env python3

import sqlite3
import json
from datetime import datetime, timedelta

def check_recent_tricks():
    """Check for tricks created in the last hour"""
    conn = sqlite3.connect('shared/data/magic_tricks.db')
    cursor = conn.cursor()
    
    # Get book info
    cursor.execute('SELECT id, title, author FROM books WHERE title LIKE "%Dai Vernon%"')
    vernon_book = cursor.fetchone()
    if not vernon_book:
        print("No Dai Vernon book found")
        return
    
    book_id, title, author = vernon_book
    print(f"Book: {title} by {author}")
    print(f"Book ID: {book_id}")
    
    # Count total tricks for this book
    cursor.execute('SELECT COUNT(*) FROM tricks WHERE book_id = ?', (book_id,))
    total_tricks = cursor.fetchone()[0]
    print(f"Total tricks: {total_tricks}")
    
    # Check recent tricks (last 2 hours)
    two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()
    cursor.execute('''
        SELECT name, difficulty, confidence, created_at 
        FROM tricks 
        WHERE book_id = ? AND created_at > ?
        ORDER BY created_at DESC
        LIMIT 10
    ''', (book_id, two_hours_ago))
    
    recent_tricks = cursor.fetchall()
    print(f"\nRecent tricks (last 2 hours): {len(recent_tricks)}")
    for trick in recent_tricks:
        print(f"  - {trick[0]} (Difficulty: {trick[1]}, Confidence: {trick[2]}, Created: {trick[3]})")
    
    # Show existing tricks
    cursor.execute('SELECT name, created_at FROM tricks WHERE book_id = ? ORDER BY created_at DESC', (book_id,))
    all_tricks = cursor.fetchall()
    print(f"\nAll tricks for this book: {len(all_tricks)}")
    for trick in all_tricks:
        print(f"  - {trick[0]} (Created: {trick[1]})")
    
    conn.close()

if __name__ == "__main__":
    check_recent_tricks()