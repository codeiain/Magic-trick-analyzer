"""
PDF processing infrastructure using PyMuPDF and OCR.
Extracts text and metadata from PDF files without external APIs.
"""
import fitz  # PyMuPDF
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class PDFMetadata:
    """Container for PDF metadata."""
    title: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    subject: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: int = 0
    has_text: bool = False
    file_size: int = 0


class PDFTextExtractor:
    """
    Infrastructure service for extracting text and metadata from PDF files.
    Uses PyMuPDF for text extraction and OCRmyPDF for scanned documents.
    """
    
    def __init__(self, enable_ocr: bool = True):
        self._logger = logging.getLogger(__name__)
        self._enable_ocr = enable_ocr
        
    async def extract_text(self, file_path: str) -> str:
        """
        Extract all text from a PDF file.
        Falls back to OCR if no text is found.
        """
        try:
            # First try direct text extraction
            text = await self._extract_text_direct(file_path)
            
            # If no text found and OCR enabled, try OCR
            if not text.strip() and self._enable_ocr:
                self._logger.info(f"No text found in {file_path}, attempting OCR...")
                text = await self._extract_text_with_ocr(file_path)
            
            return text
            
        except Exception as e:
            self._logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF file."""
        try:
            doc = fitz.open(file_path)
            metadata = doc.metadata
            page_count = doc.page_count
            
            # Get file stats
            file_stats = Path(file_path).stat()
            
            # Check if document has extractable text
            has_text = False
            for page_num in range(min(3, page_count)):  # Check first 3 pages
                page = doc[page_num]
                if page.get_text().strip():
                    has_text = True
                    break
            
            doc.close()
            
            # Clean and structure metadata
            cleaned_metadata = {
                'title': self._clean_metadata_string(metadata.get('title')),
                'author': self._clean_metadata_string(metadata.get('author')),
                'creator': self._clean_metadata_string(metadata.get('creator')),
                'producer': self._clean_metadata_string(metadata.get('producer')),
                'subject': self._clean_metadata_string(metadata.get('subject')),
                'creation_date': metadata.get('creationDate'),
                'modification_date': metadata.get('modDate'),
                'page_count': page_count,
                'has_text': has_text,
                'file_size': file_stats.st_size
            }
            
            # Try to extract year from dates
            if cleaned_metadata['creation_date']:
                year = self._extract_year_from_date(cleaned_metadata['creation_date'])
                if year:
                    cleaned_metadata['year'] = year
            
            return cleaned_metadata
            
        except Exception as e:
            self._logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            return {
                'title': None,
                'author': None,
                'page_count': 0,
                'has_text': False,
                'file_size': Path(file_path).stat().st_size if Path(file_path).exists() else 0
            }
    
    async def extract_text_by_pages(self, file_path: str) -> List[str]:
        """Extract text page by page."""
        try:
            doc = fitz.open(file_path)
            pages = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                page_text = page.get_text()
                pages.append(page_text)
            
            doc.close()
            return pages
            
        except Exception as e:
            self._logger.error(f"Error extracting pages from {file_path}: {str(e)}")
            return []
    
    async def _extract_text_direct(self, file_path: str) -> str:
        """Extract text directly from PDF using PyMuPDF."""
        doc = fitz.open(file_path)
        text_parts = []
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            
            # Try different text extraction methods
            text = page.get_text()
            
            # If no text, try text blocks
            if not text.strip():
                blocks = page.get_text("blocks")
                text = " ".join([block[4] for block in blocks if len(block) > 4])
            
            text_parts.append(text)
        
        doc.close()
        
        full_text = "\n\n".join(text_parts)
        self._logger.debug(f"Extracted {len(full_text)} characters from {file_path}")
        
        return full_text
    
    async def _extract_text_with_ocr(self, file_path: str) -> str:
        """Extract text using OCR for scanned PDFs."""
        if not self._enable_ocr:
            return ""
        
        try:
            # Create temporary file for OCR output
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Run OCRmyPDF to add text layer
            cmd = [
                'ocrmypdf',
                '--redo-ocr',   # OCR pages that need it
                '--quiet',      # Suppress output
                file_path,
                temp_path
            ]
            
            self._logger.info(f"Starting OCR command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout
            self._logger.info(f"OCR command completed with return code: {result.returncode}")
            
            if result.returncode == 0:
                # Extract text from OCR'd PDF
                text = await self._extract_text_direct(temp_path)
                Path(temp_path).unlink()  # Clean up temp file
                
                self._logger.info(f"OCR extracted {len(text)} characters from {file_path}")
                return text
            else:
                self._logger.warning(f"OCR failed for {file_path}: {result.stderr}")
                Path(temp_path).unlink()  # Clean up temp file
                return ""
                
        except subprocess.TimeoutExpired:
            self._logger.error(f"OCR timeout for {file_path} after 300 seconds")
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            return ""
        except FileNotFoundError:
            self._logger.warning("OCRmyPDF not found, skipping OCR")
            return ""
        except Exception as e:
            self._logger.error(f"OCR error for {file_path}: {str(e)}")
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            return ""
    
    def _clean_metadata_string(self, value: Optional[str]) -> Optional[str]:
        """Clean and validate metadata strings."""
        if not value:
            return None
        
        # Remove common junk values
        junk_values = ['unknown', 'untitled', '', 'none', 'null']
        if value.lower().strip() in junk_values:
            return None
        
        # Clean whitespace
        cleaned = value.strip()
        if not cleaned:
            return None
        
        # Remove very long values (likely corrupted)
        if len(cleaned) > 200:
            return cleaned[:200] + "..."
        
        return cleaned
    
    def _extract_year_from_date(self, date_string: str) -> Optional[int]:
        """Extract year from PDF date string."""
        try:
            # PDF date format: D:YYYYMMDDHHmmSSOHH'mm
            if date_string.startswith("D:"):
                year_str = date_string[2:6]
                return int(year_str)
        except (ValueError, IndexError):
            pass
        
        return None
    
    async def validate_pdf(self, file_path: str) -> bool:
        """Validate that file is a readable PDF."""
        try:
            doc = fitz.open(file_path)
            is_valid = doc.page_count > 0
            doc.close()
            return is_valid
        except Exception:
            return False


class PDFWatcher:
    """
    File system watcher for PDF files.
    Monitors directories for new PDF files to process.
    """
    
    def __init__(self, watch_directories: List[str]):
        self._logger = logging.getLogger(__name__)
        self._watch_directories = watch_directories
        self._pdf_extractor = PDFTextExtractor()
    
    async def scan_for_new_pdfs(self) -> List[str]:
        """Scan watch directories for PDF files."""
        pdf_files = []
        
        for directory in self._watch_directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                self._logger.warning(f"Watch directory does not exist: {directory}")
                continue
            
            # Find all PDF files recursively
            for pdf_file in dir_path.rglob("*.pdf"):
                if await self._pdf_extractor.validate_pdf(str(pdf_file)):
                    pdf_files.append(str(pdf_file))
                else:
                    self._logger.warning(f"Invalid PDF file: {pdf_file}")
        
        self._logger.info(f"Found {len(pdf_files)} PDF files")
        return pdf_files
    
    def add_watch_directory(self, directory: str) -> None:
        """Add a new directory to watch."""
        if directory not in self._watch_directories:
            self._watch_directories.append(directory)
            self._logger.info(f"Added watch directory: {directory}")
    
    def remove_watch_directory(self, directory: str) -> None:
        """Remove a directory from watch list."""
        if directory in self._watch_directories:
            self._watch_directories.remove(directory)
            self._logger.info(f"Removed watch directory: {directory}")


class PDFProcessor:
    """
    High-level PDF processor that coordinates extraction and analysis.
    """
    
    def __init__(self, enable_ocr: bool = True):
        self._extractor = PDFTextExtractor(enable_ocr)
        self._logger = logging.getLogger(__name__)
    
    async def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Process a PDF file completely - extract text, metadata, and basic analysis.
        """
        self._logger.info(f"Processing PDF: {file_path}")
        
        # Validate PDF first
        if not await self._extractor.validate_pdf(file_path):
            raise ValueError(f"Invalid PDF file: {file_path}")
        
        # Extract metadata
        metadata = await self._extractor.extract_metadata(file_path)
        
        # Extract text
        full_text = await self._extractor.extract_text(file_path)
        
        # Basic text analysis
        text_stats = self._analyze_text(full_text)
        
        result = {
            'file_path': file_path,
            'metadata': metadata,
            'text': full_text,
            'text_stats': text_stats,
            'processing_status': 'success'
        }
        
        self._logger.info(
            f"Successfully processed {file_path}: "
            f"{len(full_text)} chars, {text_stats['word_count']} words"
        )
        
        return result
    
    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Basic text analysis for statistics."""
        if not text:
            return {
                'character_count': 0,
                'word_count': 0,
                'line_count': 0,
                'has_content': False
            }
        
        words = text.split()
        lines = text.split('\n')
        
        return {
            'character_count': len(text),
            'word_count': len(words),
            'line_count': len(lines),
            'has_content': len(text.strip()) > 0,
            'average_word_length': sum(len(word) for word in words) / len(words) if words else 0
        }
