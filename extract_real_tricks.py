#!/usr/bin/env python3
"""
Improved trick extraction for The Dai Vernon Book of Magic
This will identify actual magic tricks instead of page breaks
"""

import sqlite3
import re
import uuid
from datetime import datetime

def extract_actual_tricks(text_content):
    """Extract actual magic tricks from the book content"""
    
    tricks = []
    
    # Find all chapter sections that describe actual tricks
    chapter_pattern = r'CHAPTER\s+[A-Z\-]+\.?—([^\.]+?)\.?\s*\n(.*?)(?=CHAPTER|\Z)'
    chapter_matches = re.finditer(chapter_pattern, text_content, re.IGNORECASE | re.DOTALL)
    
    for match in chapter_matches:
        chapter_title = match.group(1).strip()
        chapter_content = match.group(2).strip()
        chapter_position = match.start()
        
        # Skip introductory chapters
        skip_chapters = [
            'BACKGROUND TO A LEGEND', 'THE VERNON TOUCH', 'FOREWORD', 
            'INTRODUCTION', 'TIPS ON KNOTS', 'POT POURRI'
        ]
        
        if any(skip in chapter_title.upper() for skip in skip_chapters):
            continue
        
        # Extract the actual trick content
        if len(chapter_content) > 200:  # Must have substantial content
            
            # Try to find effect/method structure
            effect_match = re.search(r'(EFFECT|The effect)[:\s]+(.*?)(?=METHOD|The method|PREPARATION|PERFORMANCE|$)', 
                                   chapter_content, re.IGNORECASE | re.DOTALL)
            method_match = re.search(r'(METHOD|The method)[:\s]+(.*?)(?=EFFECT|The effect|PREPARATION|PERFORMANCE|$)', 
                                   chapter_content, re.IGNORECASE | re.DOTALL)
            
            # Determine effect type based on content
            effect_type = classify_effect_type(chapter_title, chapter_content)
            
            # Determine difficulty
            difficulty = determine_difficulty(chapter_content)
            
            # Create trick entry
            trick = {
                'id': str(uuid.uuid4()),
                'name': chapter_title.title(),
                'description': chapter_content[:1000] + ('...' if len(chapter_content) > 1000 else ''),
                'method': method_match.group(2).strip()[:500] if method_match else '',
                'effect_type': effect_type,
                'difficulty': difficulty,
                'page_start': estimate_page_number(chapter_position, text_content),
                'confidence': 0.85  # Higher confidence for actual tricks
            }
            
            tricks.append(trick)
    
    return tricks

def classify_effect_type(title, content):
    """Classify the type of magic effect"""
    title_upper = title.upper()
    content_upper = content.upper()
    
    # Card magic
    if any(word in title_upper or word in content_upper[:500] for word in 
           ['CARD', 'ACE', 'DECK', 'DOUBLE LIFT', 'AMBITIOUS']):
        return 'card_magic'
    
    # Coin magic
    if any(word in title_upper or word in content_upper[:500] for word in 
           ['COIN', 'SILVER', 'MONEY', 'PALM']):
        return 'coin_magic'
    
    # Cups and Balls
    if any(word in title_upper for word in ['CUP', 'BALL']):
        return 'cups_and_balls'
    
    # Linking Rings
    if 'RING' in title_upper:
        return 'linking_rings'
    
    # Mental magic
    if any(word in title_upper or word in content_upper[:500] for word in 
           ['MENTAL', 'MIND', 'THOUGHT', 'PENETRATION']):
        return 'mentalism'
    
    # General close-up
    return 'close_up'

def determine_difficulty(content):
    """Determine trick difficulty based on content analysis"""
    content_upper = content.upper()
    
    # Look for difficulty indicators
    if any(word in content_upper for word in 
           ['DIFFICULT', 'ADVANCED', 'EXPERT', 'SKILL', 'PRACTICE']):
        return 'Advanced'
    elif any(word in content_upper for word in 
             ['EASY', 'SIMPLE', 'BEGINNER', 'BASIC']):
        return 'Beginner'
    else:
        return 'Intermediate'

def estimate_page_number(position, text_content):
    """Estimate page number based on position in text"""
    # Count page markers before this position
    page_markers = len(re.findall(r'--- Page \d+ ---', text_content[:position]))
    return max(1, page_markers)

def main():
    """Main function to extract and update tricks"""
    
    conn = sqlite3.connect('shared/data/magic_tricks.db')
    cursor = conn.cursor()

    # Get Vernon book
    cursor.execute('SELECT id, text_content FROM books WHERE title LIKE "%Vernon%"')
    book_data = cursor.fetchone()
    book_id = book_data[0]
    text_content = book_data[1]
    
    print(f'Extracting tricks from Vernon book (ID: {book_id})')
    
    # Extract actual tricks
    tricks = extract_actual_tricks(text_content)
    print(f'Found {len(tricks)} actual tricks')
    
    # Delete old page-based "tricks"
    cursor.execute('DELETE FROM tricks WHERE book_id = ?', (book_id,))
    print('Deleted old page-based entries')
    
    # Insert actual tricks
    insert_count = 0
    for trick in tricks:
        try:
            cursor.execute('''
                INSERT INTO tricks (
                    id, book_id, name, description, method, 
                    effect_type_id, difficulty, page_start, confidence, 
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trick['id'], book_id, trick['name'], trick['description'], 
                trick['method'], trick['effect_type'], trick['difficulty'], 
                trick['page_start'], trick['confidence'],
                datetime.utcnow().isoformat(), datetime.utcnow().isoformat()
            ))
            insert_count += 1
            print(f'Added: {trick["name"]}')
        except Exception as e:
            print(f'Error inserting {trick["name"]}: {e}')
    
    conn.commit()
    print(f'\nSuccessfully inserted {insert_count} actual tricks')
    
    # Verify the results
    cursor.execute('SELECT COUNT(*) FROM tricks WHERE book_id = ?', (book_id,))
    final_count = cursor.fetchone()[0]
    print(f'Final trick count: {final_count}')
    
    conn.close()

if __name__ == "__main__":
    main()