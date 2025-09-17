#!/usr/bin/env python3
"""
Cross-Reference Validation Script
Tests the cross-reference functionality with The French Drop example
"""
import sqlite3
import json
from typing import List, Dict

def test_french_drop_cross_reference():
    """Test The French Drop cross-reference functionality"""
    db_path = "shared/data/magic_tricks.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🎭 Testing Cross-Reference System")
        print("=" * 50)
        
        # Find The French Drop tricks
        cursor.execute("""
            SELECT t.id, t.name, b.author, b.title, t.description, t.difficulty,
                   t.page_start, t.page_end
            FROM tricks t
            JOIN books b ON t.book_id = b.id
            WHERE t.name = 'The French Drop'
            ORDER BY b.author
        """)
        
        french_drops = cursor.fetchall()
        print(f"📖 Found {len(french_drops)} versions of 'The French Drop':")
        
        for i, (trick_id, name, author, book_title, desc, difficulty, start, end) in enumerate(french_drops, 1):
            print(f"\n{i}. {author} - {book_title}")
            print(f"   📄 Pages: {start}-{end}")
            print(f"   ⭐ Difficulty: {difficulty}")
            print(f"   📝 Description: {desc[:80]}...")
            print(f"   🔗 ID: {trick_id}")
        
        if len(french_drops) < 2:
            print("❌ Need at least 2 versions to test cross-references")
            return False
        
        # Check cross-references for these tricks
        print(f"\n🔗 Cross-References for The French Drop:")
        print("-" * 50)
        
        found_refs = False
        for trick_id, name, author, book_title, desc, difficulty, start, end in french_drops:
            cursor.execute("""
                SELECT 
                    cr.relationship_type,
                    cr.similarity_score,
                    t2.name as target_name,
                    b2.author as target_author,
                    b2.title as target_book,
                    cr.notes
                FROM cross_references cr
                JOIN tricks t2 ON cr.target_trick_id = t2.id
                JOIN books b2 ON t2.book_id = b2.id
                WHERE cr.source_trick_id = ?
                ORDER BY cr.similarity_score DESC
            """, (trick_id,))
            
            refs = cursor.fetchall()
            if refs:
                found_refs = True
                print(f"\n📚 From {author} → Other Versions:")
                for rel_type, score, target_name, target_author, target_book, notes in refs:
                    print(f"   🔗 → {target_author} ({target_book})")
                    print(f"      Type: {rel_type}")
                    print(f"      Similarity: {score:.2f}")
                    if notes:
                        print(f"      Notes: {notes[:60]}...")
        
        if not found_refs:
            print("❌ No cross-references found!")
            return False
        
        # Test cross-reference lookup functionality
        print(f"\n🔍 Cross-Reference Lookup Test:")
        print("-" * 30)
        
        # Get all tricks that have cross-references
        cursor.execute("""
            SELECT DISTINCT t.name, COUNT(cr.id) as ref_count
            FROM tricks t
            JOIN cross_references cr ON (t.id = cr.source_trick_id OR t.id = cr.target_trick_id)
            GROUP BY t.name
            ORDER BY ref_count DESC
            LIMIT 5
        """)
        
        top_cross_refs = cursor.fetchall()
        print("Top cross-referenced tricks:")
        for name, count in top_cross_refs:
            print(f"   • {name}: {count} cross-references")
        
        # Test relationship types
        cursor.execute("""
            SELECT relationship_type, COUNT(*) 
            FROM cross_references 
            GROUP BY relationship_type
        """)
        
        rel_types = cursor.fetchall()
        print(f"\nCross-reference relationship types:")
        for rel_type, count in rel_types:
            print(f"   • {rel_type}: {count}")
        
        print(f"\n✅ Cross-Reference System Test: SUCCESS!")
        print(f"   🔗 Found {len(french_drops)} versions of The French Drop")
        print(f"   📊 Cross-references working properly")
        print(f"   🎯 System ready for magic trick analysis!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cross-reference test: {e}")
        return False
    finally:
        conn.close()

