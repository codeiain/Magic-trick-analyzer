"""
Unit tests for OCR Processor

Tests the OCR processing functionality including text extraction,
validation, and job processing functions.
"""

import pytest
import tempfile
import shutil
import os
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
from datetime import datetime

from ocr_processor import OCRProcessor, process_pdf


class TestOCRProcessor:
    """Test cases for OCRProcessor class"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def mock_db_engine(self):
        """Mock database engine"""
        return Mock()

    @pytest.fixture
    def ocr_processor(self, mock_db_session, mock_db_engine):
        """Create OCR processor with mocked dependencies"""
        with patch('ocr_processor.create_engine', return_value=mock_db_engine), \
             patch('ocr_processor.sessionmaker') as mock_session_maker:
            
            mock_session_maker.return_value.return_value = mock_db_session
            processor = OCRProcessor()
            return processor

    @pytest.fixture
    def sample_pdf_path(self):
        """Create a sample PDF file for testing"""
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        pdf_path = os.path.join(temp_dir, "test.pdf")
        
        # Create a simple PDF-like file (just for path testing)
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\ntest pdf content')
        
        yield pdf_path
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_initialization_success(self, mock_db_session, mock_db_engine):
        """Test successful OCR processor initialization"""
        with patch('ocr_processor.create_engine', return_value=mock_db_engine), \
             patch('ocr_processor.sessionmaker') as mock_session_maker, \
             patch.dict(os.environ, {'DATABASE_URL': 'sqlite:///test.db'}):
            
            mock_session_maker.return_value.return_value = mock_db_session
            
            processor = OCRProcessor()
            
            assert processor.db_engine == mock_db_engine
            assert processor.db_session == mock_db_session

    def test_initialization_failure(self):
        """Test OCR processor initialization failure"""
        with patch('ocr_processor.create_engine', side_effect=Exception("DB connection failed")):
            with pytest.raises(Exception, match="DB connection failed"):
                OCRProcessor()

    @patch('ocr_processor.fitz')
    def test_extract_with_pymupdf_success(self, mock_fitz, ocr_processor, sample_pdf_path):
        """Test successful text extraction with PyMuPDF"""
        # Mock PyMuPDF document and pages
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "This is extracted text from page 1"
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_fitz.open.return_value = mock_doc

        result = ocr_processor._extract_with_pymupdf(sample_pdf_path)

        assert "This is extracted text from page 1" in result
        assert "--- Page 1 ---" in result
        mock_fitz.open.assert_called_once_with(sample_pdf_path)
        mock_doc.close.assert_called_once()

    @patch('ocr_processor.fitz')
    def test_extract_with_pymupdf_empty_pages(self, mock_fitz, ocr_processor, sample_pdf_path):
        """Test PyMuPDF extraction with empty pages"""
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "   "  # Empty/whitespace only
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_fitz.open.return_value = mock_doc

        result = ocr_processor._extract_with_pymupdf(sample_pdf_path)

        assert result == ""
        mock_doc.close.assert_called_once()

    @patch('ocr_processor.fitz')
    def test_extract_with_pymupdf_error(self, mock_fitz, ocr_processor, sample_pdf_path):
        """Test PyMuPDF extraction error handling"""
        mock_fitz.open.side_effect = Exception("PyMuPDF error")

        result = ocr_processor._extract_with_pymupdf(sample_pdf_path)

        assert result == ""

    @patch('ocr_processor.shutil.rmtree')
    @patch('ocr_processor.pytesseract.image_to_string')
    @patch('ocr_processor.convert_from_path')
    @patch('ocr_processor.tempfile.mkdtemp')
    def test_extract_with_ocr_success(self, mock_mkdtemp, mock_convert, 
                                     mock_tesseract, mock_rmtree, 
                                     ocr_processor, sample_pdf_path):
        """Test successful OCR extraction"""
        # Mock temporary directory
        temp_dir = "/tmp/test_ocr"
        mock_mkdtemp.return_value = temp_dir

        # Mock PDF to image conversion
        mock_image = Mock()
        mock_convert.return_value = [mock_image, mock_image]  # 2 pages

        # Mock Tesseract OCR
        mock_tesseract.side_effect = [
            "Text from page 1",
            "Text from page 2"
        ]

        result = ocr_processor._extract_with_ocr(sample_pdf_path)

        assert "Text from page 1" in result
        assert "Text from page 2" in result
        assert "--- Page 1 ---" in result
        assert "--- Page 2 ---" in result
        
        mock_convert.assert_called_once_with(
            sample_pdf_path,
            dpi=200,
            output_folder=temp_dir,
            fmt='png'
        )
        assert mock_tesseract.call_count == 2
        mock_rmtree.assert_called_once_with(temp_dir, ignore_errors=True)

    @patch('ocr_processor.shutil.rmtree')
    @patch('ocr_processor.pytesseract.image_to_string')
    @patch('ocr_processor.convert_from_path')
    @patch('ocr_processor.tempfile.mkdtemp')
    def test_extract_with_ocr_tesseract_error(self, mock_mkdtemp, mock_convert,
                                             mock_tesseract, mock_rmtree,
                                             ocr_processor, sample_pdf_path):
        """Test OCR extraction with Tesseract errors"""
        temp_dir = "/tmp/test_ocr"
        mock_mkdtemp.return_value = temp_dir
        
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        mock_tesseract.side_effect = Exception("Tesseract error")

        result = ocr_processor._extract_with_ocr(sample_pdf_path)

        # Should return empty string but not crash
        assert result == ""
        mock_rmtree.assert_called_once()

    @patch('ocr_processor.convert_from_path')
    @patch('ocr_processor.tempfile.mkdtemp')
    def test_extract_with_ocr_convert_error(self, mock_mkdtemp, mock_convert,
                                          ocr_processor, sample_pdf_path):
        """Test OCR extraction with PDF conversion error"""
        mock_mkdtemp.return_value = "/tmp/test"
        mock_convert.side_effect = Exception("Conversion error")

        result = ocr_processor._extract_with_ocr(sample_pdf_path)

        assert result == ""

    def test_extract_text_from_pdf_pymupdf_success(self, ocr_processor, sample_pdf_path):
        """Test main extraction method with PyMuPDF success"""
        with patch.object(ocr_processor, '_extract_with_pymupdf', return_value="Long text content from PyMuPDF" * 10):
            result = ocr_processor.extract_text_from_pdf(sample_pdf_path, "book_123")
            
            assert "Long text content from PyMuPDF" in result
            assert len(result) > 100

    def test_extract_text_from_pdf_fallback_to_ocr(self, ocr_processor, sample_pdf_path):
        """Test main extraction method falling back to OCR"""
        with patch.object(ocr_processor, '_extract_with_pymupdf', return_value="Short"), \
             patch.object(ocr_processor, '_extract_with_ocr', return_value="Long OCR extracted text content" * 10):
            
            result = ocr_processor.extract_text_from_pdf(sample_pdf_path, "book_123")
            
            assert "Long OCR extracted text content" in result

    def test_extract_text_from_pdf_both_fail(self, ocr_processor, sample_pdf_path):
        """Test main extraction method when both methods fail"""
        with patch.object(ocr_processor, '_extract_with_pymupdf', side_effect=Exception("PyMuPDF failed")), \
             patch.object(ocr_processor, '_extract_with_ocr', side_effect=Exception("OCR failed")):
            
            result = ocr_processor.extract_text_from_pdf(sample_pdf_path, "book_123")
            
            assert result == ""

    def test_validate_extracted_text_empty(self, ocr_processor):
        """Test text validation with empty text"""
        result = ocr_processor.validate_extracted_text("")
        
        assert result['is_valid'] is False
        assert result['reason'] == 'No text extracted'
        assert result['character_count'] == 0
        assert result['word_count'] == 0
        assert result['confidence'] == 0.0

    def test_validate_extracted_text_none(self, ocr_processor):
        """Test text validation with None text"""
        result = ocr_processor.validate_extracted_text(None)
        
        assert result['is_valid'] is False
        assert result['character_count'] == 0

    def test_validate_extracted_text_very_short(self, ocr_processor):
        """Test text validation with very short text"""
        short_text = "Short text"
        result = ocr_processor.validate_extracted_text(short_text)
        
        assert result['is_valid'] is False
        assert result['reason'] == 'Very little text extracted'
        assert result['character_count'] == len(short_text)
        assert result['confidence'] == 0.2

    def test_validate_extracted_text_limited_words(self, ocr_processor):
        """Test text validation with limited words"""
        limited_text = "This is a text with exactly twenty-five words to test the validation logic for limited text content detection and confidence scoring in our system."
        result = ocr_processor.validate_extracted_text(limited_text)
        
        assert result['is_valid'] is False
        assert result['reason'] == 'Limited text content'
        assert result['confidence'] == 0.4

    def test_validate_extracted_text_moderate(self, ocr_processor):
        """Test text validation with moderate text"""
        moderate_text = "This is a moderate length text. " * 20  # ~600 characters
        result = ocr_processor.validate_extracted_text(moderate_text)
        
        assert result['is_valid'] is True
        assert result['reason'] == 'Moderate text extraction'
        assert result['confidence'] == 0.6

    def test_validate_extracted_text_good(self, ocr_processor):
        """Test text validation with good text"""
        good_text = "This is a good length text. " * 50  # ~1400 characters
        result = ocr_processor.validate_extracted_text(good_text)
        
        assert result['is_valid'] is True
        assert result['reason'] == 'Good text extraction'
        assert result['confidence'] == 0.8


class TestProcessPdfJob:
    """Test cases for the process_pdf RQ job function"""

    @pytest.fixture
    def job_data(self, tmp_path):
        """Sample job data for testing"""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b'%PDF-1.4\ntest content')
        
        return {
            'file_path': str(test_file),
            'book_id': 'book_123',
            'parent_job_id': 'job_456'
        }

    def test_process_pdf_success(self, job_data):
        """Test successful PDF processing job"""
        mock_processor = Mock()
        mock_processor.extract_text_from_pdf.return_value = "Extracted text content"
        mock_processor.validate_extracted_text.return_value = {
            'is_valid': True,
            'character_count': 100,
            'word_count': 20,
            'confidence': 0.8,
            'reason': 'Good extraction'
        }

        with patch('ocr_processor.OCRProcessor', return_value=mock_processor):
            result = process_pdf(job_data)

        assert result['status'] == 'completed'
        assert result['book_id'] == 'book_123'
        assert result['file_path'] == job_data['file_path']
        assert result['text_content'] == "Extracted text content"
        assert result['validation']['confidence'] == 0.8
        assert 'processed_at' in result

    def test_process_pdf_file_not_found(self, job_data):
        """Test PDF processing with missing file"""
        job_data['file_path'] = '/nonexistent/file.pdf'

        result = process_pdf(job_data)

        assert result['status'] == 'failed'
        assert 'not found' in result['error'].lower()
        assert 'processed_at' in result

    def test_process_pdf_extraction_error(self, job_data):
        """Test PDF processing with extraction error"""
        mock_processor = Mock()
        mock_processor.extract_text_from_pdf.side_effect = Exception("Extraction failed")

        with patch('ocr_processor.OCRProcessor', return_value=mock_processor):
            result = process_pdf(job_data)

        assert result['status'] == 'failed'
        assert 'Extraction failed' in result['error']
        assert 'processed_at' in result

    def test_process_pdf_processor_init_error(self, job_data):
        """Test PDF processing with processor initialization error"""
        with patch('ocr_processor.OCRProcessor', side_effect=Exception("Init failed")):
            result = process_pdf(job_data)

        assert result['status'] == 'failed'
        assert 'Init failed' in result['error']

    def test_process_pdf_validation_included(self, job_data):
        """Test that PDF processing includes validation results"""
        mock_processor = Mock()
        mock_processor.extract_text_from_pdf.return_value = "Test content"
        validation_result = {
            'is_valid': False,
            'character_count': 12,
            'word_count': 2,
            'confidence': 0.2,
            'reason': 'Very little text extracted'
        }
        mock_processor.validate_extracted_text.return_value = validation_result

        with patch('ocr_processor.OCRProcessor', return_value=mock_processor):
            result = process_pdf(job_data)

        assert result['status'] == 'completed'
        assert result['validation'] == validation_result

    @patch('ocr_processor.datetime')
    def test_process_pdf_timestamp(self, mock_datetime, job_data):
        """Test that PDF processing includes correct timestamp"""
        fixed_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = fixed_time

        mock_processor = Mock()
        mock_processor.extract_text_from_pdf.return_value = "Content"
        mock_processor.validate_extracted_text.return_value = {'is_valid': True, 'confidence': 0.8}

        with patch('ocr_processor.OCRProcessor', return_value=mock_processor):
            result = process_pdf(job_data)

        assert result['processed_at'] == fixed_time.isoformat()


class TestOCRProcessorIntegration:
    """Integration tests for OCR processor with real-like scenarios"""

    @pytest.fixture
    def ocr_processor(self):
        """Create OCR processor with mocked external dependencies"""
        with patch('ocr_processor.create_engine'), \
             patch('ocr_processor.sessionmaker'):
            return OCRProcessor()

    def test_full_extraction_pipeline_pymupdf_path(self, ocr_processor):
        """Test complete extraction pipeline using PyMuPDF path"""
        with patch.object(ocr_processor, '_extract_with_pymupdf', return_value="A comprehensive magic book content with detailed explanations of various tricks and techniques used by professional magicians around the world."), \
             patch.object(ocr_processor, '_extract_with_ocr') as mock_ocr:
            
            result = ocr_processor.extract_text_from_pdf("test.pdf", "book_123")
            
            # Should use PyMuPDF and not fall back to OCR
            assert len(result) > 100
            assert "magic book content" in result
            mock_ocr.assert_not_called()

    def test_full_extraction_pipeline_ocr_fallback(self, ocr_processor):
        """Test complete extraction pipeline falling back to OCR"""
        with patch.object(ocr_processor, '_extract_with_pymupdf', return_value="Short"), \
             patch.object(ocr_processor, '_extract_with_ocr', return_value="This is a much longer text extracted via OCR from an image-based PDF containing detailed magic trick instructions and methodologies."):
            
            result = ocr_processor.extract_text_from_pdf("test.pdf", "book_123")
            
            # Should fall back to OCR
            assert "OCR from an image-based PDF" in result
            assert len(result) > 100

    def test_extraction_with_validation_pipeline(self, ocr_processor):
        """Test extraction followed by validation"""
        extracted_text = "This is extracted text from a magic book. " * 20
        
        with patch.object(ocr_processor, '_extract_with_pymupdf', return_value=extracted_text):
            result = ocr_processor.extract_text_from_pdf("test.pdf", "book_123")
            validation = ocr_processor.validate_extracted_text(result)
            
            assert validation['is_valid'] is True
            assert validation['confidence'] > 0.6
            assert validation['character_count'] > 500


# Test fixtures and utilities
@pytest.fixture
def temp_pdf_file():
    """Create a temporary PDF file for testing"""
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "test_magic_book.pdf")
    
    # Create a mock PDF file
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n')
    
    yield pdf_path
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__])