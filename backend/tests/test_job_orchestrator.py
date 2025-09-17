"""
Unit tests for Job Processing Orchestrator
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.infrastructure.jobs.orchestrator import JobOrchestrator, process_pdf_pipeline


class TestJobOrchestrator:
    """Test JobOrchestrator functionality"""
    
    @pytest.fixture
    def mock_job_queue(self):
        """Mock JobQueue"""
        mock = Mock()
        mock.enqueue_pdf_processing.return_value = "pipeline-job-123"
        return mock
    
    @pytest.fixture
    def orchestrator(self, mock_job_queue):
        """JobOrchestrator instance with mocked dependencies"""
        return JobOrchestrator(mock_job_queue)
    
    def test_create_pdf_processing_pipeline(self, orchestrator, mock_job_queue):
        """Test creating a PDF processing pipeline"""
        # Execute
        job_id = orchestrator.create_pdf_processing_pipeline(
            file_path="/test/file.pdf",
            book_id="book-123",
            original_filename="test.pdf",
            reprocess=False
        )
        
        # Assert
        assert job_id == "pipeline-job-123"
        mock_job_queue.enqueue_pdf_processing.assert_called_once_with(
            file_path="/test/file.pdf",
            book_id="book-123",
            original_filename="test.pdf",
            reprocess=False
        )
    
    def test_create_pdf_processing_pipeline_with_reprocess(self, orchestrator, mock_job_queue):
        """Test creating a PDF processing pipeline with reprocess flag"""
        # Execute
        job_id = orchestrator.create_pdf_processing_pipeline(
            file_path="/test/file.pdf",
            book_id="book-123", 
            original_filename="test.pdf",
            reprocess=True
        )
        
        # Assert
        assert job_id == "pipeline-job-123"
        
        # Check that reprocess flag was passed
        call_args = mock_job_queue.enqueue_pdf_processing.call_args
        assert call_args.kwargs['reprocess'] is True


class TestProcessPdfPipelineJobFunction:
    """Test the RQ job function process_pdf_pipeline"""
    
    @pytest.fixture
    def mock_job_queue(self):
        """Mock JobQueue for pipeline processing"""
        mock = Mock()
        
        # Mock OCR job
        mock.enqueue_ocr_processing.return_value = "ocr-job-123"
        mock._wait_for_job_completion.side_effect = [
            # OCR completion
            {
                'status': 'completed',
                'text_content': 'Extracted text from PDF with magic tricks',
                'validation': {'confidence': 0.8, 'character_count': 500}
            },
            # AI completion  
            {
                'status': 'completed',
                'tricks': [
                    {'name': 'Test Trick', 'effect_type': 'Card'},
                    {'name': 'Another Trick', 'effect_type': 'Coin'}
                ],
                'similarities': [
                    {'source_trick_idx': 0, 'target_trick_idx': 1, 'similarity_score': 0.75}
                ]
            }
        ]
        
        # Mock AI job
        mock.enqueue_ai_processing.return_value = "ai-job-456"
        
        return mock
    
    @patch('src.infrastructure.jobs.orchestrator.JobQueue')
    def test_process_pdf_pipeline_success(self, mock_job_queue_class, mock_job_queue):
        """Test successful PDF processing pipeline"""
        # Setup
        mock_job_queue_class.return_value = mock_job_queue
        
        job_data = {
            'file_path': '/test/file.pdf',
            'book_id': 'book-123',
            'original_filename': 'test.pdf',
            'reprocess': False,
            'job_id': 'pipeline-job-123'
        }
        
        # Execute
        result = process_pdf_pipeline(job_data)
        
        # Assert
        assert result['status'] == 'completed'
        assert result['book_id'] == 'book-123'
        assert result['file_path'] == '/test/file.pdf'
        assert result['original_filename'] == 'test.pdf'
        
        # Check OCR result
        assert 'ocr_result' in result
        assert result['ocr_result']['character_count'] == 500
        assert result['ocr_result']['confidence'] == 0.8
        
        # Check AI result
        assert 'ai_result' in result
        assert result['ai_result']['tricks_detected'] == 2
        assert result['ai_result']['similarities_found'] == 1
        
        # Check processing steps
        assert result['processing_steps'] == ['ocr', 'ai_processing', 'finalization']
        assert 'completed_at' in result
        
        # Verify job queue calls
        mock_job_queue.enqueue_ocr_processing.assert_called_once()
        mock_job_queue.enqueue_ai_processing.assert_called_once()
        assert mock_job_queue._wait_for_job_completion.call_count == 2
    
    @patch('src.infrastructure.jobs.orchestrator.JobQueue')
    def test_process_pdf_pipeline_ocr_failure(self, mock_job_queue_class, mock_job_queue):
        """Test PDF processing pipeline with OCR failure"""
        # Setup
        mock_job_queue_class.return_value = mock_job_queue
        mock_job_queue._wait_for_job_completion.return_value = {
            'status': 'failed',
            'error': 'OCR processing failed'
        }
        
        job_data = {
            'file_path': '/test/file.pdf',
            'book_id': 'book-123',
            'original_filename': 'test.pdf',
            'reprocess': False
        }
        
        # Execute
        result = process_pdf_pipeline(job_data)
        
        # Assert
        assert result['status'] == 'failed'
        assert 'OCR processing failed' in result['error']
        assert 'failed_at' in result
        
        # Should not proceed to AI processing
        mock_job_queue.enqueue_ai_processing.assert_not_called()
    
    @patch('src.infrastructure.jobs.orchestrator.JobQueue')
    def test_process_pdf_pipeline_insufficient_text(self, mock_job_queue_class, mock_job_queue):
        """Test PDF processing pipeline with insufficient OCR text"""
        # Setup
        mock_job_queue_class.return_value = mock_job_queue
        mock_job_queue._wait_for_job_completion.return_value = {
            'status': 'completed',
            'text_content': 'Short',  # Insufficient text
            'validation': {'confidence': 0.1, 'character_count': 5}
        }
        
        job_data = {
            'file_path': '/test/file.pdf',
            'book_id': 'book-123',
            'original_filename': 'test.pdf',
            'reprocess': False
        }
        
        # Execute
        result = process_pdf_pipeline(job_data)
        
        # Assert
        assert result['status'] == 'failed'
        assert 'insufficient text content' in result['error']
    
    @patch('src.infrastructure.jobs.orchestrator.JobQueue')
    def test_process_pdf_pipeline_ai_failure(self, mock_job_queue_class, mock_job_queue):
        """Test PDF processing pipeline with AI failure"""
        # Setup
        mock_job_queue_class.return_value = mock_job_queue
        mock_job_queue._wait_for_job_completion.side_effect = [
            # OCR success
            {
                'status': 'completed',
                'text_content': 'Sufficient text content for processing',
                'validation': {'confidence': 0.8, 'character_count': 500}
            },
            # AI failure
            {
                'status': 'failed',
                'error': 'AI model failed to load'
            }
        ]
        
        job_data = {
            'file_path': '/test/file.pdf',
            'book_id': 'book-123',
            'original_filename': 'test.pdf',
            'reprocess': False
        }
        
        # Execute
        result = process_pdf_pipeline(job_data)
        
        # Assert
        assert result['status'] == 'failed'
        assert 'AI processing failed' in result['error']
        
        # Should have called both OCR and AI
        mock_job_queue.enqueue_ocr_processing.assert_called_once()
        mock_job_queue.enqueue_ai_processing.assert_called_once()
    
    @patch('src.infrastructure.jobs.orchestrator.JobQueue')
    def test_process_pdf_pipeline_timeout_handling(self, mock_job_queue_class, mock_job_queue):
        """Test PDF processing pipeline with timeout"""
        # Setup
        mock_job_queue_class.return_value = mock_job_queue
        mock_job_queue._wait_for_job_completion.side_effect = Exception("Job did not complete within 1800 seconds")
        
        job_data = {
            'file_path': '/test/file.pdf',
            'book_id': 'book-123',
            'original_filename': 'test.pdf',
            'reprocess': False
        }
        
        # Execute
        result = process_pdf_pipeline(job_data)
        
        # Assert
        assert result['status'] == 'failed'
        assert 'Job did not complete within 1800 seconds' in result['error']
    
    @patch('src.infrastructure.jobs.orchestrator.JobQueue')
    def test_process_pdf_pipeline_with_parent_job_id(self, mock_job_queue_class, mock_job_queue):
        """Test PDF processing pipeline with parent job ID tracking"""
        # Setup
        mock_job_queue_class.return_value = mock_job_queue
        mock_job_queue._wait_for_job_completion.side_effect = [
            {
                'status': 'completed',
                'text_content': 'Test content',
                'validation': {'confidence': 0.8, 'character_count': 200}
            },
            {
                'status': 'completed', 
                'tricks': [],
                'similarities': []
            }
        ]
        
        job_data = {
            'file_path': '/test/file.pdf',
            'book_id': 'book-123',
            'original_filename': 'test.pdf',
            'reprocess': False,
            'job_id': 'parent-job-789'
        }
        
        # Execute
        result = process_pdf_pipeline(job_data)
        
        # Assert
        assert result['status'] == 'completed'
        
        # Check that parent job ID was passed to child jobs
        ocr_call_args = mock_job_queue.enqueue_ocr_processing.call_args[1]
        assert ocr_call_args['parent_job_id'] == 'parent-job-789'
        
        ai_call_args = mock_job_queue.enqueue_ai_processing.call_args[1]
        assert ai_call_args['parent_job_id'] == 'parent-job-789'


class TestJobOrchestratorIntegration:
    """Integration tests for job orchestrator"""
    
    @pytest.mark.integration
    def test_orchestrator_with_real_job_queue(self, mock_job_queue):
        """Test orchestrator with actual job queue (mocked Redis)"""
        orchestrator = JobOrchestrator(mock_job_queue)
        
        # Test pipeline creation
        job_id = orchestrator.create_pdf_processing_pipeline(
            file_path="/integration/test.pdf",
            book_id="integration-book",
            original_filename="integration.pdf"
        )
        
        assert job_id is not None
        mock_job_queue.enqueue_pdf_processing.assert_called_once()