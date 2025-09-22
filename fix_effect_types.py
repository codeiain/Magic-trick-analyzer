#!/usr/bin/env python3

import sqlite3
import os

def fix_effect_types():
    """Fix the effect type mapping for tricks to use proper effect_type_id values"""
    
    # Database path
    db_path = os.path.join("shared", "data", "magic_tricks.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create a mapping from our algorithm's effect types to database effect types
    effect_type_mapping = {
        'card_magic': 'Card',
        'coin_magic': 'Coin', 
        'mentalism': 'Mentalism',
        'close_up': 'Close-Up',
        'stage_magic': 'Stage Magic',
        'rope_magic': 'Rope',
        'silk_magic': 'Silk',
        'ring_magic': 'Ring',
        'ball_magic': 'Ball',
        'paper_magic': 'Paper',
        'money_magic': 'Money',
        'restoration': 'Restoration',
        'vanish': 'Vanish',
        'production': 'Production',
        'transformation': 'Transformation',
        'transposition': 'Transposition',
        'penetration': 'Penetration',
        'levitation': 'Levitation',
        'prediction': 'Prediction',
        'mind_reading': 'Mind Reading',
        'linking_rings': 'Ring',  # Map linking rings to Ring category
        'general': 'General'
    }
    
    # Get effect type IDs from database
    cursor.execute("SELECT id, name FROM effect_types")
    effect_types = {name: id for id, name in cursor.fetchall()}
    print("Available effect types:")
    for name, id in effect_types.items():
        print(f"  {name}: {id}")
    print()
    
    # Find tricks with invalid effect_type_id values (string instead of UUID)
    cursor.execute("SELECT id, name, effect_type_id FROM tricks WHERE book_id = 'a3a9f168-9778-4949-a20a-d0a07bdcd1ea'")
    tricks_to_fix = []
    
    for trick_id, name, effect_type_id in cursor.fetchall():
        if effect_type_id in effect_type_mapping:
            mapped_type = effect_type_mapping[effect_type_id]
            if mapped_type in effect_types:
                new_effect_type_id = effect_types[mapped_type]
                tricks_to_fix.append((trick_id, name, effect_type_id, new_effect_type_id))
            else:
                print(f"Warning: Mapped type '{mapped_type}' not found in database")
        else:
            print(f"Warning: Unknown effect type '{effect_type_id}' for trick '{name}'")
    
    print(f"Found {len(tricks_to_fix)} tricks to fix:")
    for trick_id, name, old_type, new_id in tricks_to_fix:
        print(f"  {name}: {old_type} -> {new_id}")
    print()
    
    # Update the tricks with proper effect_type_id values
    if tricks_to_fix:
        for trick_id, name, old_type, new_id in tricks_to_fix:
            cursor.execute("""
                UPDATE tricks 
                SET effect_type_id = ? 
                WHERE id = ?
            """, (new_id, trick_id))
        
        conn.commit()
        print(f"Successfully updated {len(tricks_to_fix)} tricks with proper effect_type_id values")
    else:
        print("No tricks to fix")
    
    # Verify the fix
    print("\nVerification - checking tricks with NULL effect_type_id:")
    cursor.execute("""
        SELECT COUNT(*) FROM tricks 
        WHERE book_id = 'a3a9f168-9778-4949-a20a-d0a07bdcd1ea' 
        AND effect_type_id IS NULL
    """)
    null_count = cursor.fetchone()[0]
    print(f"Tricks with NULL effect_type_id: {null_count}")
    
    # Show sample of fixed tricks
    print("\nSample of fixed tricks:")
    cursor.execute("""
        SELECT t.name, et.name as effect_type_name
        FROM tricks t
        JOIN effect_types et ON t.effect_type_id = et.id
        WHERE t.book_id = 'a3a9f168-9778-4949-a20a-d0a07bdcd1ea'
        LIMIT 5
    """)
    for name, effect_type_name in cursor.fetchall():
        print(f"  {name}: {effect_type_name}")
    
    conn.close()

if __name__ == "__main__":
    fix_effect_types()