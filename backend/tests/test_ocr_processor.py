"""
Unit tests for OCR Processing functionality
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from ocr_service.ocr_processor import OCRProcessor, process_pdf


class TestOCRProcessor:
    """Test OCRProcessor functionality"""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database components"""
        mock_engine = Mock()
        mock_session = Mock()
        return mock_engine, mock_session
    
    @pytest.fixture 
    def ocr_processor(self, mock_database):
        """OCRProcessor instance with mocked database"""
        with patch('ocr_service.ocr_processor.create_engine') as mock_create_engine:
            with patch('ocr_service.ocr_processor.sessionmaker') as mock_sessionmaker:
                mock_engine, mock_session = mock_database
                mock_create_engine.return_value = mock_engine
                mock_sessionmaker.return_value = Mock(return_value=mock_session)
                
                processor = OCRProcessor()
                return processor
    
    def test_init_successful(self, ocr_processor, mock_database):
        """Test successful OCR processor initialization"""
        mock_engine, mock_session = mock_database
        assert ocr_processor.db_engine == mock_engine
        assert ocr_processor.db_session == mock_session
    
    @patch.dict(os.environ, {"DATABASE_URL": "sqlite:///test.db"})
    def test_init_with_custom_db_url(self):
        """Test initialization with custom database URL"""
        with patch('ocr_service.ocr_processor.create_engine') as mock_create_engine:
            with patch('ocr_service.ocr_processor.sessionmaker'):
                OCRProcessor()
                mock_create_engine.assert_called_with("sqlite:///test.db")
    
    @patch('ocr_service.ocr_processor.fitz')
    def test_extract_with_pymupdf_success(self, mock_fitz, ocr_processor):
        """Test successful text extraction with PyMuPDF"""
        # Setup
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "This is extracted text from page 1"
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_fitz.open.return_value = mock_doc
        
        # Execute
        result = ocr_processor._extract_with_pymupdf("/test/file.pdf")
        
        # Assert
        assert "This is extracted text from page 1" in result
        assert "--- Page 1 ---" in result
        mock_fitz.open.assert_called_once_with("/test/file.pdf")
        mock_doc.close.assert_called_once()
    
    @patch('ocr_service.ocr_processor.fitz')
    def test_extract_with_pymupdf_empty_pages(self, mock_fitz, ocr_processor):
        """Test PyMuPDF extraction with empty pages"""
        # Setup
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "   \n\n   "  # Empty/whitespace only
        mock_doc.load_page.return_value = mock_page
        mock_doc.__len__.return_value = 1
        mock_fitz.open.return_value = mock_doc
        
        # Execute
        result = ocr_processor._extract_with_pymupdf("/test/file.pdf")
        
        # Assert
        assert result.strip() == ""  # Should be empty
    
    @patch('ocr_service.ocr_processor.fitz')
    def test_extract_with_pymupdf_error_handling(self, mock_fitz, ocr_processor):
        """Test PyMuPDF extraction error handling"""
        # Setup
        mock_fitz.open.side_effect = Exception("File not found")
        
        # Execute
        result = ocr_processor._extract_with_pymupdf("/nonexistent/file.pdf")
        
        # Assert
        assert result == ""
    
    @patch('ocr_service.ocr_processor.convert_from_path')
    @patch('ocr_service.ocr_processor.pytesseract.image_to_string')
    @patch('ocr_service.ocr_processor.tempfile.mkdtemp')
    @patch('ocr_service.ocr_processor.shutil.rmtree')
    def test_extract_with_ocr_success(self, mock_rmtree, mock_mkdtemp, mock_tesseract, mock_convert, ocr_processor):
        """Test successful OCR extraction"""
        # Setup
        mock_mkdtemp.return_value = "/tmp/test"
        mock_image = Mock()
        mock_convert.return_value = [mock_image, mock_image]  # 2 pages
        mock_tesseract.side_effect = ["Page 1 text", "Page 2 text"]
        
        # Execute
        result = ocr_processor._extract_with_ocr("/test/file.pdf")
        
        # Assert
        assert "Page 1 text" in result
        assert "Page 2 text" in result
        assert "--- Page 1 ---" in result
        assert "--- Page 2 ---" in result
        mock_convert.assert_called_once_with("/test/file.pdf", dpi=200, output_folder="/tmp/test", fmt='png')
        mock_rmtree.assert_called_once_with("/tmp/test", ignore_errors=True)
    
    @patch('ocr_service.ocr_processor.convert_from_path')
    @patch('ocr_service.ocr_processor.pytesseract.image_to_string')
    @patch('ocr_service.ocr_processor.tempfile.mkdtemp')
    @patch('ocr_service.ocr_processor.shutil.rmtree')
    def test_extract_with_ocr_tesseract_error(self, mock_rmtree, mock_mkdtemp, mock_tesseract, mock_convert, ocr_processor):
        """Test OCR extraction with Tesseract errors"""
        # Setup
        mock_mkdtemp.return_value = "/tmp/test"
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        mock_tesseract.side_effect = Exception("Tesseract failed")
        
        # Execute
        result = ocr_processor._extract_with_ocr("/test/file.pdf")
        
        # Assert - should handle error gracefully
        assert result == ""
        mock_rmtree.assert_called_once()
    
    def test_extract_text_from_pdf_pymupdf_success(self, ocr_processor):
        """Test PDF text extraction using PyMuPDF (sufficient text)"""
        # Setup
        ocr_processor._extract_with_pymupdf = Mock(return_value="A" * 200)  # Sufficient text
        ocr_processor._extract_with_ocr = Mock()
        
        # Execute
        result = ocr_processor.extract_text_from_pdf("/test/file.pdf", "book-123")
        
        # Assert
        assert len(result) == 200
        ocr_processor._extract_with_pymupdf.assert_called_once()
        ocr_processor._extract_with_ocr.assert_not_called()  # Should not fallback
    
    def test_extract_text_from_pdf_fallback_to_ocr(self, ocr_processor):
        """Test PDF text extraction falling back to OCR"""
        # Setup
        ocr_processor._extract_with_pymupdf = Mock(return_value="A" * 50)  # Insufficient text
        ocr_processor._extract_with_ocr = Mock(return_value="B" * 500)  # Good OCR result
        
        # Execute
        result = ocr_processor.extract_text_from_pdf("/test/file.pdf", "book-123")
        
        # Assert
        assert len(result) == 500
        assert result == "B" * 500
        ocr_processor._extract_with_pymupdf.assert_called_once()
        ocr_processor._extract_with_ocr.assert_called_once()
    
    def test_extract_text_from_pdf_all_methods_fail(self, ocr_processor):
        """Test PDF text extraction when all methods fail"""
        # Setup
        ocr_processor._extract_with_pymupdf = Mock(side_effect=Exception("PyMuPDF failed"))
        ocr_processor._extract_with_ocr = Mock(side_effect=Exception("OCR failed"))
        
        # Execute
        result = ocr_processor.extract_text_from_pdf("/test/file.pdf", "book-123")
        
        # Assert
        assert result == ""
    
    def test_validate_extracted_text_valid(self, ocr_processor):
        """Test text validation with valid text"""
        # Setup
        text = "This is a valid magic trick description " * 10  # 400+ characters
        
        # Execute
        validation = ocr_processor.validate_extracted_text(text)
        
        # Assert
        assert validation['is_valid'] is True
        assert validation['character_count'] > 100
        assert validation['word_count'] > 50
        assert validation['confidence'] >= 0.6
    
    def test_validate_extracted_text_insufficient(self, ocr_processor):
        """Test text validation with insufficient text"""
        # Setup
        text = "Short text"
        
        # Execute
        validation = ocr_processor.validate_extracted_text(text)
        
        # Assert
        assert validation['is_valid'] is False
        assert validation['reason'] == 'Very little text extracted'
        assert validation['confidence'] == 0.2
    
    def test_validate_extracted_text_empty(self, ocr_processor):
        """Test text validation with empty text"""
        # Execute
        validation = ocr_processor.validate_extracted_text("")
        
        # Assert
        assert validation['is_valid'] is False
        assert validation['reason'] == 'No text extracted'
        assert validation['character_count'] == 0
        assert validation['confidence'] == 0.0


