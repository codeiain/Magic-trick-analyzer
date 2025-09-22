#!/usr/bin/env python3

import sqlite3
import os

def test_api_query():
    """Test the exact query the API would run to fetch tricks"""
    
    # Database path
    db_path = os.path.join("shared", "data", "magic_tricks.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get Vernon book info
    cursor.execute("SELECT id, title FROM books WHERE id = 'a3a9f168-9778-4949-a20a-d0a07bdcd1ea'")
    book_info = cursor.fetchone()
    print(f"Book: {book_info}")
    print()
    
    # Query tricks as the API would
    cursor.execute("""
        SELECT 
            t.id,
            t.name,
            t.description,
            t.effect_type_id,
            et.name as effect_type_name,
            t.difficulty,
            t.page_start,
            t.page_end
        FROM tricks t
        LEFT JOIN effect_types et ON t.effect_type_id = et.id
        WHERE t.book_id = 'a3a9f168-9778-4949-a20a-d0a07bdcd1ea'
        ORDER BY t.page_start
    """)
    
    print("Vernon book tricks with joined effect types:")
    for row in cursor.fetchall():
        trick_id, name, description, effect_type_id, effect_type_name, difficulty, page_start, page_end = row
        print(f"  ID: {trick_id[:8]}...")
        print(f"  Name: {name}")
        print(f"  Effect Type ID: {effect_type_id}")
        print(f"  Effect Type Name: {effect_type_name}")
        print(f"  Difficulty: {difficulty}")
        print(f"  Pages: {page_start}-{page_end}")
        print()
        
        if effect_type_name is None:
            print(f"  WARNING: effect_type_name is None for trick '{name}'!")
            print(f"  effect_type_id = {effect_type_id}")
            # Check if this effect_type_id exists in effect_types table
            cursor.execute("SELECT name FROM effect_types WHERE id = ?", (effect_type_id,))
            result = cursor.fetchone()
            if result is None:
                print(f"  ERROR: effect_type_id '{effect_type_id}' not found in effect_types table!")
            else:
                print(f"  Found effect type: {result[0]}")
            print()
    
    conn.close()

if __name__ == "__main__":
    test_api_query()