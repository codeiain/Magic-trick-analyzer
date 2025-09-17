"""
Simplified PDF processing infrastructure using PyMuPDF for text extraction.
Extracts text and metadata from PDF files. OCR functionality moved to dedicated OCR service.
"""
import fitz  # PyMuPDF
import logging
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
    Uses PyMuPDF for text extraction. OCR processing delegated to dedicated OCR service.
    """
    
    def __init__(self, enable_ocr: bool = False):  # OCR flag kept for compatibility but ignored
        self._logger = logging.getLogger(__name__)
        # OCR functionality moved to dedicated OCR service
    
    async def extract_text_and_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text and metadata from PDF file.
        Returns text for PDFs with existing text layer. For scanned PDFs, delegates to OCR service via job queue.
        """
        try:
            # Extract existing text
            text = await self._extract_text_direct(file_path)
            metadata = await self._extract_metadata(file_path)
            
            return {
                'text': text,
                'metadata': metadata.__dict__,
                'has_text_layer': bool(text.strip()),
                'requires_ocr': not bool(text.strip())
            }
            
        except Exception as e:
            self._logger.error(f"Error extracting from {file_path}: {str(e)}")
            return {
                'text': '',
                'metadata': PDFMetadata().__dict__,
                'has_text_layer': False,
                'requires_ocr': True,
                'error': str(e)
            }
    
    async def extract_text(self, file_path: str) -> str:
        """
        Extract all text from a PDF file.
        Only returns text from existing text layers - no OCR processing.
        """
        return await self._extract_text_direct(file_path)
    
    async def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF file."""
        try:
            metadata = await self._extract_metadata(file_path)
            return metadata.__dict__
        except Exception as e:
            self._logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            return PDFMetadata().__dict__
    
    async def _extract_text_direct(self, file_path: str) -> str:
        """Extract text directly from PDF using PyMuPDF (no OCR)."""
        self._logger.debug(f"Extracting text from {file_path}")
        
        try:
            doc = fitz.open(file_path)
            full_text = ""
            
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                
                if page_text.strip():
                    full_text += f"\n--- Page {page_num + 1} ---\n"
                    full_text += page_text
            
            doc.close()
            self._logger.debug(f"Extracted {len(full_text)} characters from {file_path}")
            
            return full_text
            
        except Exception as e:
            self._logger.error(f"Error in direct text extraction from {file_path}: {str(e)}")
            raise
    
    async def _extract_metadata(self, file_path: str) -> PDFMetadata:
        """Extract metadata from PDF file."""
        try:
            doc = fitz.open(file_path)
            metadata_dict = doc.metadata
            page_count = doc.page_count
            
            # Check if PDF has text content
            has_text = False
            try:
                # Sample first few pages to check for text
                sample_pages = min(3, page_count)
                for i in range(sample_pages):
                    page = doc.load_page(i)
                    if page.get_text().strip():
                        has_text = True
                        break
            except:
                pass
            
            doc.close()
            
            # Get file size
            file_size = Path(file_path).stat().st_size
            
            metadata = PDFMetadata(
                title=self._clean_metadata_string(metadata_dict.get('title')),
                author=self._clean_metadata_string(metadata_dict.get('author')),
                creator=self._clean_metadata_string(metadata_dict.get('creator')),
                producer=self._clean_metadata_string(metadata_dict.get('producer')),
                subject=self._clean_metadata_string(metadata_dict.get('subject')),
                creation_date=metadata_dict.get('creationDate'),
                modification_date=metadata_dict.get('modDate'),
                page_count=page_count,
                has_text=has_text,
                file_size=file_size
            )
            
            return metadata
            
        except Exception as e:
            self._logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            return PDFMetadata()
    
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
    
    async def validate_pdf(self, file_path: str) -> bool:
        """Validate that file is a readable PDF."""
        try:
            doc = fitz.open(file_path)
            is_valid = doc.page_count > 0
            doc.close()
            return is_valid
        except Exception:
            return False