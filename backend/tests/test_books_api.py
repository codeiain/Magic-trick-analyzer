"""
Unit tests for Books API Router
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
import io

from src.presentation.api.routers.books import create_router


class TestBooksRouter:
    """Test Books API router functionality"""
    
    @pytest.fixture
    def mock_process_books_use_case(self):
        """Mock ProcessBooksUseCase"""
        return AsyncMock()
    
    @pytest.fixture  
    def mock_book_repository(self):
        """Mock BookRepository"""
        mock = AsyncMock()
        
        # Sample book data
        mock_book = Mock()
        mock_book.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_book.title = "Test Magic Book"
        mock_book.author = "Test Author"
        mock_book.file_path = "/test/path.pdf"
        
        mock.get_all.return_value = [mock_book]
        mock.find_by_id.return_value = mock_book
        
        return mock
    
    @pytest.fixture
    def mock_statistics_use_case(self):
        """Mock statistics use case"""
        return AsyncMock()
    
    @pytest.fixture
    def app(self, mock_process_books_use_case, mock_book_repository, mock_statistics_use_case):
        """FastAPI test app with books router"""
        app = FastAPI()
        
        router = create_router(
            mock_process_books_use_case,
            mock_book_repository, 
            mock_statistics_use_case
        )
        app.include_router(router, prefix="/api/v1/books")
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Test client"""
        return TestClient(app)
    
    def test_get_all_books_success(self, client, mock_book_repository):
        """Test getting all books successfully"""
        # Execute
        response = client.get("/api/v1/books/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        book = data[0]
        assert book['id'] == "550e8400-e29b-41d4-a716-446655440000"
        assert book['title'] == "Test Magic Book"
        assert book['author'] == "Test Author"
        
        mock_book_repository.get_all.assert_called_once()
    
    def test_get_all_books_error(self, client, mock_book_repository):
        """Test getting all books with error"""
        # Setup
        mock_book_repository.get_all.side_effect = Exception("Database error")
        
        # Execute
        response = client.get("/api/v1/books/")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Error retrieving books" in data['detail']
    
    def test_get_book_by_id_success(self, client, mock_book_repository):
        """Test getting book by ID successfully"""
        # Execute
        response = client.get("/api/v1/books/550e8400-e29b-41d4-a716-446655440000")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data['id'] == "550e8400-e29b-41d4-a716-446655440000"
        assert data['title'] == "Test Magic Book"
    
    def test_get_book_by_id_not_found(self, client, mock_book_repository):
        """Test getting non-existent book"""
        # Setup
        mock_book_repository.find_by_id.return_value = None
        
        # Execute
        response = client.get("/api/v1/books/nonexistent-id")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Book not found" in data['detail']
    
    def test_get_book_by_id_invalid_uuid(self, client):
        """Test getting book with invalid UUID"""
        # Execute
        response = client.get("/api/v1/books/invalid-uuid")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid book ID format" in data['detail']
    
    def test_upload_pdf_success(self, client):
        """Test successful PDF upload"""
        # Create a mock PDF file
        pdf_content = b"Mock PDF content"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        with patch('src.infrastructure.queue.job_queue.JobQueue') as mock_job_queue_class:
            mock_job_queue = Mock()
            mock_job_queue.enqueue_pdf_processing.return_value = "test-job-123"
            mock_job_queue_class.return_value = mock_job_queue
            
            with patch('os.makedirs'):  # Mock directory creation
                with patch('builtins.open', create=True) as mock_open:
                    # Execute
                    response = client.post("/api/v1/books/upload", files=files)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'queued'
        assert data['job_id'] == 'test-job-123'
        assert 'queued for processing' in data['message']
    
    def test_upload_pdf_invalid_file_type(self, client):
        """Test upload with non-PDF file"""
        # Create a mock text file
        files = {"file": ("test.txt", io.BytesIO(b"Text content"), "text/plain")}
        
        # Execute
        response = client.post("/api/v1/books/upload", files=files)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Only PDF files are supported" in data['detail']
    
    def test_upload_pdf_with_reprocess_flag(self, client):
        """Test PDF upload with reprocess flag"""
        pdf_content = b"Mock PDF content"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        with patch('src.infrastructure.queue.job_queue.JobQueue') as mock_job_queue_class:
            mock_job_queue = Mock()
            mock_job_queue.enqueue_pdf_processing.return_value = "reprocess-job-456"
            mock_job_queue_class.return_value = mock_job_queue
            
            with patch('os.makedirs'):
                with patch('builtins.open', create=True):
                    # Execute
                    response = client.post("/api/v1/books/upload?reprocess=true", files=files)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data['job_id'] == 'reprocess-job-456'
        
        # Check that reprocess flag was passed
        call_args = mock_job_queue.enqueue_pdf_processing.call_args
        assert call_args.kwargs['reprocess'] is True
    
    def test_upload_pdf_job_queue_error(self, client):
        """Test PDF upload with job queue error"""
        pdf_content = b"Mock PDF content"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        with patch('src.infrastructure.queue.job_queue.JobQueue') as mock_job_queue_class:
            mock_job_queue_class.side_effect = Exception("Redis connection failed")
            
            # Execute
            response = client.post("/api/v1/books/upload", files=files)
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Error processing upload" in data['detail']
    
    def test_reprocess_book_success(self, client, mock_book_repository):
        """Test book reprocessing information"""
        # Execute
        response = client.get("/api/v1/books/550e8400-e29b-41d4-a716-446655440000/reprocess")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data['status'] == 'info'
        assert 'reprocess' in data['message']
        assert 'upload endpoint' in data['message']
        assert data['book_id'] == '550e8400-e29b-41d4-a716-446655440000'
        assert 'upload_endpoint' in data
    
    def test_reprocess_book_not_found(self, client, mock_book_repository):
        """Test reprocessing non-existent book"""
        # Setup
        mock_book_repository.find_by_id.return_value = None
        
        # Execute
        response = client.get("/api/v1/books/550e8400-e29b-41d4-a716-446655440000/reprocess")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Book not found" in data['detail']
    
    def test_reprocess_book_invalid_uuid(self, client):
        """Test reprocessing with invalid UUID"""
        # Execute
        response = client.get("/api/v1/books/invalid-uuid/reprocess")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid book ID format" in data['detail']


class TestBooksRouterIntegration:
    """Integration tests for books router"""
    
    @pytest.mark.integration
    def test_full_upload_workflow(self, temp_dir):
        """Test complete upload workflow with mocked dependencies"""
        from src.presentation.api.routers.books import create_router
        
        # Create mocks
        mock_use_case = AsyncMock()
        mock_repository = AsyncMock()
        mock_stats = AsyncMock()
        
        # Create router and app
        router = create_router(mock_use_case, mock_repository, mock_stats)
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/books")
        client = TestClient(app)
        
        # Create test file
        pdf_content = b"%PDF-1.4 Mock PDF content"
        files = {"file": ("integration.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        with patch('src.infrastructure.queue.job_queue.JobQueue') as mock_job_queue_class:
            mock_job_queue = Mock()
            mock_job_queue.enqueue_pdf_processing.return_value = "integration-job"
            mock_job_queue_class.return_value = mock_job_queue
            
            with patch('os.makedirs'):
                with patch('builtins.open', create=True):
                    response = client.post("/api/v1/books/upload", files=files)
        
        # Assert workflow completed
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'queued'
        assert data['job_id'] == 'integration-job'


class TestProcessingStatusSchema:
    """Test ProcessingStatusSchema updates"""
    
    def test_processing_status_schema_with_job_id(self):
        """Test ProcessingStatusSchema includes job_id"""
        from src.presentation.api.routers.schemas import ProcessingStatusSchema
        
        data = {
            'status': 'queued',
            'message': 'Job queued successfully',
            'job_id': 'test-job-123',
            'file_path': '/app/temp/test.pdf'
        }
        
        # Execute
        schema = ProcessingStatusSchema(**data)
        
        # Assert
        assert schema.status == 'queued'
        assert schema.job_id == 'test-job-123'
        assert schema.file_path == '/app/temp/test.pdf'
    
    def test_processing_status_schema_minimal(self):
        """Test ProcessingStatusSchema with minimal data"""
        from src.presentation.api.routers.schemas import ProcessingStatusSchema
        
        data = {
            'status': 'processing',
            'message': 'Processing started'
        }
        
        # Execute
        schema = ProcessingStatusSchema(**data)
        
        # Assert
        assert schema.status == 'processing'
        assert schema.message == 'Processing started'
        assert schema.job_id is None
        assert schema.file_path is None