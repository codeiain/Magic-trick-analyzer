#!/usr/bin/env python3

import sys
import os
import sqlite3

# Add the AI service path so we can import the processor
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai-service'))

from ai_processor import AIProcessor

def test_enhanced_detection():
    """Test the enhanced AI detection on a sample of Vernon book text"""
    
    # Sample text from the Dai Vernon book that should contain many tricks
    sample_text = """
    THE AMBITIOUS CARD
    This routine is one of the most popular in card magic. The effect is that a selected card continually rises to the top of the pack despite being placed in the center.
    
    PERFORMANCE:
    Have a card selected and returned to the pack. Control it to the top using your favorite method.
    
    THE FOUR ACE ROUTINE
    This classic routine involves the apparent separation of the four aces from the deck through various magical methods and presentations.
    
    METHOD:
    The aces are secretly arranged in advance. The routine relies on careful handling and misdirection to create the illusion.
    
    THE CUPS AND BALLS ROUTINE
    One of the oldest tricks in magic, involving three cups and three balls. The balls appear to vanish and reappear beneath the cups in impossible ways.
    
    PRESENTATION:
    Begin with the cups mouth up on the table. Place one ball on top of each cup. The routine involves a series of magical passes and flourishes.
    
    COIN VANISH TECHNIQUE
    This sleight allows for the apparent vanishing of a coin from the performer's hand through careful handling and timing.
    
    PROCEDURE:
    Hold the coin at the fingertips. Execute the vanish through proper misdirection and hand positioning. The move requires practice to perfect.
    
    THE THUMB TIE ROUTINE
    A classic escape effect where the performer's thumbs are tied together but solid objects penetrate through the restraint.
    """
    
    # Create AI processor
    processor = AIProcessor()
    
    # Test detection with the sample
    print("Testing enhanced AI detection...")
    print(f"Sample text length: {len(sample_text)} characters")
    
    # Detect tricks
    detected_tricks = processor.detect_tricks(sample_text, "test-book-id")
    
    print(f"\nDetected {len(detected_tricks)} tricks:")
    for i, trick in enumerate(detected_tricks, 1):
        print(f"{i}. {trick['name']}")
        print(f"   Effect Type: {trick['effect_type']}")
        print(f"   Difficulty: {trick['difficulty']}")
        print(f"   Confidence: {trick['confidence']}")
        print(f"   Description: {trick['description'][:100]}...")
        print()
    
    # Test if our enhanced indicators work better
    print("\nChecking enhanced indicators in sample text:")
    enhanced_indicators = [
        'routine', 'handling', 'presentation', 'procedure', 'technique', 
        'flourish', 'move', 'sleight', 'pass', 'control', 'method'
    ]
    
    text_lower = sample_text.lower()
    found_indicators = []
    for indicator in enhanced_indicators:
        if indicator in text_lower:
            count = text_lower.count(indicator)
            found_indicators.append(f"{indicator}: {count}")
    
    print(f"Enhanced indicators found: {', '.join(found_indicators)}")
    
    # Get the actual Vernon book text and test a portion
    try:
        conn = sqlite3.connect('shared/data/magic_tricks.db')
        cursor = conn.cursor()
        cursor.execute('SELECT text_content FROM books WHERE title LIKE "%Dai Vernon%"')
        result = cursor.fetchone()
        
        if result and result[0]:
            vernon_text = result[0]
            print(f"\nActual Vernon book text length: {len(vernon_text)} characters")
            
            # Test on a smaller chunk to avoid memory issues
            test_chunk = vernon_text[:50000]  # First 50k characters
            print(f"Testing on first {len(test_chunk)} characters...")
            
            vernon_tricks = processor.detect_tricks(test_chunk, "vernon-test")
            print(f"Detected {len(vernon_tricks)} tricks in sample chunk:")
            
            for i, trick in enumerate(vernon_tricks[:10], 1):  # Show first 10
                print(f"{i}. {trick['name'][:50]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"Error testing on actual Vernon text: {e}")

if __name__ == "__main__":
    test_enhanced_detection()