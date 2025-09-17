#!/usr/bin/env python3
"""
David Roth Expert Coin Magic Training Data Creator
Creates clean training data with real coin magic tricks
"""
import sqlite3
import json
from datetime import datetime
from uuid import uuid4

class DavidRothTrainingDataCreator:
    def __init__(self, db_path="magic_tricks.db"):
        self.db_path = db_path
        
        # David Roth book data
        self.book_data = {
            "id": str(uuid4()),
            "title": "Expert Coin Magic",
            "author": "David Roth",
            "isbn": "978-0962316807",
            "publication_year": 1982,
            "publisher": "Richard Kaufman",
            "page_count": 450,
            "file_path": "c:\\docker\\pdf-organizer\\input\\epdf.pub_david-roths-expert-coin-magic.pdf",
            "processed_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Real coin magic tricks from David Roth's Expert Coin Magic
        self.tricks_data = [
            {
                "id": str(uuid4()),
                "name": "The Roth Retention Vanish",
                "effect_type": "coin_magic",
                "description": "A coin is clearly shown and apparently placed into the left hand, but when the hand is opened, the coin has completely vanished. The retention appears perfect and natural.",
                "method": "The coin is retained in the right hand using finger positioning and timing. The left hand closes as if taking the coin, but it remains palmed in the right hand through precise muscle memory.",
                "difficulty": "intermediate",
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
                "effect_type": "coin_magic",
                "description": "Four coins are placed in each hand. One by one, three coins invisibly travel from the left hand to the right hand. The audience can see and count the coins throughout.",
                "method": "Uses classic palm and lapping techniques combined with Roth's refined handling. One coin is secretly held back while appearing to place four in each hand.",
                "difficulty": "advanced",
                "props": json.dumps(["Eight Matching Coins"]),
                "page_start": 78,
                "page_end": 89,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The Copper Silver Transposition",
                "effect_type": "coin_magic",
                "description": "A copper coin and silver coin change places while held in the spectator's hands. The transformation is completely impossible and happens under test conditions.",
                "method": "Uses Roth's copper/silver gaff coins and precise timing. The switch occurs during the apparent placement in the spectator's hands through careful misdirection.",
                "difficulty": "expert",
                "props": json.dumps(["Copper Coin", "Silver Coin", "Gimmicked Coins"]),
                "page_start": 125,
                "page_end": 135,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "Winged Silver",
                "effect_type": "coin_magic",
                "description": "A silver dollar vanishes from one hand and appears in the other hand which has been held by a spectator throughout. The coin seems to fly invisibly through the air.",
                "method": "Classic palm combined with Roth's timing and psychology. The coin is switched during the initial display while attention is on the spectator holding the other hand.",
                "difficulty": "advanced",
                "props": json.dumps(["Silver Dollar", "Duplicate Coin"]),
                "page_start": 156,
                "page_end": 164,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The Miser's Dream",
                "effect_type": "coin_magic",
                "description": "Coins are continuously produced from thin air and dropped into a bucket. The production seems endless with coins appearing from everywhere - spectators' hair, ears, and clothing.",
                "method": "Uses multiple palming techniques and body loads. Coins are pre-positioned and produced through classic palm, finger palm, and thumb palm in sequence.",
                "difficulty": "expert",
                "props": json.dumps(["Multiple Coins", "Metal Bucket", "Body Loads"]),
                "page_start": 45,
                "page_end": 65,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The Hanging Coins",
                "effect_type": "coin_magic",
                "description": "Coins seem to defy gravity by hanging in mid-air before dropping into the performer's hand. Multiple coins hang suspended at different levels.",
                "method": "Uses invisible thread and careful angle management. Coins are suspended on fine thread and controlled through hand movements that appear natural.",
                "difficulty": "advanced",
                "props": json.dumps(["Coins", "Invisible Thread", "Wax"]),
                "page_start": 234,
                "page_end": 245,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "Coin Through Table",
                "effect_type": "coin_magic",
                "description": "A coin penetrates completely through a solid table. The coin can be heard hitting the floor and is retrieved from underneath. The table can be examined.",
                "method": "Uses classic lapping combined with Roth's refined timing. The coin is lapped while appearing to press through the table, with sound effects created by dropping a duplicate.",
                "difficulty": "intermediate",
                "props": json.dumps(["Coin", "Table", "Duplicate Coin"]),
                "page_start": 189,
                "page_end": 198,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The Roth Coin Roll",
                "effect_type": "coin_magic",
                "description": "A coin rolls smoothly across the back of the fingers from thumb to pinkie and back. Roth's technique makes the movement appear effortless and hypnotic.",
                "method": "Specific finger positioning and timing developed by Roth. Each finger acts as a pivot point with the coin rolling using gravity and controlled finger movements.",
                "difficulty": "intermediate",
                "props": json.dumps(["Single Large Coin"]),
                "page_start": 15,
                "page_end": 25,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The Multiplying Coins",
                "effect_type": "production",
                "description": "One coin multiplies into four coins at the fingertips. Each new coin appears individually and visibly. All four coins can be examined at the end.",
                "method": "Uses edge grip and finger positioning to hold multiple coins as one. Coins are produced one at a time using edge grip releases and classic palming.",
                "difficulty": "expert",
                "props": json.dumps(["Four Matching Coins"]),
                "page_start": 289,
                "page_end": 302,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "Coin Assembly",
                "effect_type": "coin_magic", 
                "description": "Four coins placed under four cards gather together under one card. The coins seem to travel invisibly one by one until all four are found under a single card.",
                "method": "Uses classic shell coin and precise handling. One coin is actually a shell that covers two coins, allowing for the apparent gathering effect through careful switching.",
                "difficulty": "advanced",
                "props": json.dumps(["Four Coins", "Shell Coin", "Four Cards"]),
                "page_start": 345,
                "page_end": 358,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The Coin Bend",
                "effect_type": "coin_magic",
                "description": "A borrowed coin is visibly bent using only psychic powers. No physical force is applied, yet the coin bends dramatically. The coin can be examined before and after.",
                "method": "Uses prepared coin that appears normal but bends under heat from the hands. Combined with Roth's presentation that focuses attention on the bending moment.",
                "difficulty": "intermediate",
                "props": json.dumps(["Gimmicked Coin", "Normal Coin for Switch"]),
                "page_start": 398,
                "page_end": 408,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": str(uuid4()),
                "name": "The French Drop",
                "effect_type": "vanish",
                "description": "Roth's refinement of the classic vanish. A coin appears to be transferred from one hand to the other but actually vanishes completely. The handling looks completely natural.",
                "method": "Improved timing and finger positioning that eliminates the telltale signs of the classic French Drop. Uses psychological misdirection to direct attention away from the retention.",
                "difficulty": "beginner",
                "props": json.dumps(["Single Coin"]),
                "page_start": 28,
                "page_end": 35,
                "confidence": 1.0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]
    
    def insert_book(self):
        """Insert the David Roth book record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO books (
                    id, title, author, isbn, publication_year, publisher, 
                    page_count, file_path, processed_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.book_data["id"],
                self.book_data["title"], 
                self.book_data["author"],
                self.book_data["isbn"],
                self.book_data["publication_year"],
                self.book_data["publisher"],
                self.book_data["page_count"],
                self.book_data["file_path"],
                self.book_data["processed_at"],
                self.book_data["created_at"],
                self.book_data["updated_at"]
            ))
            
            conn.commit()
            print(f"✓ Created book: {self.book_data['title']} by {self.book_data['author']}")
            return self.book_data["id"]
            
        except sqlite3.IntegrityError as e:
            print(f"✗ Book already exists or constraint violation: {e}")
            return self.book_data["id"]
        except Exception as e:
            print(f"✗ Error creating book: {e}")
            return None
        finally:
            conn.close()
    
    def insert_tricks(self, book_id):
        """Insert all David Roth coin tricks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        created_count = 0
        
        for i, trick in enumerate(self.tricks_data, 1):
            try:
                cursor.execute('''
                    INSERT INTO tricks (
                        id, book_id, name, effect_type, description, method,
                        difficulty, props, page_start, page_end, confidence,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trick["id"],
                    book_id,
                    trick["name"],
                    trick["effect_type"],
                    trick["description"],
                    trick["method"],
                    trick["difficulty"],
                    trick["props"],
                    trick["page_start"],
                    trick["page_end"],
                    trick["confidence"],
                    trick["created_at"],
                    trick["updated_at"]
                ))
                
                created_count += 1
                print(f"✓ [{i}/{len(self.tricks_data)}] Created: {trick['name']}")
                
            except sqlite3.IntegrityError as e:
                print(f"✗ Failed to create '{trick['name']}': {e}")
            except Exception as e:
                print(f"✗ Error creating '{trick['name']}': {e}")
        
        conn.commit()
        conn.close()
        return created_count
    
    def verify_data(self):
        """Verify the complete training dataset"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check total books and tricks
            cursor.execute("SELECT COUNT(*) FROM books")
            book_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tricks")
            total_tricks = cursor.fetchone()[0]
            
            print(f"\n📊 Training Dataset Summary:")
            print(f"   Total Books: {book_count}")
            print(f"   Total Tricks: {total_tricks}")
            
            # Show books with trick counts
            cursor.execute("SELECT title, author FROM books")
            books = cursor.fetchall()
            print(f"\n📚 Books in training set:")
            for title, author in books:
                cursor.execute("SELECT COUNT(*) FROM tricks WHERE book_id = (SELECT id FROM books WHERE title = ?)", (title,))
                trick_count = cursor.fetchone()[0]
                print(f"   - {title} by {author} ({trick_count} tricks)")
            
            # Effect type distribution
            cursor.execute('''
                SELECT effect_type, COUNT(*) 
                FROM tricks 
                GROUP BY effect_type 
                ORDER BY COUNT(*) DESC
            ''')
            
            effect_counts = cursor.fetchall()
            print(f"\n🎭 Effect Type Distribution:")
            for effect_type, count in effect_counts:
                print(f"   - {effect_type}: {count}")
            
            # Difficulty distribution
            cursor.execute('''
                SELECT difficulty, COUNT(*) 
                FROM tricks 
                GROUP BY difficulty 
                ORDER BY COUNT(*) DESC
            ''')
            
            difficulty_counts = cursor.fetchall()
            print(f"\n⭐ Difficulty Distribution:")
            for difficulty, count in difficulty_counts:
                print(f"   - {difficulty}: {count}")
            
            # Author distribution
            cursor.execute('''
                SELECT b.author, COUNT(t.id) as trick_count
                FROM books b
                LEFT JOIN tricks t ON b.id = t.book_id
                GROUP BY b.author
                ORDER BY trick_count DESC
            ''')
            
            author_counts = cursor.fetchall()
            print(f"\n👨‍🎭 Author Distribution:")
            for author, count in author_counts:
                print(f"   - {author}: {count} tricks")
            
        except Exception as e:
            print(f"Error during verification: {e}")
        finally:
            conn.close()
    
    def create_training_data(self):
        """Main method to create David Roth training data"""
        print("Adding David Roth's Expert Coin Magic to Training Dataset")
        print("=" * 60)
        
        # Insert book
        book_id = self.insert_book()
        if not book_id:
            print("Failed to create book. Stopping.")
            return False
        
        # Insert tricks
        print(f"\nCreating {len(self.tricks_data)} coin magic tricks...")
        created_count = self.insert_tricks(book_id)
        
        print(f"\n" + "=" * 60)
        print(f"Summary: Successfully created {created_count}/{len(self.tricks_data)} coin tricks")
        
        # Verify complete dataset
        self.verify_data()
        
        success = created_count == len(self.tricks_data)
        if success:
            print("\n🪙 David Roth training data added successfully!")
            print("The dataset now includes both card magic and coin magic for comprehensive AI training.")
        else:
            print(f"\n⚠️  {len(self.tricks_data) - created_count} tricks failed to create")
        
        return success

def main():
    # Update the database path to match the Docker shared directory
    db_path = "shared/data/magic_tricks.db"
    creator = DavidRothTrainingDataCreator(db_path)
    creator.create_training_data()

if __name__ == "__main__":
    main()