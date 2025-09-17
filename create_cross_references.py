#!/usr/bin/env python3
"""
Cross-Reference Creator for Magic Tricks
Creates cross-references for tricks that appear in multiple books
"""
import sqlite3
import json
from datetime import datetime
from uuid import uuid4
from collections import defaultdict

class CrossReferenceCreator:
    def __init__(self, db_path="shared/data/magic_tricks.db"):
        self.db_path = db_path
    
    def find_duplicate_tricks(self):
        """Find tricks with identical or very similar names across different books"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Find tricks grouped by name with different book_ids
            cursor.execute("""
                SELECT t.name, t.id, t.book_id, b.title as book_title, b.author, 
                       t.description, t.difficulty, t.page_start, t.page_end
                FROM tricks t 
                JOIN books b ON t.book_id = b.id 
                ORDER BY t.name, b.author
            """)
            
            all_tricks = cursor.fetchall()
            
            # Group by name
            tricks_by_name = defaultdict(list)
            for trick in all_tricks:
                name, trick_id, book_id, book_title, author, desc, difficulty, start, end = trick
                tricks_by_name[name].append({
                    'id': trick_id,
                    'name': name,
                    'book_id': book_id,
                    'book_title': book_title,
                    'author': author,
                    'description': desc,
                    'difficulty': difficulty,
                    'page_start': start,
                    'page_end': end
                })
            
            # Find duplicates (same name, different books)
            duplicates = {}
            for name, tricks in tricks_by_name.items():
                if len(tricks) > 1:
                    # Check if they're from different books
                    unique_books = set(t['book_id'] for t in tricks)
                    if len(unique_books) > 1:
                        duplicates[name] = tricks
            
            return duplicates
            
        finally:
            conn.close()
    
    def calculate_similarity_score(self, trick1, trick2):
        """Calculate similarity score between two tricks"""
        score = 0.0
        
        # Same name = high similarity
        if trick1['name'] == trick2['name']:
            score += 0.7
        
        # Same difficulty = moderate boost
        if trick1['difficulty'] == trick2['difficulty']:
            score += 0.2
        
        # Description similarity (simple word overlap check)
        words1 = set(trick1['description'].lower().split())
        words2 = set(trick2['description'].lower().split())
        overlap = len(words1 & words2)
        total = len(words1 | words2)
        if total > 0:
            desc_similarity = overlap / total
            score += desc_similarity * 0.1
        
        return min(score, 1.0)
    
    def create_cross_references(self):
        """Create cross-reference entries for duplicate tricks"""
        print("🔍 Finding duplicate tricks across books...")
        duplicates = self.find_duplicate_tricks()
        
        if not duplicates:
            print("✅ No duplicates found!")
            return
        
        print(f"📖 Found {len(duplicates)} trick names with multiple versions:")
        for name, versions in duplicates.items():
            print(f"   • {name}: {len(versions)} versions")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create cross_references table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cross_references (
                id TEXT PRIMARY KEY,
                source_trick_id TEXT NOT NULL,
                target_trick_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                similarity_score REAL,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_trick_id) REFERENCES tricks (id),
                FOREIGN KEY (target_trick_id) REFERENCES tricks (id),
                UNIQUE(source_trick_id, target_trick_id)
            )
        """)
        
        total_refs_created = 0
        
        try:
            for name, versions in duplicates.items():
                print(f"\n🔗 Creating cross-references for '{name}':")
                
                # Create bidirectional cross-references between all versions
                for i, trick1 in enumerate(versions):
                    for j, trick2 in enumerate(versions):
                        if i >= j:  # Avoid self-references and duplicates
                            continue
                        
                        similarity = self.calculate_similarity_score(trick1, trick2)
                        
                        # Determine relationship type
                        if similarity >= 0.9:
                            relationship_type = "identical_technique"
                        elif similarity >= 0.7:
                            relationship_type = "same_effect_different_method"
                        else:
                            relationship_type = "related_effect"
                        
                        notes = f"Cross-reference between {trick1['author']}'s version (pages {trick1['page_start']}-{trick1['page_end']}) and {trick2['author']}'s version (pages {trick2['page_start']}-{trick2['page_end']})"
                        
                        # Create bidirectional references
                        refs_to_create = [
                            (trick1['id'], trick2['id'], f"{relationship_type}_forward"),
                            (trick2['id'], trick1['id'], f"{relationship_type}_reverse")
                        ]
                        
                        for source_id, target_id, rel_type in refs_to_create:
                            try:
                                cursor.execute("""
                                    INSERT OR IGNORE INTO cross_references 
                                    (id, source_trick_id, target_trick_id, relationship_type, 
                                     similarity_score, notes, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    str(uuid4()),
                                    source_id,
                                    target_id,
                                    rel_type,
                                    similarity,
                                    notes,
                                    datetime.now().isoformat()
                                ))
                                total_refs_created += 1
                            except sqlite3.IntegrityError:
                                pass  # Reference already exists
                        
                        print(f"   ✓ Linked {trick1['author']} ↔ {trick2['author']} (similarity: {similarity:.2f})")
            
            conn.commit()
            print(f"\n✅ Created {total_refs_created} cross-references successfully!")
            
            # Verify the cross-references
            self.verify_cross_references()
            
        except Exception as e:
            print(f"❌ Error creating cross-references: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def verify_cross_references(self):
        """Verify the created cross-references"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM cross_references")
            total_refs = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT relationship_type, COUNT(*) 
                FROM cross_references 
                GROUP BY relationship_type
            """)
            ref_types = cursor.fetchall()
            
            print(f"\n📊 Cross-Reference Summary:")
            print(f"   🔗 Total Cross-References: {total_refs}")
            print(f"   📖 Reference Types:")
            for ref_type, count in ref_types:
                print(f"      • {ref_type}: {count}")
            
            # Show specific example for The French Drop
            cursor.execute("""
                SELECT cr.relationship_type, cr.similarity_score, cr.notes,
                       t1.name as source_name, b1.author as source_author,
                       t2.name as target_name, b2.author as target_author
                FROM cross_references cr
                JOIN tricks t1 ON cr.source_trick_id = t1.id
                JOIN books b1 ON t1.book_id = b1.id
                JOIN tricks t2 ON cr.target_trick_id = t2.id
                JOIN books b2 ON t2.book_id = b2.id
                WHERE t1.name = 'The French Drop'
                LIMIT 3
            """)
            
            french_drop_refs = cursor.fetchall()
            if french_drop_refs:
                print(f"\n🎭 Example: The French Drop Cross-References:")
                for ref in french_drop_refs:
                    rel_type, score, notes, src_name, src_author, tgt_name, tgt_author = ref
                    print(f"   🔗 {src_author} → {tgt_author}")
                    print(f"      Type: {rel_type}")
                    print(f"      Similarity: {score:.2f}")
                    print(f"      Note: {notes[:80]}...")
                    print()
            
        finally:
            conn.close()
    
    def show_cross_referenced_tricks(self, trick_name=None):
        """Show cross-referenced tricks, optionally filtered by name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            where_clause = ""
            params = []
            if trick_name:
                where_clause = "WHERE t1.name = ?"
                params = [trick_name]
            
            cursor.execute(f"""
                SELECT t1.name, b1.author as source_author, b1.title as source_book,
                       t2.name, b2.author as target_author, b2.title as target_book,
                       cr.relationship_type, cr.similarity_score
                FROM cross_references cr
                JOIN tricks t1 ON cr.source_trick_id = t1.id
                JOIN books b1 ON t1.book_id = b1.id
                JOIN tricks t2 ON cr.target_trick_id = t2.id
                JOIN books b2 ON t2.book_id = b2.id
                {where_clause}
                ORDER BY t1.name, cr.similarity_score DESC
            """, params)
            
            results = cursor.fetchall()
            
            if not results:
                print(f"No cross-references found{' for ' + trick_name if trick_name else ''}.")
                return
            
            print(f"\n🔗 Cross-Referenced Tricks{' for ' + trick_name if trick_name else ''}:")
            current_trick = None
            for result in results:
                name, src_author, src_book, tgt_name, tgt_author, tgt_book, rel_type, score = result
                
                if current_trick != name:
                    current_trick = name
                    print(f"\n📖 {name}:")
                
                print(f"   🔗 {src_author} ({src_book}) → {tgt_author} ({tgt_book})")
                print(f"      Type: {rel_type}, Similarity: {score:.2f}")
            
        finally:
            conn.close()

def main():
    creator = CrossReferenceCreator()
    
    print("🎭 Magic Trick Cross-Reference Creator")
    print("=" * 50)
    
    # Create cross-references
    creator.create_cross_references()
    
    # Show examples
    print("\n" + "=" * 50)
    creator.show_cross_referenced_tricks("The French Drop")

if __name__ == "__main__":
    main()