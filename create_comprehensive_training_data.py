#!/usr/bin/env python3
"""
Comprehensive Magic Trick Training Data Creator

Combines all individual training data creators into a single script.
Creates high-quality training data from multiple magic books for AI training.
"""

import sqlite3
import json
import argparse
from datetime import datetime
from uuid import uuid4
from pathlib import Path
from typing import Dict, List, Optional

class MagicTrainingDataCreator:
    """Comprehensive training data creator for magic tricks"""
    
    def __init__(self, db_path: str = "magic_tricks.db"):
        self.db_path = db_path
        self.books_created = 0
        self.tricks_created = 0
        
        # All training data sets
        self.training_data_sets = {
            "dai_vernon": self._get_dai_vernon_data(),
            "david_roth": self._get_david_roth_data(),
            "hugard": self._get_hugard_data(),
            "mentalism": self._get_mentalism_data()
        }
    
    def _get_dai_vernon_data(self) -> Dict:
        """Get Dai Vernon Book of Magic training data"""
        book_data = {
            "id": str(uuid4()),
            "title": "The Dai Vernon Book Of Magic",
            "author": "Dai Vernon",
            "isbn": "",
            "publication_year": 1957,
            "publisher": "Harry Stanley",
            "page_count": 209,
            "file_path": "dai_vernon_book_of_magic.pdf",
            "processed_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        tricks_data = [
            {
                "id": str(uuid4()),
                "name": "The Ambitious Card",
                "effect_type": "Card",
                "description": "A selected card repeatedly rises to the top of the deck despite being placed in the middle. Vernon's handling includes psychological touches and natural movements that make the effect seem impossible.",
                "method": "Combination of double lift, top stock control, and misdirection. Uses the Vernon touch - natural handling that conceals the method through timing and psychology.",
                "difficulty": "Intermediate",
                "props": json.dumps(["Playing Cards"]),
                "page_start": 45,
                "page_end": 52,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "Coins Through Table",
                "effect_type": "Coin",
                "description": "Three coins pass through a solid table top one at a time. The handling is completely natural and can be performed surrounded. Each coin's passage is clearly seen and heard.",
                "method": "Classic method using lapping combined with Vernon's natural movements. The coins are secretly lapped while appearing to pass through the table. Timing and misdirection are crucial.",
                "difficulty": "Advanced",
                "props": json.dumps(["Three Coins", "Table"]),
                "page_start": 78,
                "page_end": 85,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The Cups and Balls",
                "effect_type": "General",
                "description": "Vernon's complete routine with three cups and balls. Includes multiple phases with balls appearing, vanishing, and multiplying under the cups. Climaxes with the production of larger objects.",
                "method": "Classical cups and balls technique refined by Vernon. Uses natural loading, palming, and misdirection. Each phase builds logically to create a complete entertaining routine.",
                "difficulty": "Advanced",
                "props": json.dumps(["Three Cups", "Small Balls", "Load Objects"]),
                "page_start": 95,
                "page_end": 115,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The Linking Rings",
                "effect_type": "General",
                "description": "Vernon's handling of the classic linking rings. Rings link and unlink in impossible ways. Includes spinning sequences and a spectacular unlinking method.",
                "method": "Uses key ring principle with Vernon's improvements. Natural handling conceals the moves. Includes psychological touches that enhance the impossibility.",
                "difficulty": "Intermediate",
                "props": json.dumps(["Set of Linking Rings"]),
                "page_start": 125,
                "page_end": 140,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The French Drop",
                "effect_type": "General",
                "description": "Vernon's refined handling of the classic vanish. A small object appears to be placed in one hand but actually remains in the other, then vanishes completely.",
                "method": "Improved finger positioning and timing that makes the vanish completely natural. The secret lies in the psychological aspects rather than just the mechanics.",
                "difficulty": "Beginner",
                "props": json.dumps(["Small Object", "Coin", "Ball"]),
                "page_start": 168,
                "page_end": 175,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        return {"book": book_data, "tricks": tricks_data}
    
    def _get_david_roth_data(self) -> Dict:
        """Get David Roth Expert Coin Magic training data"""
        book_data = {
            "id": str(uuid4()),
            "title": "Expert Coin Magic",
            "author": "David Roth",
            "isbn": "978-0962316807",
            "publication_year": 1982,
            "publisher": "Richard Kaufman",
            "page_count": 450,
            "file_path": "expert_coin_magic.pdf",
            "processed_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        tricks_data = [
            {
                "id": str(uuid4()),
                "name": "The Roth Retention Vanish",
                "effect_type": "Coin",
                "description": "A coin is clearly shown and apparently placed into the left hand, but when the hand is opened, the coin has completely vanished. The retention appears perfect and natural.",
                "method": "The coin is retained in the right hand using finger positioning and timing. The left hand closes as if taking the coin, but it remains palmed in the right hand through precise muscle memory.",
                "difficulty": "Intermediate",
                "props": json.dumps(["Single Coin"]),
                "page_start": 45,
                "page_end": 52,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "Coins Across",
                "effect_type": "Coin",
                "description": "Four coins are placed in each hand. One by one, three coins invisibly travel from the left hand to the right hand. The audience can see and count the coins throughout.",
                "method": "Uses classic palm and lapping techniques combined with Roth's refined handling. One coin is secretly held back while appearing to place four in each hand.",
                "difficulty": "Advanced",
                "props": json.dumps(["Eight Coins"]),
                "page_start": 78,
                "page_end": 95,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The Winged Silver",
                "effect_type": "Coin",
                "description": "A silver coin changes to copper, then back to silver, then vanishes and reappears in impossible locations. Multiple transformations create a stunning sequence.",
                "method": "Uses Roth's advanced palming and switching techniques. Copper and silver coins are switched at precise moments using expert timing and misdirection.",
                "difficulty": "Advanced",
                "props": json.dumps(["Silver Coin", "Copper Coin"]),
                "page_start": 125,
                "page_end": 145,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The French Drop",
                "effect_type": "Coin",
                "description": "Roth's version of the classic vanish with improved handling. A coin is apparently placed into one hand but vanishes completely when the hand is opened.",
                "method": "Refined finger positions and timing make the vanish appear completely natural. Focus on the psychological aspects and audience management during the critical moment.",
                "difficulty": "Beginner",
                "props": json.dumps(["Single Coin"]),
                "page_start": 25,
                "page_end": 32,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        return {"book": book_data, "tricks": tricks_data}
    
    def _get_hugard_data(self) -> Dict:
        """Get Jean Hugard Coin Magic training data"""
        book_data = {
            "id": str(uuid4()),
            "title": "Coin Magic",
            "author": "Jean Hugard",
            "isbn": "978-0486210285",
            "publication_year": 1954,
            "publisher": "Dover Publications",
            "page_count": 128,
            "file_path": "hugard_coin_magic.pdf",
            "processed_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        tricks_data = [
            {
                "id": str(uuid4()),
                "name": "The Classic Palm",
                "effect_type": "Coin",
                "description": "The fundamental technique for concealing a coin in the hand while the hand appears empty. Forms the basis for most advanced coin magic.",
                "method": "The coin is held in the palm using natural muscle tension. The hand maintains a relaxed appearance while the coin remains hidden.",
                "difficulty": "Intermediate",
                "props": json.dumps(["Single Coin"]),
                "page_start": 15,
                "page_end": 25,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The Bobo Switch",
                "effect_type": "Coin",
                "description": "A method for secretly switching one coin for another during a natural handling action. The switch is completely imperceptible to the audience.",
                "method": "Uses timing and natural hand movements to switch coins. The palmed coin is released while the visible coin is secretly retained.",
                "difficulty": "Intermediate",
                "props": json.dumps(["Two Different Coins"]),
                "page_start": 45,
                "page_end": 52,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The French Drop",
                "effect_type": "Coin",
                "description": "Hugard's foundational teaching of the classic vanish. A coin is apparently taken by one hand but secretly retained in the other, then vanishes.",
                "method": "Basic finger drop technique with emphasis on natural timing and misdirection. The foundation technique that leads to more advanced vanishes.",
                "difficulty": "Beginner",
                "props": json.dumps(["Single Coin"]),
                "page_start": 8,
                "page_end": 14,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        return {"book": book_data, "tricks": tricks_data}
    
    def _get_mentalism_data(self) -> Dict:
        """Get Mentalism training data"""
        book_data = {
            "id": str(uuid4()),
            "title": "Encyclopedic Dictionary of Mentalism - Volume 3",
            "author": "Richard Osterlind",
            "isbn": "978-1932785037",
            "publication_year": 2005,
            "publisher": "Richard Osterlind International",
            "page_count": 320,
            "file_path": "mentalism_encyclopedia_v3.pdf",
            "processed_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        tricks_data = [
            {
                "id": str(uuid4()),
                "name": "Book Test",
                "effect_type": "Mentalism",
                "description": "The mentalist accurately divines a word chosen randomly from a book by the spectator. The effect appears to demonstrate genuine mind reading abilities.",
                "method": "Uses a prepared book with known content or a forcing technique to control the selection. Presentation emphasizes the mental aspect rather than the method.",
                "difficulty": "Intermediate",
                "props": json.dumps(["Special Book", "Regular Book"]),
                "page_start": 45,
                "page_end": 55,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "Thought Transmission",
                "effect_type": "Mentalism",
                "description": "The performer accurately receives and reveals thoughts transmitted by a spectator. The effect suggests genuine telepathic abilities.",
                "method": "Uses subtle cueing, psychological techniques, or a secret communication system. The method is completely hidden behind strong presentation.",
                "difficulty": "Advanced",
                "props": json.dumps(["None Required"]),
                "page_start": 78,
                "page_end": 92,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "Prediction Effect",
                "effect_type": "Mentalism",
                "description": "The mentalist makes a prediction about future choices before they are made, then proves the prediction correct when revealed.",
                "method": "Uses forcing techniques, multiple outs, or pre-show work to ensure the prediction matches the outcome. Strong presentation sells the impossibility.",
                "difficulty": "Intermediate",
                "props": json.dumps(["Envelope", "Prediction"]),
                "page_start": 125,
                "page_end": 138,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
        
        return {"book": book_data, "tricks": tricks_data}
    
    def create_database_tables(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create books table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT,
                publication_year INTEGER,
                publisher TEXT,
                page_count INTEGER,
                file_path TEXT,
                processed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Create tricks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tricks (
                id TEXT PRIMARY KEY,
                book_id TEXT NOT NULL,
                name TEXT NOT NULL,
                effect_type TEXT NOT NULL,
                description TEXT,
                method TEXT,
                difficulty TEXT,
                props TEXT,
                page_start INTEGER,
                page_end INTEGER,
                confidence REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (book_id) REFERENCES books (id)
            )
        ''')
        
        # Create cross_references table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cross_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_trick_id TEXT NOT NULL,
                target_trick_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                similarity_score REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_trick_id) REFERENCES tricks (id),
                FOREIGN KEY (target_trick_id) REFERENCES tricks (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Database tables created/verified")
    
    def insert_book(self, book_data: Dict) -> Optional[str]:
        """Insert a book record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO books (
                    id, title, author, isbn, publication_year, publisher,
                    page_count, file_path, processed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                book_data["id"], book_data["title"], book_data["author"],
                book_data["isbn"], book_data["publication_year"], book_data["publisher"],
                book_data["page_count"], book_data["file_path"], book_data["processed_at"],
                book_data["created_at"], book_data["updated_at"]
            ))
            
            conn.commit()
            self.books_created += 1
            print(f"✓ Created book: {book_data['title']} by {book_data['author']}")
            return book_data["id"]
            
        except sqlite3.IntegrityError:
            print(f"⚠ Book already exists: {book_data['title']}")
            return book_data["id"]
        except Exception as e:
            print(f"✗ Error creating book '{book_data['title']}': {e}")
            return None
        finally:
            conn.close()
    
    def insert_tricks(self, tricks_data: List[Dict], book_id: str) -> int:
        """Insert tricks for a book"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        created_count = 0
        
        for trick in tricks_data:
            try:
                cursor.execute('''
                    INSERT INTO tricks (
                        id, book_id, name, effect_type, description, method,
                        difficulty, props, page_start, page_end, confidence,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trick["id"], book_id, trick["name"], trick["effect_type"],
                    trick["description"], trick["method"], trick["difficulty"],
                    trick["props"], trick["page_start"], trick["page_end"],
                    trick["confidence"], trick["created_at"], trick["updated_at"]
                ))
                
                created_count += 1
                self.tricks_created += 1
                print(f"  ✓ Created trick: {trick['name']}")
                
            except sqlite3.IntegrityError:
                print(f"  ⚠ Trick already exists: {trick['name']}")
            except Exception as e:
                print(f"  ✗ Error creating trick '{trick['name']}': {e}")
        
        conn.commit()
        conn.close()
        return created_count
    
    def create_cross_references(self):
        """Create cross-references for similar tricks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find tricks with the same name for cross-referencing
        cursor.execute('''
            SELECT t1.id, t1.name, t1.book_id, b1.author,
                   t2.id, t2.name, t2.book_id, b2.author
            FROM tricks t1
            JOIN books b1 ON t1.book_id = b1.id
            JOIN tricks t2 ON t1.name = t2.name
            JOIN books b2 ON t2.book_id = b2.id
            WHERE t1.id != t2.id
        ''')
        
        cross_refs = cursor.fetchall()
        cross_ref_count = 0
        
        for row in cross_refs:
            source_id, source_name, _, source_author, target_id, target_name, _, target_author = row
            
            try:
                cursor.execute('''
                    INSERT INTO cross_references (
                        source_trick_id, target_trick_id, relationship_type,
                        similarity_score, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    source_id, target_id, "similar",
                    1.0, datetime.now().isoformat()
                ))
                
                cross_ref_count += 1
                print(f"  ✓ Cross-referenced: {source_name} ({source_author}) ↔ ({target_author})")
                
            except sqlite3.IntegrityError:
                # Cross-reference already exists
                pass
            except Exception as e:
                print(f"  ✗ Error creating cross-reference: {e}")
        
        conn.commit()
        conn.close()
        
        if cross_ref_count > 0:
            print(f"✓ Created {cross_ref_count} cross-references")
        
        return cross_ref_count
    
    def create_training_data(self, datasets: Optional[List[str]] = None):
        """Create training data for specified datasets"""
        if datasets is None:
            datasets = list(self.training_data_sets.keys())
        
        print("🎭 Creating Magic Trick Training Data")
        print("=" * 60)
        
        # Setup database
        self.create_database_tables()
        
        # Process each dataset
        for dataset_name in datasets:
            if dataset_name not in self.training_data_sets:
                print(f"⚠ Unknown dataset: {dataset_name}")
                continue
            
            dataset = self.training_data_sets[dataset_name]
            print(f"\n📚 Processing {dataset_name.replace('_', ' ').title()} dataset...")
            
            # Insert book
            book_id = self.insert_book(dataset["book"])
            if not book_id:
                print(f"  ✗ Failed to create book for {dataset_name}")
                continue
            
            # Insert tricks
            created_count = self.insert_tricks(dataset["tricks"], book_id)
            print(f"  ✓ Created {created_count}/{len(dataset['tricks'])} tricks")
        
        # Create cross-references
        print(f"\n🔗 Creating cross-references...")
        cross_ref_count = self.create_cross_references()
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"📊 Summary:")
        print(f"  📚 Books created: {self.books_created}")
        print(f"  🎭 Tricks created: {self.tricks_created}")
        print(f"  🔗 Cross-references created: {cross_ref_count}")
        
        self.verify_data()
    
    def verify_data(self):
        """Verify the created training data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            print(f"\n🔍 Data Verification:")
            
            # Books summary
            cursor.execute("SELECT COUNT(*) FROM books")
            book_count = cursor.fetchone()[0]
            print(f"  📚 Total books: {book_count}")
            
            cursor.execute("SELECT title, author FROM books ORDER BY author")
            books = cursor.fetchall()
            for title, author in books:
                cursor.execute("""
                    SELECT COUNT(*) FROM tricks 
                    WHERE book_id = (SELECT id FROM books WHERE title = ? AND author = ?)
                """, (title, author))
                trick_count = cursor.fetchone()[0]
                print(f"    - {title} by {author} ({trick_count} tricks)")
            
            # Effect type distribution
            cursor.execute('''
                SELECT effect_type, COUNT(*) 
                FROM tricks 
                GROUP BY effect_type 
                ORDER BY COUNT(*) DESC
            ''')
            
            effect_counts = cursor.fetchall()
            print(f"\n  🎭 Tricks by effect type:")
            for effect_type, count in effect_counts:
                print(f"    - {effect_type}: {count}")
            
            # Difficulty distribution
            cursor.execute('''
                SELECT difficulty, COUNT(*) 
                FROM tricks 
                GROUP BY difficulty 
                ORDER BY COUNT(*) DESC
            ''')
            
            difficulty_counts = cursor.fetchall()
            print(f"\n  📊 Tricks by difficulty:")
            for difficulty, count in difficulty_counts:
                print(f"    - {difficulty}: {count}")
            
            # Cross-references
            cursor.execute("SELECT COUNT(*) FROM cross_references")
            cross_ref_count = cursor.fetchone()[0]
            print(f"\n  🔗 Total cross-references: {cross_ref_count}")
            
        except Exception as e:
            print(f"  ✗ Error during verification: {e}")
        finally:
            conn.close()

def main():
    parser = argparse.ArgumentParser(
        description="Create comprehensive magic trick training data"
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=["dai_vernon", "david_roth", "hugard", "mentalism"],
        help="Specify which datasets to create (default: all)"
    )
    parser.add_argument(
        "--db-path",
        default="magic_tricks.db",
        help="Path to SQLite database file (default: magic_tricks.db)"
    )
    
    args = parser.parse_args()
    
    creator = MagicTrainingDataCreator(args.db_path)
    creator.create_training_data(args.datasets)
    
    print(f"\n🎩 Training data creation complete!")
    print(f"   Database: {args.db_path}")
    print(f"   Ready for AI training and analysis!")

if __name__ == "__main__":
    main()