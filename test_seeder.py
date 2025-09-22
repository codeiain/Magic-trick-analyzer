#!/usr/bin/env python3
"""
Test script for the AI-powered database seeder

This script runs basic tests to verify the seeder functionality without
actually calling the Claude API or processing large PDFs.

Usage:
    python test_seeder.py
"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add current directory to path so we can import the seeder
sys.path.insert(0, str(Path(__file__).parent))

try:
    from seed_database_with_claude import MagicBookSeeder, BookMetadata, MagicTrick
    print("✅ Successfully imported seeder components")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all requirements are installed: pip install -r seeder_requirements.txt")
    sys.exit(1)


def test_book_metadata_lookup():
    """Test book metadata lookup functionality"""
    print("\n🔍 Testing book metadata lookup...")
    
    # Create a mock seeder (no API key needed for this test)
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        
        try:
            seeder = MagicBookSeeder(api_key="test-key", database_url="sqlite:///:memory:")
            
            # Test known book patterns
            test_cases = [
                ("epdf.pub_the-dai-vernon-book-of-magic", "The Dai Vernon Book of Magic", "Dai Vernon"),
                ("david-roths-expert-coin-magic", "David Roth's Expert Coin Magic", "David Roth"),
                ("HugardCoinMagic", "Coin Magic", "Jean Hugard"),
                ("Encyclopedic Dictionary of Mentalism", "Encyclopedic Dictionary of Mentalism - Volume 3", "Richard Webster")
            ]
            
            for filename, expected_title, expected_author in test_cases:
                metadata = seeder.lookup_book_metadata(filename)
                print(f"  📖 {filename}")
                print(f"     Title: {metadata.title}")
                print(f"     Author: {metadata.author}")
                print(f"     Year: {metadata.publication_year}")
                print(f"     ISBN: {metadata.isbn}")
                
                if expected_title.lower() in metadata.title.lower():
                    print("     ✅ Title match")
                else:
                    print("     ❌ Title mismatch")
                    
                if expected_author.lower() in metadata.author.lower():
                    print("     ✅ Author match")
                else:
                    print("     ❌ Author mismatch")
                print()
            
        except Exception as e:
            print(f"❌ Error in metadata test: {e}")


def test_database_operations():
    """Test database setup and table creation"""
    print("\n💾 Testing database operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        
        try:
            seeder = MagicBookSeeder(
                api_key="test-key", 
                database_url=f"sqlite:///{db_path}"
            )
            
            # Test table creation
            seeder.create_tables()
            print("✅ Database tables created successfully")
            
            # Test database clearing
            seeder.clear_database()
            print("✅ Database cleared successfully")
            
        except Exception as e:
            print(f"❌ Error in database test: {e}")


def test_similarity_calculation():
    """Test trick similarity calculation"""
    print("\n🔗 Testing similarity calculation...")
    
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    
    try:
        seeder = MagicBookSeeder(api_key="test-key", database_url="sqlite:///:memory:")
        
        # Create mock tricks
        trick1 = Mock()
        trick1.name = "Ambitious Card"
        trick1.effect_type = "Card"
        trick1.description = "A selected card repeatedly rises to the top of the deck"
        
        trick2 = Mock()
        trick2.name = "Ambitious Card Routine"
        trick2.effect_type = "Card"
        trick2.description = "The chosen card keeps appearing at the top of the deck"
        
        trick3 = Mock()
        trick3.name = "Coin Vanish"
        trick3.effect_type = "Coin"
        trick3.description = "A coin disappears from the magician's hand"
        
        # Test similarity calculations
        sim1_2 = seeder.calculate_trick_similarity(trick1, trick2)
        sim1_3 = seeder.calculate_trick_similarity(trick1, trick3)
        
        print(f"  🎭 Similarity between similar card tricks: {sim1_2:.2f}")
        print(f"  🎭 Similarity between card and coin trick: {sim1_3:.2f}")
        
        if sim1_2 > sim1_3:
            print("✅ Similar tricks have higher similarity score")
        else:
            print("❌ Similar tricks should have higher similarity score")
            
        # Test relationship determination
        rel_high = seeder.determine_relationship_type(trick1, trick2, 0.95)
        rel_med = seeder.determine_relationship_type(trick1, trick2, 0.75)
        rel_low = seeder.determine_relationship_type(trick1, trick3, 0.6)
        
        print(f"  🔗 High similarity (0.95): {rel_high}")
        print(f"  🔗 Medium similarity (0.75): {rel_med}")
        print(f"  🔗 Low similarity (0.6): {rel_low}")
        
    except Exception as e:
        print(f"❌ Error in similarity test: {e}")


def test_magic_trick_dataclass():
    """Test MagicTrick dataclass functionality"""
    print("\n🎭 Testing MagicTrick dataclass...")
    
    try:
        # Test creating a trick
        trick = MagicTrick(
            name="Test Trick",
            effect_type="Card",
            description="A test magic trick",
            method="Secret method",
            props=["Playing cards", "Magic wand"],
            difficulty="Beginner",
            page_start=10,
            page_end=15,
            confidence=0.85
        )
        
        print(f"  📝 Name: {trick.name}")
        print(f"  📝 Effect: {trick.effect_type}")
        print(f"  📝 Props: {trick.props}")
        print(f"  📝 Difficulty: {trick.difficulty}")
        print(f"  📝 Confidence: {trick.confidence}")
        print("✅ MagicTrick dataclass working correctly")
        
    except Exception as e:
        print(f"❌ Error in MagicTrick test: {e}")


def main():
    """Run all tests"""
    print("🧪 Testing Magic Book Seeder Components")
    print("=" * 50)
    
    # Check if required packages are available
    try:
        import anthropic
        import PyPDF2
        import sqlalchemy
        import requests
        print("✅ All required packages are available")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Install requirements: pip install -r seeder_requirements.txt")
        return
    
    # Run tests
    test_magic_trick_dataclass()
    test_book_metadata_lookup()
    test_database_operations()
    test_similarity_calculation()
    
    print("\n🎉 All tests completed!")
    print("\n📋 To use the seeder:")
    print("1. Set your Anthropic API key:")
    print("   export ANTHROPIC_API_KEY=your_api_key_here")
    print("2. Run the seeder:")
    print("   python seed_database_with_claude.py")
    print("3. Or test with books-only mode:")
    print("   python seed_database_with_claude.py --books-only")


if __name__ == "__main__":
    main()