#!/usr/bin/env python3

import sqlite3
import os

def check_tricks_schema():
    """Check the actual schema of the tricks table"""
    
    # Database path
    db_path = os.path.join("shared", "data", "magic_tricks.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tricks table schema
    cursor.execute("PRAGMA table_info(tricks)")
    print("Tricks table schema:")
    for row in cursor.fetchall():
        print(f"  Column: {row[1]}, Type: {row[2]}, NotNull: {row[3]}, Default: {row[4]}")
    print()
    
    # Check for tricks with NULL effect_type_id for Vernon book
    cursor.execute("""
        SELECT id, name, effect_type_id, description
        FROM tricks 
        WHERE book_id = 'a3a9f168-9778-4949-a20a-d0a07bdcd1ea'
        AND effect_type_id IS NULL
        LIMIT 10
    """)
    print("Vernon book tricks with NULL effect_type_id:")
    for row in cursor.fetchall():
        print(f"  ID: {row[0][:8]}..., Name: {row[1]}, Effect Type ID: {row[2]}")
        if row[3]:
            print(f"    Description: {row[3][:100]}...")
    print()
    
    # Check total count
    cursor.execute("""
        SELECT COUNT(*) FROM tricks 
        WHERE book_id = 'a3a9f168-9778-4949-a20a-d0a07bdcd1ea'
        AND effect_type_id IS NULL
    """)
    null_count = cursor.fetchone()[0]
    print(f"Total Vernon tricks with NULL effect_type_id: {null_count}")
    
    conn.close()

if __name__ == "__main__":
    check_tricks_schema()