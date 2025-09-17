"""
Unit tests for Jobs API Router
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.presentation.api.routers.jobs import router, initialize_job_queue


class TestJobsRouter:
    """Test Jobs API router functionality"""
    
    @pytest.fixture
    def mock_job_queue(self):
        """Mock JobQueue for testing"""
        mock = Mock()
        
        # Default mock responses
        mock.get_job_status.return_value = {
            'job_id': 'test-job-123',
            'status': 'completed',
            'progress': 100,
            'message': 'Job completed successfully',
            'result': {'data': 'test_result'},
            'error': None,
            'created_at': '2025-09-17T12:00:00Z',
            'started_at': '2025-09-17T12:01:00Z',
            'finished_at': '2025-09-17T12:05:00Z'
        }
        
        mock.cancel_job.return_value = True
        mock.list_jobs.return_value = [
            {
                'job_id': 'job-1',
                'status': 'completed',
                'created_at': '2025-09-17T12:00:00Z'
            },
            {
                'job_id': 'job-2', 
                'status': 'queued',
                'created_at': '2025-09-17T12:01:00Z'
            }
        ]
        mock.cleanup_completed_jobs.return_value = 5
        
        return mock
    
    @pytest.fixture
    def app(self, mock_job_queue):
        """FastAPI test app with jobs router"""
        app = FastAPI()
        
        # Initialize the job queue in the router
        initialize_job_queue(mock_job_queue)
        app.include_router(router, prefix="/api/v1")
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Test client"""
        return TestClient(app)
    
    def test_get_job_status_success(self, client, mock_job_queue):
        """Test getting job status successfully"""
        # Execute
        response = client.get("/api/v1/jobs/test-job-123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data['job_id'] == 'test-job-123'
        assert data['status'] == 'completed'
        assert data['progress'] == 100
        assert data['message'] == 'Job completed successfully'
        assert data['result'] == {'data': 'test_result'}
        
        mock_job_queue.get_job_status.assert_called_once_with('test-job-123')
    
    def test_get_job_status_not_found(self, client, mock_job_queue):
        """Test getting status for non-existent job"""
        # Setup
        mock_job_queue.get_job_status.return_value = None
        
        # Execute
        response = client.get("/api/v1/jobs/nonexistent-job")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Job not found" in data['detail']
    
    def test_get_job_status_error(self, client, mock_job_queue):
        """Test getting job status with error"""
        # Setup
        mock_job_queue.get_job_status.side_effect = Exception("Database error")
        
        # Execute
        response = client.get("/api/v1/jobs/test-job-123")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Error retrieving job status" in data['detail']
    
    def test_cancel_job_success(self, client, mock_job_queue):
        """Test cancelling job successfully"""
        # Execute
        response = client.delete("/api/v1/jobs/test-job-123")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "cancelled successfully" in data['message']
        
        mock_job_queue.cancel_job.assert_called_once_with('test-job-123')
    
    def test_cancel_job_not_found(self, client, mock_job_queue):
        """Test cancelling non-existent job"""
        # Setup
        mock_job_queue.cancel_job.return_value = False
        
        # Execute
        response = client.delete("/api/v1/jobs/nonexistent-job")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Job not found" in data['detail']
    
    def test_cancel_job_error(self, client, mock_job_queue):
        """Test cancelling job with error"""
        # Setup
        mock_job_queue.cancel_job.side_effect = Exception("Redis error")
        
        # Execute
        response = client.delete("/api/v1/jobs/test-job-123")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Error cancelling job" in data['detail']
    
    def test_list_jobs_success(self, client, mock_job_queue):
        """Test listing jobs successfully"""
        # Execute
        response = client.get("/api/v1/jobs/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert len(data['jobs']) == 2
        assert data['total'] == 2
        
        # Check job structure
        job = data['jobs'][0]
        assert 'job_id' in job
        assert 'status' in job
        assert 'created_at' in job
        
        mock_job_queue.list_jobs.assert_called_once_with(status_filter=None, limit=50)
    
    def test_list_jobs_with_filters(self, client, mock_job_queue):
        """Test listing jobs with status filter"""
        # Execute
        response = client.get("/api/v1/jobs/?status=completed&limit=10")
        
        # Assert
        assert response.status_code == 200
        mock_job_queue.list_jobs.assert_called_once_with(status_filter="completed", limit=10)
    
    def test_list_jobs_error(self, client, mock_job_queue):
        """Test listing jobs with error"""
        # Setup
        mock_job_queue.list_jobs.side_effect = Exception("Redis connection failed")
        
        # Execute
        response = client.get("/api/v1/jobs/")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Error listing jobs" in data['detail']
    
    def test_cleanup_completed_jobs_success(self, client, mock_job_queue):
        """Test cleaning up completed jobs"""
        # Execute
        response = client.delete("/api/v1/jobs/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Cleaned up 5 completed jobs" in data['message']
        
        mock_job_queue.cleanup_completed_jobs.assert_called_once()
    
    def test_cleanup_completed_jobs_error(self, client, mock_job_queue):
        """Test cleanup with error"""
        # Setup
        mock_job_queue.cleanup_completed_jobs.side_effect = Exception("Cleanup failed")
        
        # Execute
        response = client.delete("/api/v1/jobs/")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Error cleaning up jobs" in data['detail']


class TestJobsRouterDependencyInjection:
    """Test job queue dependency injection"""
    
    def test_initialize_job_queue(self):
        """Test job queue initialization"""
        mock_queue = Mock()
        
        # Execute
        initialize_job_queue(mock_queue)
        
        # Assert - should not raise an error
        # The actual assertion would be tested in integration with a real app
    
    def test_get_job_queue_uninitialized(self):
        """Test getting job queue when uninitialized"""
        # Reset global state
        from src.presentation.api.routers.jobs import job_queue
        original_queue = job_queue
        
        # Temporarily set to None
        import src.presentation.api.routers.jobs as jobs_module
        jobs_module.job_queue = None
        
        try:
            app = FastAPI()
            app.include_router(router, prefix="/api/v1")
            client = TestClient(app)
            
            # Execute
            response = client.get("/api/v1/jobs/test-job")
            
            # Assert
            assert response.status_code == 500
            data = response.json()
            assert "Job queue not initialized" in data['detail']
            
        finally:
            # Restore original state
            jobs_module.job_queue = original_queue


class TestJobStatusResponseModel:
    """Test Pydantic models for job responses"""
    
    def test_job_status_response_complete(self):
        """Test JobStatusResponse with complete data"""
        from src.presentation.api.routers.jobs import JobStatusResponse
        
        data = {
            'job_id': 'test-job-123',
            'status': 'completed',
            'progress': 100,
            'message': 'Job completed',
            'result': {'data': 'result'},
            'error': None,
            'created_at': '2025-09-17T12:00:00Z',
            'started_at': '2025-09-17T12:01:00Z',
            'finished_at': '2025-09-17T12:05:00Z'
        }
        
        # Execute
        response = JobStatusResponse(**data)
        
        # Assert
        assert response.job_id == 'test-job-123'
        assert response.status == 'completed'
        assert response.progress == 100
        assert response.result == {'data': 'result'}
    
    def test_job_status_response_minimal(self):
        """Test JobStatusResponse with minimal data"""
        from src.presentation.api.routers.jobs import JobStatusResponse
        
        data = {
            'job_id': 'test-job-123',
            'status': 'queued',
            'created_at': '2025-09-17T12:00:00Z'
        }
        
        # Execute
        response = JobStatusResponse(**data)
        
        # Assert
        assert response.job_id == 'test-job-123'
        assert response.status == 'queued'
        assert response.progress is None
        assert response.result is None
    
    def test_job_submission_response(self):
        """Test JobSubmissionResponse"""
        from src.presentation.api.routers.jobs import JobSubmissionResponse
        
        data = {
            'job_id': 'new-job-456',
            'status': 'queued',
            'message': 'Job submitted successfully'
        }
        
        # Execute
        response = JobSubmissionResponse(**data)
        
        # Assert
        assert response.job_id == 'new-job-456'
        assert response.status == 'queued'
        assert response.message == 'Job submitted successfully'