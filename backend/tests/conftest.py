"""
Test configuration and fixtures
"""

import os
import tempfile
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, MagicMock

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use test database

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir

@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    mock = Mock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.keys.return_value = []
    return mock

@pytest.fixture
def mock_job_queue():
    """Mock job queue for testing"""
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock.enqueue_ocr_processing.return_value = "test-job-id-ocr"
    mock.enqueue_ai_processing.return_value = "test-job-id-ai"
    mock.enqueue_pdf_processing.return_value = "test-job-id-pdf"
    mock.get_job_status.return_value = {
        "job_id": "test-job-id",
        "status": "completed",
        "result": {"status": "completed"}
    }
    return mock

@pytest.fixture
def test_pdf_path(temp_dir):
    """Create a test PDF file"""
    import fitz  # PyMuPDF
    
    # Create a simple test PDF
    doc = fitz.open()  # Create new PDF
    page = doc.new_page()
    
    # Add some test text
    text = "MAGIC TRICK TEST\n\nThe Vanishing Coin\n\nEffect: A coin vanishes from the magician's hand.\n\nMethod: Use a thumb tip to conceal the coin."
    page.insert_text((50, 50), text)
    
    pdf_path = os.path.join(temp_dir, "test_book.pdf")
    doc.save(pdf_path)
    doc.close()
    
    return pdf_path

@pytest.fixture
def sample_book_data():
    """Sample book data for testing"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Test Magic Book",
        "author": "Test Author",
        "file_path": "/test/path/book.pdf",
        "processed_at": "2025-09-17T12:00:00Z"
    }

@pytest.fixture
def sample_trick_data():
    """Sample trick data for testing"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "The Vanishing Coin",
        "description": "A coin vanishes from the magician's hand using sleight of hand.",
        "effect_type": "Coin",
        "difficulty": "Beginner",
        "page_start": 1,
        "page_end": 2,
        "book_id": "550e8400-e29b-41d4-a716-446655440000"
    }

@pytest.fixture
def mock_sentence_transformer():
    """Mock sentence transformer model"""
    import numpy as np
    
    mock = Mock()
    # Return consistent embeddings for testing
    mock.encode.return_value = np.array([[0.1, 0.2, 0.3, 0.4, 0.5]])
    return mock

@pytest.fixture
def mock_database_session():
    """Mock database session"""
    from unittest.mock import AsyncMock
    
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    return session