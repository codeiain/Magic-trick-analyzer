"""
Application services for PDF processing.
These orchestrate domain logic and coordinate with infrastructure.
Following Clean Architecture principles.
"""
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path

from ...domain.entities.magic import Book, Trick
from ...domain.value_objects.common import Title, Author, BookId, EffectType, Confidence
from ...domain.repositories.magic_repositories import BookRepository, TrickRepository


class PDFProcessingService:
    """
    Application service for processing PDF files.
    Coordinates between PDF extraction, AI analysis, and domain logic.
    """
    
    def __init__(
        self,
        book_repository: BookRepository,
        trick_repository: TrickRepository,
        pdf_extractor: 'PDFTextExtractor',  # Infrastructure dependency
        trick_detector: 'TrickDetector',    # Infrastructure dependency
        logger: Optional[logging.Logger] = None
    ):
        self._book_repository = book_repository
        self._trick_repository = trick_repository
        self._pdf_extractor = pdf_extractor
        self._trick_detector = trick_detector
        self._logger = logger or logging.getLogger(__name__)
    
    async def process_pdf_file(self, file_path: str, original_filename: Optional[str] = None) -> Optional[Book]:
        """
        Process a single PDF file to extract tricks and metadata.
        Returns the processed Book entity or None if processing fails.
        """
        try:
            self._logger.info(f"Starting PDF processing for: {file_path}")
            
            # Check if book already exists
            existing_book = await self._book_repository.find_by_file_path(file_path)
            if existing_book and existing_book.is_processed():
                self._logger.info(f"Book already processed: {file_path}")
                return existing_book
            
            # Extract basic metadata and text from PDF
            pdf_metadata = await self._pdf_extractor.extract_metadata(file_path)
            full_text = await self._pdf_extractor.extract_text(file_path)
            
            if not full_text.strip():
                self._logger.warning(f"No text extracted from PDF: {file_path}")
                return None
            
            # Create or update book entity (pass original filename for better title extraction)
            book = await self._create_or_update_book(file_path, pdf_metadata, original_filename)
            
            # Detect tricks in the text
            detected_tricks = await self._trick_detector.detect_tricks(full_text, book.id)
            
            # Save tricks to repository first
            for trick in detected_tricks:
                await self._trick_repository.save(trick)
            
            # Add tricks to book
            for trick in detected_tricks:
                book.add_trick(trick)
            
            # Mark book as processed
            book.mark_as_processed()
            
            # Save to repository
            await self._book_repository.save(book)
            
            self._logger.info(
                f"Successfully processed PDF: {file_path} "
                f"({len(detected_tricks)} tricks found)"
            )
            
            return book
            
        except Exception as e:
            self._logger.error(f"Error processing PDF {file_path}: {str(e)}")
            raise
    
    async def process_multiple_pdfs(self, file_paths: List[str]) -> List[Book]:
        """
        Process multiple PDF files.
        Returns list of successfully processed books.
        """
        processed_books = []
        
        for file_path in file_paths:
            try:
                book = await self.process_pdf_file(file_path)
                if book:
                    processed_books.append(book)
            except Exception as e:
                self._logger.error(f"Failed to process {file_path}: {str(e)}")
                # Continue with other files
                continue
        
        return processed_books
    
    async def reprocess_book(self, book_id: BookId) -> Optional[Book]:
        """
        Reprocess an existing book (useful after AI model improvements).
        """
        book = await self._book_repository.find_by_id(book_id)
        if not book:
            self._logger.warning(f"Book not found for reprocessing: {book_id}")
            return None
        
        self._logger.info(f"Reprocessing book: {book.title}")
        
        # Clear existing tricks
        for trick in book.tricks:
            book.remove_trick(trick)
        
        # Process again
        return await self.process_pdf_file(book.file_path)
    
    async def _create_or_update_book(
        self, 
        file_path: str, 
        pdf_metadata: Dict[str, Any],
        original_filename: Optional[str] = None
    ) -> Book:
        """
        Create a new book or update existing one with PDF metadata.
        """
        # Extract title and author from metadata or filename
        title = self._extract_title(pdf_metadata, file_path, original_filename)
        author = self._extract_author(pdf_metadata, file_path, original_filename)
        
        # Check if book already exists
        existing_book = await self._book_repository.find_by_title_and_author(
            str(title), str(author)
        )
        
        if existing_book:
            return existing_book
        
        # Create new book
        book = Book(
            title=title,
            author=author,
            file_path=file_path,
            publication_year=pdf_metadata.get('year'),
            isbn=pdf_metadata.get('isbn')
        )
        
        return book
    
    def _extract_title(self, metadata: Dict[str, Any], file_path: str, original_filename: Optional[str] = None) -> Title:
        """Extract title from PDF metadata or filename."""
        # Try metadata first
        if 'title' in metadata and metadata['title']:
            return Title(metadata['title'])
        
        # Use original filename if available, otherwise fall back to file_path
        filename_to_use = original_filename if original_filename else Path(file_path).name
        filename_stem = Path(filename_to_use).stem
        
        # Clean up common filename patterns
        clean_title = self._clean_filename_for_title(filename_stem)
        return Title(clean_title)
    
    def _extract_author(self, metadata: Dict[str, Any], file_path: str, original_filename: Optional[str] = None) -> Author:
        """Extract author from PDF metadata or filename."""
        # Try metadata first
        if 'author' in metadata and metadata['author']:
            return Author(metadata['author'])
        
        # Use original filename if available, otherwise fall back to file_path
        filename_to_use = original_filename if original_filename else Path(file_path).name
        filename_stem = Path(filename_to_use).stem
        author_name = self._extract_author_from_filename(filename_stem)
        
        return Author(author_name or "Unknown Author")
    
    def _clean_filename_for_title(self, filename: str) -> str:
        """Clean filename to create a readable title."""
        # Remove common prefixes
        prefixes_to_remove = ['epdf.pub_', 'www.', 'free-', 'download-']
        for prefix in prefixes_to_remove:
            if filename.startswith(prefix):
                filename = filename[len(prefix):]
        
        # Replace common separators
        filename = filename.replace('-', ' ').replace('_', ' ')
        
        # Remove file extensions if any remain
        filename = filename.replace('.pdf', '')
        
        # Title case
        return ' '.join(word.capitalize() for word in filename.split())
    
    def _extract_author_from_filename(self, filename: str) -> Optional[str]:
        """Try to extract author name from filename patterns."""
        # Common patterns: "author-title", "title-by-author", etc.
        # This is a simplified implementation
        
        # Pattern: "david-roth-expert-coin-magic" -> "David Roth"
        words = filename.replace('_', '-').split('-')
        
        # Look for common author name patterns
        if len(words) >= 2:
            # If first two words look like a name
            first_two = f"{words[0]} {words[1]}".title()
            if self._looks_like_name(first_two):
                return first_two
        
        return None
    
    def _looks_like_name(self, text: str) -> bool:
        """Simple heuristic to check if text looks like an author name."""
        words = text.split()
        if len(words) != 2:
            return False
        
        # Both words should be capitalized and not too long
        return all(
            word.isalpha() and word[0].isupper() and len(word) <= 15 
            for word in words
        )
