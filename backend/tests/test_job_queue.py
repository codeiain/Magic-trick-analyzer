"""
Unit tests for the Job Queue infrastructure
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.infrastructure.queue.job_queue import JobQueue


class TestJobQueue:
    """Test JobQueue functionality"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis connection"""
        mock = Mock()
        mock.ping.return_value = True
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = True
        mock.keys.return_value = []
        mock.hset.return_value = True
        mock.hget.return_value = None
        mock.hgetall.return_value = {}
        return mock
    
    @pytest.fixture
    def mock_queue(self):
        """Mock RQ Queue"""
        mock = Mock()
        mock.enqueue.return_value = Mock(id="test-job-id")
        return mock
    
    @pytest.fixture
    def job_queue(self, mock_redis, mock_queue):
        """JobQueue instance with mocked dependencies"""
        with patch('src.infrastructure.queue.job_queue.redis.Redis') as mock_redis_cls:
            mock_redis_cls.from_url.return_value = mock_redis
            with patch('src.infrastructure.queue.job_queue.Queue') as mock_queue_cls:
                mock_queue_cls.return_value = mock_queue
                queue = JobQueue("redis://test:6379")
                queue.redis_conn = mock_redis
                queue.ocr_queue = mock_queue
                queue.ai_queue = mock_queue
                queue.training_queue = mock_queue
                return queue
    
    def test_init_successful(self, job_queue, mock_redis):
        """Test successful JobQueue initialization"""
        assert job_queue.redis_conn == mock_redis
        mock_redis.ping.assert_called_once()
    
    @patch('src.infrastructure.queue.job_queue.redis.Redis')
    def test_init_redis_connection_failure(self, mock_redis_cls):
        """Test JobQueue initialization with Redis connection failure"""
        mock_redis = Mock()
        mock_redis.ping.side_effect = Exception("Connection failed")
        mock_redis_cls.from_url.return_value = mock_redis
        
        with pytest.raises(Exception):
            JobQueue("redis://invalid:6379")
    
    def test_enqueue_ocr_processing(self, job_queue, mock_queue, mock_redis):
        """Test OCR job enqueueing"""
        # Setup
        mock_queue.enqueue.return_value = Mock(id="ocr-job-123")
        
        # Execute
        job_id = job_queue.enqueue_ocr_processing(
            file_path="/test/file.pdf",
            book_id="book-123"
        )
        
        # Assert
        assert job_id == "ocr-job-123"
        mock_queue.enqueue.assert_called_once()
        
        # Check job data was stored
        mock_redis.hset.assert_called()
    
    def test_enqueue_ai_processing(self, job_queue, mock_queue, mock_redis):
        """Test AI job enqueueing"""
        # Setup
        mock_queue.enqueue.return_value = Mock(id="ai-job-456")
        
        # Execute  
        job_id = job_queue.enqueue_ai_processing(
            text_content="Test magic trick content",
            book_id="book-123"
        )
        
        # Assert
        assert job_id == "ai-job-456"
        mock_queue.enqueue.assert_called_once()
        mock_redis.hset.assert_called()
    
    def test_enqueue_training_job(self, job_queue, mock_queue, mock_redis):
        """Test training job enqueueing"""
        # Setup
        mock_queue.enqueue.return_value = Mock(id="training-job-789")
        training_data = {"feedback": [{"trick_id": "123", "rating": 5}]}
        
        # Execute
        job_id = job_queue.enqueue_training_job(training_data)
        
        # Assert
        assert job_id == "training-job-789"
        mock_queue.enqueue.assert_called_once()
        mock_redis.hset.assert_called()
    
    def test_get_job_status_existing_job(self, job_queue, mock_redis, mock_queue):
        """Test getting status for existing job"""
        # Setup
        job_data = {
            "id": "test-job-123",
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "queue": "ocr"
        }
        mock_redis.hgetall.return_value = {k: str(v) for k, v in job_data.items()}
        
        mock_rq_job = Mock()
        mock_rq_job.get_status.return_value = "finished"
        mock_rq_job.result = {"status": "completed", "data": "test"}
        mock_queue.fetch_job.return_value = mock_rq_job
        
        # Execute
        status = job_queue.get_job_status("test-job-123")
        
        # Assert
        assert status is not None
        assert status["job_id"] == "test-job-123"
        assert status["status"] == "finished"
    
    def test_get_job_status_nonexistent_job(self, job_queue, mock_redis):
        """Test getting status for non-existent job"""
        # Setup
        mock_redis.hgetall.return_value = {}
        
        # Execute
        status = job_queue.get_job_status("nonexistent-job")
        
        # Assert
        assert status is None
    
    def test_cancel_job_success(self, job_queue, mock_redis, mock_queue):
        """Test successful job cancellation"""
        # Setup
        job_data = {"queue": "ocr", "status": "queued"}
        mock_redis.hgetall.return_value = {k: str(v) for k, v in job_data.items()}
        
        mock_rq_job = Mock()
        mock_rq_job.cancel.return_value = True
        mock_queue.fetch_job.return_value = mock_rq_job
        
        # Execute
        result = job_queue.cancel_job("test-job-123")
        
        # Assert
        assert result is True
        mock_rq_job.cancel.assert_called_once()
        mock_redis.hset.assert_called()  # Status should be updated
    
    def test_cancel_job_not_found(self, job_queue, mock_redis):
        """Test cancelling non-existent job"""
        # Setup
        mock_redis.hgetall.return_value = {}
        
        # Execute
        result = job_queue.cancel_job("nonexistent-job")
        
        # Assert
        assert result is False
    
    def test_list_jobs(self, job_queue, mock_redis):
        """Test listing jobs"""
        # Setup
        mock_redis.keys.return_value = [b"job:test-1", b"job:test-2"]
        mock_redis.hgetall.side_effect = [
            {"id": "test-1", "status": "completed", "created_at": "2025-09-17T12:00:00Z"},
            {"id": "test-2", "status": "queued", "created_at": "2025-09-17T12:05:00Z"}
        ]
        
        # Execute
        jobs = job_queue.list_jobs()
        
        # Assert
        assert len(jobs) == 2
        assert jobs[0]["id"] == "test-1"
        assert jobs[1]["id"] == "test-2"
    
    def test_list_jobs_with_status_filter(self, job_queue, mock_redis):
        """Test listing jobs with status filter"""
        # Setup
        mock_redis.keys.return_value = [b"job:test-1", b"job:test-2"]
        mock_redis.hgetall.side_effect = [
            {"id": "test-1", "status": "completed", "created_at": "2025-09-17T12:00:00Z"},
            {"id": "test-2", "status": "queued", "created_at": "2025-09-17T12:05:00Z"}
        ]
        
        # Execute
        jobs = job_queue.list_jobs(status_filter="completed")
        
        # Assert
        assert len(jobs) == 1
        assert jobs[0]["id"] == "test-1"
        assert jobs[0]["status"] == "completed"
    
    def test_cleanup_completed_jobs(self, job_queue, mock_redis):
        """Test cleanup of old completed jobs"""
        # Setup - create old completed jobs
        old_time = (datetime.utcnow() - timedelta(days=8)).isoformat()
        mock_redis.keys.return_value = [b"job:old-job", b"job:recent-job"]
        mock_redis.hgetall.side_effect = [
            {"id": "old-job", "status": "completed", "created_at": old_time, "queue": "ocr"},
            {"id": "recent-job", "status": "completed", "created_at": datetime.utcnow().isoformat(), "queue": "ai"}
        ]
        
        # Mock RQ job fetching
        mock_old_job = Mock()
        mock_old_job.get_status.return_value = "finished"
        mock_recent_job = Mock() 
        mock_recent_job.get_status.return_value = "finished"
        
        job_queue.ocr_queue.fetch_job.return_value = mock_old_job
        job_queue.ai_queue.fetch_job.return_value = mock_recent_job
        
        # Execute
        cleaned_count = job_queue.cleanup_completed_jobs()
        
        # Assert
        assert cleaned_count == 1  # Only old job should be cleaned
        mock_redis.delete.assert_called_once_with("job:old-job")
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_wait_for_job_completion_success(self, mock_sleep, job_queue):
        """Test waiting for job completion successfully"""
        # Setup
        job_queue.get_job_status = Mock()
        job_queue.get_job_status.side_effect = [
            {"status": "queued"},
            {"status": "started"},
            {"status": "finished", "result": {"data": "completed"}}
        ]
        
        # Execute
        result = job_queue._wait_for_job_completion("test-job", timeout=30)
        
        # Assert
        assert result == {"data": "completed"}
    
    @patch('time.sleep')
    def test_wait_for_job_completion_timeout(self, mock_sleep, job_queue):
        """Test waiting for job times out"""
        # Setup
        job_queue.get_job_status = Mock()
        job_queue.get_job_status.return_value = {"status": "started"}
        
        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            job_queue._wait_for_job_completion("test-job", timeout=1)
        
        assert "did not complete within" in str(exc_info.value)
    
    @patch('time.sleep')
    def test_wait_for_job_completion_failure(self, mock_sleep, job_queue):
        """Test waiting for job that fails"""
        # Setup
        job_queue.get_job_status = Mock()
        job_queue.get_job_status.return_value = {
            "status": "failed", 
            "error": "Processing failed"
        }
        
        # Execute & Assert
        with pytest.raises(Exception) as exc_info:
            job_queue._wait_for_job_completion("test-job", timeout=30)
        
        assert "Processing failed" in str(exc_info.value)


class TestJobQueueIntegration:
    """Integration tests for JobQueue (requires Redis)"""
    
    @pytest.mark.redis
    @pytest.mark.integration
    def test_real_redis_connection(self):
        """Test actual Redis connection (requires running Redis)"""
        try:
            queue = JobQueue("redis://localhost:6379/15")
            assert queue.redis_conn.ping() is True
        except Exception:
            pytest.skip("Redis not available for integration test")