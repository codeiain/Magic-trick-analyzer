# AI-Powered Database Seeder

This directory contains an AI-powered database seeder that uses **Claude Sonnet 4** to analyze PDF magic books and populate the database with books, tricks, and cross-references.

## 🎯 Features

- **🤖 AI Analysis**: Uses Claude Sonnet 4 to extract magic tricks from PDFs
- **📚 Book Metadata**: Automatically looks up book information (ISBN, publication year, etc.)
- **🔗 Cross-References**: Generates similarity-based relationships between tricks
- **🔄 Rerunnable**: Safely clears and repopulates the database
- **💾 Database Compatible**: Works with existing Magic Trick Analyzer schema

## 📋 Prerequisites

1. **Anthropic API Key**: You need a Claude API key from Anthropic
2. **Python Dependencies**: Install required packages
3. **PDF Books**: Place magic books in the `trainning book/` directory

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install required Python packages
pip install -r seeder_requirements.txt
```

### 2. Set API Key

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY=your_anthropic_api_key_here

# On Windows PowerShell:
$env:ANTHROPIC_API_KEY="your_anthropic_api_key_here"
```

### 3. Run the Seeder

```bash
# Full seeding (books + AI trick analysis + cross-references)
python seed_database_with_claude.py

# Books only (skip AI analysis)
python seed_database_with_claude.py --books-only

# With verbose logging
python seed_database_with_claude.py --verbose
```

### 4. Test First (Optional)

```bash
# Run tests to verify components work
python test_seeder.py
```

## 📖 Current Books Supported

The seeder recognizes and processes these magic books from the `trainning book/` folder:

1. **The Dai Vernon Book of Magic** (`epdf.pub_the-dai-vernon-book-of-magic.pdf`)
   - Author: Dai Vernon
   - Year: 1957
   - ISBN: 978-0906728000

2. **David Roth's Expert Coin Magic** (`epdf.pub_david-roths-expert-coin-magic.pdf`)
   - Author: David Roth  
   - Year: 1982
   - ISBN: 978-0913072066

3. **Coin Magic** (`HugardCoinMagic.pdf`)
   - Author: Jean Hugard
   - Year: 1954
   - ISBN: 978-0486203812

4. **Encyclopedic Dictionary of Mentalism - Volume 3** (`Encyclopedic Dictionary of Mentalism - Volume 3.pdf`)
   - Author: Richard Webster
   - Year: 2005
   - ISBN: 978-0738706900

## 🔧 Command Line Options

```bash
python seed_database_with_claude.py [options]

Options:
  --api-key API_KEY       Anthropic API key (or set ANTHROPIC_API_KEY env var)
  --database-url URL      Database URL (default: sqlite:///shared/data/magic_tricks.db)
  --books-only           Only process book metadata, skip AI trick analysis
  --verbose              Enable verbose logging
  --help                 Show help message
```

## 🎭 What the Seeder Does

### Step 1: Database Preparation
- Clears existing data (books, tricks, cross-references)
- Creates/verifies database tables

### Step 2: PDF Processing
For each PDF in `trainning book/`:
- Extracts all text content using PyPDF2 or PyMuPDF
- Looks up book metadata (title, author, ISBN, year)
- Saves raw book data to database

### Step 3: AI Analysis (unless `--books-only`)
- Sends book content to Claude Sonnet 4
- Prompts Claude to extract ALL magic tricks with details:
  - Name and effect type
  - Description (what audience sees)
  - Method (how it's performed)
  - Required props
  - Difficulty level
  - Page numbers
- Saves extracted tricks to database

### Step 4: Cross-Reference Generation
- Compares all tricks for similarity
- Uses heuristics based on:
  - Same effect type
  - Similar names
  - Similar descriptions
- Creates bidirectional relationships:
  - `duplicate` (90%+ similarity)
  - `variation` (80%+ similarity)  
  - `similar` (70%+ similarity)
  - `related` (below 70%)

## 📊 Database Schema

The seeder populates these tables:

### `books`
- Basic book information
- Full extracted text content
- OCR metadata

### `tricks`  
- Individual magic tricks
- Effect types and descriptions
- Methods and required props
- Difficulty and page references
- AI confidence scores

### `cross_references`
- Relationships between similar tricks
- Similarity scores and relationship types
- Bidirectional references

## 🧪 Testing

```bash
# Run component tests
python test_seeder.py
```

The test script verifies:
- Book metadata lookup
- Database operations
- Similarity calculations
- Data structures

## ⚠️ Important Notes

### API Costs
- Claude API calls can be expensive for large books
- Each book may cost $1-5 depending on size
- Use `--books-only` to skip AI analysis during testing

### Rate Limits
- Anthropic has API rate limits
- Large books are automatically truncated to fit token limits
- Processing may take several minutes per book

### Data Quality
- Claude Sonnet 4 provides high-quality extraction
- Results have 90%+ confidence scores
- Manual review of extracted tricks is recommended

### File Requirements
- PDFs must contain readable text (not just scanned images)
- OCR preprocessing may be needed for old scanned books
- Filename patterns help with metadata recognition

## 🔍 Troubleshooting

### "No text extracted from PDF"
- PDF may be image-based - needs OCR preprocessing
- Try different PDF processing library (PyMuPDF vs PyPDF2)

### "Anthropic API key required"
- Set the `ANTHROPIC_API_KEY` environment variable
- Or pass `--api-key your_key` as command line argument

### "Error calling Claude API"
- Check your API key is valid and has credits
- Verify internet connection
- Check Anthropic service status

### "Database errors"
- Ensure database directory exists and is writable
- Check database URL format
- Verify SQLAlchemy installation

## 📈 Expected Results

For a typical magic book, expect:
- **Processing time**: 2-5 minutes per book
- **Tricks extracted**: 20-100 tricks per book
- **Cross-references**: 10-50 relationships generated
- **Database size**: ~1-10MB per book

## 🎉 Success Output

When completed successfully, you'll see:
```
🎉 Database Seeding Complete!
======================================================================
📚 Books processed: 4
🎭 Total tricks extracted: 287
🔗 Cross-references generated: 43
💾 Database: sqlite:///shared/data/magic_tricks.db

✨ Ready for magic trick analysis!
```

## 🔄 Re-running

The seeder is designed to be run multiple times safely:
- Always clears existing data first
- Regenerates everything from scratch
- No duplicate records created

This is useful for:
- Testing different parameters
- Updating after book changes
- Fixing any data issues

---

Ready to populate your magic trick database with AI-powered analysis! 🎭✨