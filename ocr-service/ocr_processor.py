"""
OCR Processing Functions

Core OCR functionality extracted from the main application for microservice architecture.
"""

import os
import logging
import tempfile
import shutil
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# OCR and PDF processing imports
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

# Database imports  
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

class OCRProcessor:
    """OCR processing functionality"""
    
    def __init__(self):
        self.db_engine = None
        self.db_session = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database connection"""
        try:
            # Initialize database
            db_url = os.getenv("DATABASE_URL", "sqlite:///data/magic_tricks.db")
            self.db_engine = create_engine(db_url)
            Session = sessionmaker(bind=self.db_engine)
            self.db_session = Session()
            
            logger.info("OCR processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OCR processor: {e}")
            raise
    
    def extract_text_from_pdf(self, file_path: str, book_id: str) -> str:
        """Extract text from PDF using multiple methods"""
        
        logger.info(f"Starting text extraction for {file_path}")
        
        extracted_text = ""
        
        try:
            # Method 1: Try PyMuPDF first (fastest for text-based PDFs)
            logger.info("Attempting PyMuPDF text extraction...")
            extracted_text = self._extract_with_pymupdf(file_path)
            
            if len(extracted_text.strip()) > 100:  # If we got substantial text
                logger.info(f"PyMuPDF extraction successful: {len(extracted_text)} characters")
                return extracted_text
            
            # Method 2: Fall back to OCR for image-based PDFs
            logger.info("PyMuPDF yielded minimal text, trying OCR...")
            extracted_text = self._extract_with_ocr(file_path)
            
            logger.info(f"OCR extraction completed: {len(extracted_text)} characters")
            return extracted_text
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""
    
    def _extract_with_pymupdf(self, file_path: str) -> str:
        """Extract text using PyMuPDF (for text-based PDFs)"""
        
        text_content = ""
        
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():  # Only add if page has text
                    text_content += f"\\n\\n--- Page {page_num + 1} ---\\n\\n"
                    text_content += text
            
            doc.close()
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction error: {e}")
        
        return text_content
    
    def _extract_with_ocr(self, file_path: str) -> str:
        """Extract text using OCR (for image-based PDFs)"""
        
        text_content = ""
        temp_dir = None
        
        try:
            # Create temporary directory for images
            temp_dir = tempfile.mkdtemp()
            
            # Convert PDF to images
            logger.info("Converting PDF to images...")
            images = convert_from_path(
                file_path,
                dpi=200,  # Good balance of quality vs processing time
                output_folder=temp_dir,
                fmt='png'
            )
            
            logger.info(f"Converted {len(images)} pages to images")
            
            # Process each image with OCR
            for i, image in enumerate(images):
                logger.info(f"Processing page {i + 1}/{len(images)} with OCR...")
                
                try:
                    # Use Tesseract OCR
                    page_text = pytesseract.image_to_string(
                        image, 
                        lang='eng',
                        config='--psm 6'  # Uniform block of text
                    )
                    
                    if page_text.strip():  # Only add if page has text
                        text_content += f"\\n\\n--- Page {i + 1} ---\\n\\n"
                        text_content += page_text
                        
                except Exception as e:
                    logger.warning(f"OCR failed for page {i + 1}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
        
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        return text_content
    
    def validate_extracted_text(self, text: str) -> Dict[str, Any]:
        """Validate and analyze extracted text quality"""
        
        if not text or not text.strip():
            return {
                'is_valid': False,
                'reason': 'No text extracted',
                'character_count': 0,
                'word_count': 0,
                'confidence': 0.0
            }
        
        # Basic text analysis
        char_count = len(text)
        word_count = len(text.split())
        
        # Simple quality heuristics
        if char_count < 100:
            confidence = 0.2
            reason = 'Very little text extracted'
        elif word_count < 50:
            confidence = 0.4
            reason = 'Limited text content'
        elif char_count < 1000:
            confidence = 0.6
            reason = 'Moderate text extraction'
        else:
            confidence = 0.8
            reason = 'Good text extraction'
        
        return {
            'is_valid': char_count >= 100,
            'reason': reason,
            'character_count': char_count,
            'word_count': word_count,
            'confidence': confidence
        }

def trigger_ai_processing(book_id: str, text_content: str, parent_job_id: str = '') -> Optional[str]:
    """Trigger AI processing by sending a request to the backend job queue"""
    try:
        backend_url = os.getenv('BACKEND_URL', 'http://backend:8000')
        ai_queue_endpoint = f"{backend_url}/api/v1/jobs/ai/queue"
        
        # Prepare the AI processing job data
        ai_job_data = {
            'book_id': book_id,
            'text_content': text_content,
            'parent_job_id': parent_job_id,
            'source': 'ocr_service',
            'queued_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Triggering AI processing for book_id: {book_id}")
        
        # Send request to backend to queue AI job
        response = requests.post(
            ai_queue_endpoint,
            json=ai_job_data,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_job_id = result.get('job_id')
            logger.info(f"AI processing job queued successfully: {ai_job_id}")
            return ai_job_id
        else:
            logger.error(f"Failed to queue AI processing job: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error triggering AI processing: {e}")
        logger.error(traceback.format_exc())
        return None

def update_job_status_with_ai_info(ocr_job_id: str, ai_job_id: str, ocr_result: Dict[str, Any]):
    """Update OCR job status to include AI job information"""
    try:
        backend_url = os.getenv('BACKEND_URL', 'http://backend:8000')
        update_endpoint = f"{backend_url}/api/v1/jobs/{ocr_job_id}/ai-info"
        
        update_data = {
            'ai_job_id': ai_job_id,
            'ocr_completed': True,
            'ai_queued': True,
            'ocr_result': {
                'character_count': ocr_result.get('validation', {}).get('character_count', 0),
                'confidence': ocr_result.get('validation', {}).get('confidence', 0),
                'database_saved': ocr_result.get('database_saved', False)
            },
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = requests.patch(
            update_endpoint,
            json=update_data,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"Updated OCR job {ocr_job_id} with AI job info: {ai_job_id}")
        else:
            logger.warning(f"Failed to update OCR job status: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"Error updating OCR job status: {e}")

# RQ job function (called by the worker)

def process_pdf(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process PDF file for text extraction (RQ job function)"""
    
    logger.info(f"Starting OCR processing job: {job_data.get('parent_job_id')}")
    
    try:
        processor = OCRProcessor()
        
        file_path = job_data['file_path']
        book_id = job_data['book_id']
        book_metadata = job_data.get('book_metadata', {})
        title = book_metadata.get('title', 'Unknown Title')
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Extract text
        logger.info(f"Extracting text from: {file_path}")
        extracted_text = processor.extract_text_from_pdf(file_path, book_id)
        
        # Validate extraction
        validation = processor.validate_extracted_text(extracted_text)
        
        # Save results to database
        from database import save_book_ocr_results
        database_saved = save_book_ocr_results(
            book_id=book_id,
            title=title,
            file_path=file_path,
            text_content=extracted_text,
            confidence=validation['confidence'],
            character_count=validation['character_count']
        )
        
        result = {
            'status': 'completed',
            'book_id': book_id,
            'file_path': file_path,
            'text_content': extracted_text,
            'validation': validation,
            'database_saved': database_saved,
            'processed_at': datetime.utcnow().isoformat(),
            'next_stage': 'ai_processing'  # Indicate next stage
        }
        
        # Trigger AI processing if we have sufficient text content
        ai_job_id = None
        if validation['character_count'] > 50:  # Only process if we have reasonable text
            try:
                ai_job_id = trigger_ai_processing(book_id, extracted_text, job_data.get('parent_job_id', ''))
                if ai_job_id:
                    result['ai_job_id'] = ai_job_id
                    result['ai_status'] = 'queued'
                    logger.info(f"AI processing queued: job_id={ai_job_id}")
                else:
                    result['ai_status'] = 'failed_to_queue'
            except Exception as ai_error:
                logger.error(f"Failed to trigger AI processing: {ai_error}")
                result['ai_status'] = 'failed_to_queue'
                result['ai_error'] = str(ai_error)
        else:
            result['ai_status'] = 'skipped_insufficient_text'
            logger.info(f"Skipping AI processing: insufficient text content ({validation['character_count']} characters)")
        
        # Update job status with OCR completion and AI job info
        if ai_job_id:
            # Update the original OCR job to indicate AI processing has been queued
            update_job_status_with_ai_info(
                ocr_job_id=job_data.get('parent_job_id', ''),
                ai_job_id=ai_job_id,
                ocr_result=result
            )
        
        logger.info(f"OCR processing completed: {validation['character_count']} characters, confidence: {validation['confidence']}, database_saved: {database_saved}, ai_job_id: {ai_job_id}")
        return result
        
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        
        # Try to mark book as failed in database
        try:
            from database import get_database_connection, BookModel
            db = get_database_connection()
            db.create_tables()
            session = db.get_session()
            
            existing_book = session.query(BookModel).filter(BookModel.id == job_data.get('book_id')).first()
            if existing_book:
                existing_book.processing_status = 'failed'
                existing_book.updated_at = datetime.utcnow()
                session.commit()
            
            session.close()
            db.close()
        except Exception as db_error:
            logger.error(f"Failed to update database with error status: {db_error}")
        
        return {
            'status': 'failed',
            'book_id': job_data.get('book_id'),
            'error': str(e),
            'processed_at': datetime.utcnow().isoformat()
        }