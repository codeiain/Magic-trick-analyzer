#!/usr/bin/env python3

import sqlite3
import uuid
from datetime import datetime

def fix_trick_ids():
    """Fix malformed trick IDs by replacing them with proper UUIDs"""
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = sqlite3.connect('shared/data/magic_tricks.db')
        cursor = conn.cursor()
        
        # Get all tricks with malformed IDs
        cursor.execute('SELECT id, book_id, name FROM tricks')
        tricks = cursor.fetchall()
        
        print(f"Found {len(tricks)} tricks to check")
        
        updates_made = 0
        for old_id, book_id, name in tricks:
            # Check if the ID is a proper UUID
            try:
                uuid.UUID(old_id)
                # If this succeeds, the ID is already a proper UUID
                continue
            except ValueError:
                # This ID is malformed, needs to be fixed
                new_id = str(uuid.uuid4())
                
                print(f"Updating trick: {name[:50]}... from {old_id} to {new_id}")
                
                # Update the trick ID
                cursor.execute('''
                    UPDATE tricks 
                    SET id = ?, updated_at = ?
                    WHERE id = ?
                ''', (new_id, datetime.utcnow().isoformat(), old_id))
                
                updates_made += 1
        
        # Commit changes
        conn.commit()
        print(f"Successfully updated {updates_made} trick IDs")
        
        # Verify the fix by counting tricks again
        cursor.execute('SELECT COUNT(*) FROM tricks')
        total_tricks = cursor.fetchone()[0]
        print(f"Total tricks in database: {total_tricks}")
        
        conn.close()
        print("Fix completed successfully!")
        
    except Exception as e:
        print(f"Error fixing trick IDs: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    fix_trick_ids()