#!/usr/bin/env python3
"""
PDF Text Extraction and Analysis Tool for Dai Vernon Book
Extracts text content from PDF to compare with database entries.
"""
import PyPDF2
import re
from pathlib import Path

def extract_pdf_text(pdf_path):
    """Extract text from PDF file."""
    text_content = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            print(f"Extracting text from {total_pages} pages...")
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    text = page.extract_text()
                    text_content.append({
                        'page': page_num,
                        'text': text.strip()
                    })
                    
                    if page_num % 50 == 0:
                        print(f"Processed {page_num}/{total_pages} pages...")
                        
                except Exception as e:
                    print(f"Error extracting text from page {page_num}: {e}")
                    
        return text_content, total_pages
        
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return [], 0

def find_table_of_contents(text_content):
    """Look for table of contents or chapter headings."""
    toc_patterns = [
        r'TABLE OF CONTENTS',
        r'CONTENTS',
        r'CHAPTER \d+',
        r'Chapter \d+',
        r'\d+\.\s+[A-Z][A-Z\s]+',  # Numbered sections like "1. THE EVOLUTION"
    ]
    
    toc_pages = []
    
    for page_data in text_content[:20]:  # Check first 20 pages for TOC
        page_text = page_data['text'].upper()
        
        for pattern in toc_patterns:
            if re.search(pattern, page_text):
                toc_pages.append({
                    'page': page_data['page'],
                    'text': page_data['text']
                })
                break
    
    return toc_pages

def identify_trick_sections(text_content):
    """Identify sections that appear to be actual magic tricks vs biographical content."""
    
    # Patterns that suggest actual trick descriptions
    trick_patterns = [
        r'EFFECT:',
        r'METHOD:',
        r'PERFORMANCE:',
        r'The spectator',
        r'The performer',
        r'The audience',
        r'is asked to',
        r'coin.*pass.*through',
        r'card.*changes',
        r'vanishes',
        r'appears',
        r'restored'
    ]
    
    # Patterns that suggest biographical/instructional content
    bio_patterns = [
        r'Vernon',
        r'was born',
        r'In \d{4}',
        r'young.*boy',
        r'years later',
        r'during his',
        r'he met',
        r'travelled to'
    ]
    
    analysis = []
    
    for page_data in text_content:
        page_text = page_data['text']
        
        trick_score = sum(1 for pattern in trick_patterns if re.search(pattern, page_text, re.IGNORECASE))
        bio_score = sum(1 for pattern in bio_patterns if re.search(pattern, page_text, re.IGNORECASE))
        
        page_type = "unknown"
        if trick_score > bio_score and trick_score > 0:
            page_type = "trick"
        elif bio_score > trick_score and bio_score > 0:
            page_type = "biographical"
        elif trick_score == bio_score and trick_score > 0:
            page_type = "mixed"
        
        analysis.append({
            'page': page_data['page'],
            'type': page_type,
            'trick_score': trick_score,
            'bio_score': bio_score,
            'text_preview': page_text[:200] + "..." if len(page_text) > 200 else page_text
        })
    
    return analysis

def main():
    pdf_path = Path("c:/docker/pdf-organizer/input/epdf.pub_the-dai-vernon-book-of-magic.pdf")
    
    if not pdf_path.exists():
        print(f"PDF file not found: {pdf_path}")
        return
    
    print("Analyzing Dai Vernon Book of Magic PDF...")
    print("=" * 60)
    
    # Extract text
    text_content, total_pages = extract_pdf_text(pdf_path)
    
    if not text_content:
        print("Failed to extract text from PDF")
        return
    
    print(f"\nSuccessfully extracted text from {len(text_content)} pages")
    
    # Find table of contents
    print("\nLooking for table of contents...")
    toc_pages = find_table_of_contents(text_content)
    
    if toc_pages:
        print(f"Found potential TOC on pages: {[p['page'] for p in toc_pages]}")
        for toc in toc_pages:
            print(f"\nPage {toc['page']} content preview:")
            print(toc['text'][:500])
            print("..." if len(toc['text']) > 500 else "")
    else:
        print("No clear table of contents found")
    
    # Analyze page content types
    print("\nAnalyzing page content types...")
    analysis = identify_trick_sections(text_content)
    
    # Summary statistics
    trick_pages = [a for a in analysis if a['type'] == 'trick']
    bio_pages = [a for a in analysis if a['type'] == 'biographical']
    mixed_pages = [a for a in analysis if a['type'] == 'mixed']
    unknown_pages = [a for a in analysis if a['type'] == 'unknown']
    
    print(f"\nContent Analysis Summary:")
    print(f"  Trick description pages: {len(trick_pages)}")
    print(f"  Biographical pages: {len(bio_pages)}")
    print(f"  Mixed content pages: {len(mixed_pages)}")
    print(f"  Unknown/other pages: {len(unknown_pages)}")
    
    # Show some examples
    if trick_pages:
        print(f"\nSample trick pages:")
        for page in trick_pages[:3]:
            print(f"  Page {page['page']}: {page['text_preview']}")
    
    if bio_pages:
        print(f"\nSample biographical pages:")
        for page in bio_pages[:3]:
            print(f"  Page {page['page']}: {page['text_preview']}")
    
    # Save detailed analysis
    output_file = Path("c:/docker/magic-trick-analyzer/dai_vernon_analysis.txt")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Dai Vernon Book Analysis\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total pages processed: {total_pages}\n")
            f.write(f"Trick pages: {len(trick_pages)}\n")
            f.write(f"Biographical pages: {len(bio_pages)}\n")
            f.write(f"Mixed pages: {len(mixed_pages)}\n")
            f.write(f"Unknown pages: {len(unknown_pages)}\n\n")
            
            f.write("Page-by-page analysis:\n")
            f.write("-" * 30 + "\n")
            
            for page_analysis in analysis:
                f.write(f"Page {page_analysis['page']:3d}: {page_analysis['type']:12s} "
                       f"(trick={page_analysis['trick_score']}, bio={page_analysis['bio_score']})\n")
                f.write(f"    {page_analysis['text_preview']}\n\n")
        
        print(f"\nDetailed analysis saved to: {output_file}")
        
    except Exception as e:
        print(f"Error saving analysis: {e}")

if __name__ == "__main__":
    main()