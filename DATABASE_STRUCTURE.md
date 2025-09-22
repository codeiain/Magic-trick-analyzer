# Magic Trick Analyzer - Database Structure Guide

## Overview

This document provides comprehensive guidance on the database structure for the Magic Trick Analyzer system. The system uses SQLite with SQLAlchemy ORM and implements a clean architecture with domain entities, value objects, and proper data validation.

## 📊 Core Database Tables

### 1. Books (`books`)
Stores information about magic books that contain tricks.

**Fields:**
- `id` (String, Primary Key) - UUID identifier
- `title` (String, NOT NULL) - Book title
- `author` (String, NOT NULL) - Book author name
- `file_path` (String, NOT NULL, UNIQUE) - Path to uploaded PDF file
- `publication_year` (Integer, Optional) - Year of publication
- `isbn` (String, Optional) - ISBN number
- `processed_at` (DateTime, Optional) - When OCR processing completed
- `text_content` (Text, Optional) - Extracted text from OCR
- `ocr_confidence` (Float, Optional) - OCR accuracy score (0.0-1.0)
- `character_count` (Integer, Optional) - Number of characters in extracted text
- `created_at` (DateTime) - Record creation timestamp
- `updated_at` (DateTime) - Last modification timestamp

**Example Data Structure:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Expert Card Technique",
  "author": "Jean Hugard",
  "file_path": "/app/data/books/expert-card-technique.pdf",
  "publication_year": 1950,
  "isbn": "978-0486217550",
  "ocr_confidence": 0.95,
  "character_count": 450000,
  "processed_at": "2023-10-15T14:30:00Z"
}
```

**Validation Rules:**
- Title cannot be empty
- Author cannot be empty
- File path must be unique across all books
- OCR confidence must be between 0.0 and 1.0

### 2. Effect Types (`effect_types`)
Defines the categories of magic effects/tricks.

**Fields:**
- `id` (String, Primary Key) - UUID identifier
- `name` (String, NOT NULL, UNIQUE) - Effect type name
- `description` (Text, Optional) - Detailed description
- `category` (String, Optional) - Broader category (e.g., "Close-up", "Stage")
- `created_at` (DateTime) - Record creation timestamp
- `updated_at` (DateTime) - Last modification timestamp

**Common Effect Types:**
```
- Card          (Card manipulations and tricks)
- Coin          (Coin magic and sleight of hand)
- Mentalism     (Mind reading, predictions)
- Close-Up      (Close-up magic effects)
- Ball          (Ball manipulations)
- Money         (Currency-based tricks)
- Penetration   (Objects passing through barriers)
- Levitation    (Floating objects)
- Mind Reading  (Telepathy effects)
- Paper         (Paper-based tricks)
```

### 3. Tricks (`tricks`)
Core table storing individual magic tricks.

**Fields:**
- `id` (String, Primary Key) - UUID identifier
- `book_id` (String, Foreign Key → books.id, NOT NULL) - Source book reference
- `effect_type_id` (String, Foreign Key → effect_types.id, NOT NULL) - Effect category
- `name` (String, NOT NULL) - Trick name/title
- `description` (Text, NOT NULL) - What the audience sees
- `method` (Text, Optional) - How the trick is performed (secret)
- `props` (Text, Optional) - JSON array of required props
- `difficulty` (String, NOT NULL) - Skill level required
- `page_start` (Integer, Optional) - Starting page in book
- `page_end` (Integer, Optional) - Ending page in book
- `confidence` (Float, Optional) - AI extraction confidence (0.0-1.0)
- `created_at` (DateTime) - Record creation timestamp
- `updated_at` (DateTime) - Last modification timestamp

**Difficulty Levels:**
- `beginner` - Easy to learn, minimal skill required
- `intermediate` - Moderate skill, some practice needed
- `advanced` - Significant skill and practice required
- `expert` - Master-level technique required

**Validation Rules:**
- Name cannot be empty
- Description cannot be empty
- Props must be valid JSON array when present
- Page start must be positive integer
- Page end must be >= page start
- Confidence must be between 0.0 and 1.0
- Difficulty must be one of the four valid levels

**Fields:**
- `id` (String, Primary Key) - UUID identifier
- `trick_id` (String, Foreign Key → tricks.id, NOT NULL) - Reviewed trick
- `book_id` (String, Foreign Key → books.id, NOT NULL) - Source book
- `reviewer_id` (String, Optional) - Future user system identifier
- `is_accurate` (Boolean, Optional) - True=correct, False=incorrect, None=pending
- `confidence_score` (Float, Optional) - Reviewer confidence (0.0-1.0)
- `review_notes` (Text, Optional) - Reviewer comments
- `corrected_name` (String, Optional) - Fixed trick name if wrong
- `corrected_effect_type` (String, Optional) - Fixed effect type if wrong
- `corrected_description` (Text, Optional) - Fixed description if wrong
- `corrected_difficulty` (String, Optional) - Fixed difficulty if wrong
- `use_for_training` (Boolean, Default: True) - Include in training dataset
- `quality_score` (Float, Optional) - Overall quality assessment
- `created_at` (DateTime) - Record creation timestamp
- `updated_at` (DateTime) - Last modification timestamp

**Review Workflow:**
1. AI extracts trick from book → creates `tricks` record
2. Human reviewer evaluates → creates `training_reviews` record
3. If accurate: `is_accurate = True`, `use_for_training = True`
4. If inaccurate: `is_accurate = False`, corrected fields populated
5. Training system uses reviewed tricks with `use_for_training = True`

### 5. Training Datasets (`training_datasets`)
Manages AI model training datasets and progress.

**Fields:**
- `id` (String, Primary Key) - UUID identifier
- `name` (String, NOT NULL) - Dataset name
- `description` (Text, Optional) - Dataset description
- `version` (String, NOT NULL, Default: "1.0") - Dataset version
- `total_tricks` (Integer, Default: 0) - Total tricks in dataset
- `reviewed_tricks` (Integer, Default: 0) - Number of reviewed tricks
- `accuracy_rate` (Float, Optional) - Percentage of accurate detections
- `status` (String, Default: "building") - Dataset status
- `is_active` (Boolean, Default: False) - Currently active dataset
- `training_progress` (Integer, Default: 0) - Training progress (0-100%)
- `training_message` (String, Optional) - Current training status message
- `last_training_job_id` (String, Optional) - Redis job ID for training
- `model_accuracy` (Float, Optional) - Trained model accuracy
- `validation_score` (Float, Optional) - Validation set performance
- `model_version` (String, Optional) - Trained model version identifier
- `training_duration` (Float, Optional) - Training time in seconds
- `created_at` (DateTime) - Record creation timestamp
- `updated_at` (DateTime) - Last modification timestamp

**Dataset Status Values:**
- `building` - Collecting training data
- `ready` - Ready for training
- `training` - Currently training model
- `trained` - Training completed
- `deployed` - Model deployed for inference

### 6. Cross References (`cross_references`)
Links related tricks across different books.

**Fields:**
- `id` (String, Primary Key) - UUID identifier
- `source_trick_id` (String, Foreign Key → tricks.id, NOT NULL) - Source trick
- `target_trick_id` (String, Foreign Key → tricks.id, NOT NULL) - Related trick
- `relationship_type` (String, NOT NULL) - Type of relationship
- `similarity_score` (Float, Optional) - AI-computed similarity (0.0-1.0)
- `notes` (Text, Optional) - Human-added notes about relationship
- `created_at` (DateTime) - Record creation timestamp

**Relationship Types:**
- `variation` - Different version of same trick
- `prerequisite` - Source trick must be learned first
- `similar_effect` - Similar audience experience
- `same_method` - Uses same underlying technique
- `improved_version` - Target is enhanced version of source

## 🔧 Data Validation & Business Rules

### Value Objects
The system uses immutable value objects for data validation:

#### **TrickId & BookId**
```python
# UUID-based identifiers
TrickId(uuid4())  # Auto-generated
BookId(uuid4())   # Auto-generated
```

#### **Title**
```python
Title("The Ambitious Card")  # Must not be empty
```

#### **DifficultyLevel**
```python
# Enum with four levels
DifficultyLevel.BEGINNER     # "beginner"
DifficultyLevel.INTERMEDIATE # "intermediate" 
DifficultyLevel.ADVANCED     # "advanced"
DifficultyLevel.EXPERT       # "expert"
```

#### **Props**
```python
# List of required items
Props(["deck of cards", "close-up pad"])  # Immutable list
```

#### **PageRange**
```python
PageRange(start=42)           # Single page
PageRange(start=42, end=45)   # Page range
# start must be positive, end >= start
```

#### **Confidence**
```python
Confidence(0.95)  # Must be between 0.0 and 1.0
```

### JSON Data Formats

#### **Props Field Storage**
```json
// Stored as JSON string in database
"[\"deck of cards\", \"close-up pad\", \"rubber band\"]"

// Retrieved as list in application
["deck of cards", "close-up pad", "rubber band"]
```

## 📝 API Data Examples


## 🔄 Data Flow

## ⚠️ Important Constraints

### Database Constraints
- Foreign key relationships are enforced
- Unique constraints on `books.file_path` and `effect_types.name`
- NOT NULL constraints on required fields

## 🛠️ Development Guidelines

### Adding New Effect Types
```sql
INSERT INTO effect_types (id, name, description, category)
VALUES (
  '<uuid>', 
  'rope_magic', 
  'Tricks involving rope manipulations', 
  'close_up'
);
```



This structure ensures data integrity, supports AI model training, and provides a solid foundation for the magic trick analysis system.