class TestProcessPDFJobFunction:
    """Test the RQ job function process_pdf"""
    
    @patch('ocr_service.ocr_processor.OCRProcessor')
    def test_process_pdf_success(self, mock_processor_class):
        """Test successful PDF processing job"""
        # Setup
        mock_processor = Mock()
        mock_processor.extract_text_from_pdf.return_value = "Extracted text content"
        mock_processor.validate_extracted_text.return_value = {
            'is_valid': True,
            'character_count': 100,
            'confidence': 0.8
        }
        mock_processor_class.return_value = mock_processor
        
        job_data = {
            'file_path': '/test/file.pdf',
            'book_id': 'book-123'
        }
        
        # Execute
        result = process_pdf(job_data)
        
        # Assert
        assert result['status'] == 'completed'
        assert result['book_id'] == 'book-123'
        assert result['text_content'] == 'Extracted text content'
        assert 'validation' in result
        assert 'processed_at' in result
    
    @patch('ocr_service.ocr_processor.OCRProcessor')
    @patch('ocr_service.ocr_processor.os.path.exists')
    def test_process_pdf_file_not_found(self, mock_exists, mock_processor_class):
        """Test PDF processing with missing file"""
        # Setup
        mock_exists.return_value = False
        
        job_data = {
            'file_path': '/nonexistent/file.pdf',
            'book_id': 'book-123'
        }
        
        # Execute
        result = process_pdf(job_data)
        
        # Assert
        assert result['status'] == 'failed'
        assert 'PDF file not found' in result['error']
    
    @patch('ocr_service.ocr_processor.OCRProcessor')
    def test_process_pdf_extraction_failure(self, mock_processor_class):
        """Test PDF processing with extraction failure"""
        # Setup
        mock_processor = Mock()
        mock_processor.extract_text_from_pdf.side_effect = Exception("Extraction failed")
        mock_processor_class.return_value = mock_processor
        
        job_data = {
            'file_path': '/test/file.pdf',
            'book_id': 'book-123'
        }
        
        # Execute
        result = process_pdf(job_data)
        
        # Assert
        assert result['status'] == 'failed'
        assert 'Extraction failed' in result['error']
        assert 'processed_at' in result


class TestOCRProcessorIntegration:
    """Integration tests for OCR processor"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_pdf_processing(self, test_pdf_path):
        """Test processing a real PDF file"""
        with patch('ocr_service.ocr_processor.create_engine'):
            with patch('ocr_service.ocr_processor.sessionmaker'):
                processor = OCRProcessor()
                
                # Process the test PDF
                result = processor.extract_text_from_pdf(test_pdf_path, "test-book")
                
                # Assert
                assert len(result) > 0
                assert "MAGIC TRICK TEST" in result or "Vanishing Coin" in result
                
                # Validate the result
                validation = processor.validate_extracted_text(result)
                assert validation['is_valid'] is True