#!/usr/bin/env python3

import sqlite3
import os
import requests

def final_verification():
    """Final verification that both database and API are working correctly"""
    
    print("=== FINAL VERIFICATION ===")
    print()
    
    # Database verification
    print("1. Database Verification:")
    db_path = os.path.join("shared", "data", "magic_tricks.db")
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Count Vernon tricks
    cursor.execute("""
        SELECT COUNT(*) FROM tricks 
        WHERE book_id = 'a3a9f168-9778-4949-a20a-d0a07bdcd1ea'
    """)
    total_tricks = cursor.fetchone()[0]
    print(f"   ✅ Total Vernon tricks in database: {total_tricks}")
    
    # Check effect types
    cursor.execute("""
        SELECT COUNT(*) FROM tricks t
        JOIN effect_types et ON t.effect_type_id = et.id
        WHERE t.book_id = 'a3a9f168-9778-4949-a20a-d0a07bdcd1ea'
    """)
    valid_effect_types = cursor.fetchone()[0]
    print(f"   ✅ Tricks with valid effect types: {valid_effect_types}")
    
    # Show effect type distribution
    cursor.execute("""
        SELECT et.name, COUNT(*) as count
        FROM tricks t
        JOIN effect_types et ON t.effect_type_id = et.id
        WHERE t.book_id = 'a3a9f168-9778-4949-a20a-d0a07bdcd1ea'
        GROUP BY et.name
        ORDER BY count DESC
    """)
    print("   📊 Effect type distribution:")
    for effect_type, count in cursor.fetchall():
        print(f"      {effect_type}: {count} tricks")
    
    conn.close()
    print()
    
    # API verification
    print("2. API Verification:")
    try:
        response = requests.get(
            "http://localhost:8084/api/v1/tricks/", 
            params={"book_title": "The Dai Vernon Book of Magic"}
        )
        if response.status_code == 200:
            tricks = response.json()
            print(f"   ✅ API returned {len(tricks)} tricks")
            
            # Sample trick names
            if tricks:
                print("   📚 Sample trick names:")
                for i, trick in enumerate(tricks[:5]):
                    print(f"      {i+1}. {trick['name']} ({trick['effect_type']})")
                if len(tricks) > 5:
                    print(f"      ... and {len(tricks) - 5} more")
        else:
            print(f"   ❌ API error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ API connection error: {e}")
    
    print()
    
    # Summary
    print("3. Summary:")
    if total_tricks == 16 and valid_effect_types == 16:
        print("   ✅ SUCCESS: All Vernon tricks properly extracted and categorized!")
        print("   ✅ Frontend should now display all tricks correctly")
        print(f"   🌐 Visit: http://localhost:3000/books/a3a9f168-9778-4949-a20a-d0a07bdcd1ea")
    else:
        print("   ⚠️  Some issues may remain - check the counts above")

if __name__ == "__main__":
    final_verification()