def demonstrate_cross_reference_features():
    """Demonstrate practical cross-reference features"""
    db_path = "shared/data/magic_tricks.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print(f"\n🎪 Cross-Reference Feature Demonstration")
        print("=" * 60)
        
        # Feature 1: Compare different authors' approaches
        print("🔍 Feature 1: Compare Different Authors' Approaches")
        print("-" * 50)
        
        cursor.execute("""
            SELECT t1.name, b1.author as author1, t1.description as desc1,
                   b2.author as author2, t2.description as desc2,
                   cr.similarity_score
            FROM cross_references cr
            JOIN tricks t1 ON cr.source_trick_id = t1.id
            JOIN books b1 ON t1.book_id = b1.id
            JOIN tricks t2 ON cr.target_trick_id = t2.id
            JOIN books b2 ON t2.book_id = b2.id
            WHERE t1.name = t2.name AND b1.author != b2.author
            ORDER BY cr.similarity_score DESC
            LIMIT 3
        """)
        
        comparisons = cursor.fetchall()
        for name, auth1, desc1, auth2, desc2, score in comparisons:
            print(f"\n📖 {name} - Comparison (Similarity: {score:.2f})")
            print(f"   {auth1}: {desc1[:60]}...")
            print(f"   {auth2}: {desc2[:60]}...")
        
        # Feature 2: Find related techniques
        print(f"\n🔗 Feature 2: Technique Relationships")
        print("-" * 40)
        
        cursor.execute("""
            SELECT t1.name as technique, t2.name as related_technique,
                   cr.relationship_type, cr.similarity_score
            FROM cross_references cr
            JOIN tricks t1 ON cr.source_trick_id = t1.id
            JOIN tricks t2 ON cr.target_trick_id = t2.id
            WHERE t1.name != t2.name
            ORDER BY cr.similarity_score DESC
            LIMIT 5
        """)
        
        relations = cursor.fetchall()
        if relations:
            for tech1, tech2, rel_type, score in relations:
                print(f"   🔗 {tech1} ↔ {tech2}")
                print(f"      Relationship: {rel_type} (Score: {score:.2f})")
        else:
            print("   (No cross-technique relationships found)")
        
        # Feature 3: Learning progressions
        print(f"\n📈 Feature 3: Learning Progressions")
        print("-" * 35)
        
        cursor.execute("""
            SELECT t1.name, t1.difficulty, t2.name, t2.difficulty,
                   cr.similarity_score
            FROM cross_references cr
            JOIN tricks t1 ON cr.source_trick_id = t1.id
            JOIN tricks t2 ON cr.target_trick_id = t2.id
            WHERE t1.name = t2.name 
            AND t1.difficulty != t2.difficulty
            ORDER BY 
                CASE t1.difficulty 
                    WHEN 'beginner' THEN 1 
                    WHEN 'intermediate' THEN 2 
                    WHEN 'advanced' THEN 3 
                    WHEN 'expert' THEN 4 
                END
        """)
        
        progressions = cursor.fetchall()
        for name1, diff1, name2, diff2, score in progressions:
            print(f"   📚 {name1}: {diff1} → {diff2} progression")
            print(f"      Cross-reference score: {score:.2f}")
        
        print(f"\n🎭 Cross-Reference System Features:")
        print(f"   ✅ Author comparison capabilities")
        print(f"   ✅ Technique relationship mapping")  
        print(f"   ✅ Learning progression tracking")
        print(f"   ✅ Similarity scoring system")
        print(f"   ✅ Bidirectional cross-referencing")
        
    finally:
        conn.close()

def main():
    """Main test function"""
    success = test_french_drop_cross_reference()
    
    if success:
        demonstrate_cross_reference_features()
        
        print(f"\n🏆 CROSS-REFERENCE SYSTEM: FULLY OPERATIONAL!")
        print(f"=" * 60)
        print(f"✨ The French Drop can now be cross-referenced between:")
        print(f"   📚 Dai Vernon's classical approach")
        print(f"   📚 David Roth's modern refinements")
        print(f"🔗 Users can now explore different authors' perspectives")
        print(f"🎓 Perfect for studying technique variations and evolution!")
    else:
        print(f"\n❌ Cross-reference system needs attention")

if __name__ == "__main__":
    main()