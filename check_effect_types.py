#!/usr/bin/env python3
"""
Check effect type data in the database
"""

import sqlite3

def main():
    conn = sqlite3.connect('shared/data/magic_tricks.db')
    cursor = conn.cursor()

    # Check the effect_type_id values in tricks
    cursor.execute('SELECT id, name, effect_type_id FROM tricks WHERE book_id = ? LIMIT 5', 
                   ('a3a9f168-9778-4949-a20a-d0a07bdcd1ea',))
    tricks = cursor.fetchall()
    print('Sample tricks with effect types:')
    for trick in tricks:
        print(f'ID: {trick[0][:8]}..., Name: {trick[1]}, Effect Type: {trick[2]}')

    # Check what's in the effect_types table
    cursor.execute('SELECT * FROM effect_types')
    effect_types = cursor.fetchall()
    print('\nEffect types table:')
    for et in effect_types:
        print(f'ID: {et[0]}, Name: {et[1] if len(et) > 1 else "N/A"}')

    # Check the schema of effect_types
    cursor.execute('PRAGMA table_info(effect_types)')
    schema = cursor.fetchall()
    print('\nEffect types table schema:')
    for col in schema:
        print(f'Column: {col[1]}, Type: {col[2]}')

    conn.close()

if __name__ == "__main__":
    main()