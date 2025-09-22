#!/usr/bin/env python3

import sqlite3
import os

def fix_cups_and_balls():
    """Fix the remaining trick with unmapped effect type"""
    
    # Database path
    db_path = os.path.join("shared", "data", "magic_tricks.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Find "The Cups And Balls" trick
    cursor.execute("""
        SELECT id, name, effect_type_id 
        FROM tricks 
        WHERE name = 'The Cups And Balls'
    """)
    trick = cursor.fetchone()
    
    if trick:
        trick_id, name, effect_type_id = trick
        print(f"Found trick: {name} with effect_type_id: {effect_type_id}")
        
        # Cups and Balls should probably be "Stage Magic" or we could use "General"
        # Let's use "Stage Magic" as it's a classic stage magic effect
        cursor.execute("SELECT id FROM effect_types WHERE name = 'Stage Magic'")
        stage_magic_id = cursor.fetchone()[0]
        
        cursor.execute("UPDATE tricks SET effect_type_id = ? WHERE id = ?", (stage_magic_id, trick_id))
        conn.commit()
        
        print(f"Updated '{name}' to use Stage Magic effect type: {stage_magic_id}")
    else:
        print("Trick 'The Cups And Balls' not found")
    
    conn.close()

if __name__ == "__main__":
    fix_cups_and_balls()