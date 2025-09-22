#!/usr/bin/env python3

import sys
import os
import sqlite3
from datetime import datetime

# Add the AI service path so we can import the processor
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from ai_processor import AIProcessor

def manual_reprocess_vernon():
    """Manually reprocess the Dai Vernon book to test our enhancements"""
    
    try:
        # Connect to database and get Vernon book content
        print("Connecting to database...")
        db_path = '/app/data/magic_tricks.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the Vernon book
        cursor.execute('''
            SELECT id, title, text_content 
            FROM books 
            WHERE title LIKE "%Dai Vernon%"
        ''')
        
        result = cursor.fetchone()
        if not result:
            print("No Dai Vernon book found!")
            return
        
        book_id, title, text_content = result
        print(f"Found book: {title}")
        print(f"Book ID: {book_id}")
        print(f"Text length: {len(text_content)} characters")
        
        # Clear existing tricks first
        print("Clearing existing tricks...")
        cursor.execute("DELETE FROM tricks WHERE book_id = ?", (book_id,))
        deleted_count = cursor.rowcount
        print(f"Deleted {deleted_count} existing tricks")
        
        # Initialize AI processor
        print("Initializing AI processor...")
        processor = AIProcessor()
        
        # Detect tricks
        print("Detecting tricks with enhanced algorithm...")
        tricks = processor.detect_tricks(text_content, book_id)
        print(f"Detected {len(tricks)} potential tricks")
        
        # Show first few detected tricks
        print("\nFirst 10 detected tricks:")
        for i, trick in enumerate(tricks[:10], 1):
            print(f"{i}. {trick['name'][:60]}...")
            print(f"   Effect: {trick['effect_type']} | Difficulty: {trick['difficulty']} | Confidence: {trick['confidence']}")
        
        # Get effect type mapping
        print("\nMapping effect types...")
        cursor.execute("SELECT id, name FROM effect_types")
        effect_types = cursor.fetchall()
        effect_type_mapping = {et[1].lower(): et[0] for et in effect_types}
        print(f"Found {len(effect_type_mapping)} effect types")
        
        # Persist tricks to database
        print("Persisting tricks to database...")
        persisted_count = 0
        
        for trick_data in tricks:
            try:
                # Map effect type to ID
                effect_type_name = trick_data.get('effect_type', 'Other')
                effect_type_id = effect_type_mapping.get(effect_type_name.lower())
                
                if not effect_type_id:
                    # Create new effect type if doesn't exist
                    cursor.execute("INSERT INTO effect_types (id, name) VALUES (?, ?)", 
                                 (len(effect_type_mapping) + 1, effect_type_name))
                    effect_type_id = len(effect_type_mapping) + 1
                    effect_type_mapping[effect_type_name.lower()] = effect_type_id
                    print(f"Created new effect type: {effect_type_name}")
                
                # Insert trick
                cursor.execute('''
                    INSERT INTO tricks (id, book_id, effect_type_id, name, description, 
                                      difficulty, page_start, confidence, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"trick_{persisted_count + 1}_{book_id}",
                    trick_data['book_id'],
                    effect_type_id,
                    trick_data['name'],
                    trick_data['description'],
                    trick_data.get('difficulty', 'Unknown'),
                    trick_data.get('page_start'),
                    trick_data.get('confidence', 0.7),
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat()
                ))
                
                persisted_count += 1
                
            except Exception as trick_error:
                print(f"Error persisting trick {trick_data.get('name', 'Unknown')}: {trick_error}")
                continue
        
        # Commit changes
        conn.commit()
        print(f"\nSuccessfully persisted {persisted_count}/{len(tricks)} tricks to database")
        
        # Verify by counting tricks in database
        cursor.execute("SELECT COUNT(*) FROM tricks WHERE book_id = ?", (book_id,))
        final_count = cursor.fetchone()[0]
        print(f"Final trick count in database: {final_count}")
        
        conn.close()
        print("Manual reprocessing complete!")
        
    except Exception as e:
        print(f"Error during manual reprocessing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    manual_reprocess_vernon()