"""
Unit tests for main application initialization and configuration
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

from src.presentation.app import create_app, get_config, get_db_manager


class TestApplicationCreation:
    """Test main application creation and configuration"""
    
    @patch('src.presentation.app.Config')
    @patch('src.presentation.app.DatabaseManager')  
    @patch('src.presentation.app.JobQueue')
    def test_create_app_success(self, mock_job_queue, mock_db_manager_class, mock_config_class):
        """Test successful application creation"""
        # Setup mocks
        mock_config = Mock()
        mock_config.validate.return_value = []  # No validation issues
        mock_config.api.cors_origins = ["*"]
        mock_config_class.return_value = mock_config
        
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = True
        mock_db_manager_class.return_value = mock_db_manager
        
        mock_queue = Mock()
        mock_job_queue.return_value = mock_queue
        
        # Execute
        app = create_app()
        
        # Assert
        assert app is not None
        assert app.title == "Magic Trick Analyzer"
        assert app.version == "1.0.0"
        
        # Verify initialization calls
        mock_config.setup_logging.assert_called_once()
        mock_config.validate.assert_called_once()
        mock_db_manager.initialize.assert_called_once()
    
    @patch('src.presentation.app.Config')
    def test_create_app_config_validation_failure(self, mock_config_class):
        """Test app creation with configuration validation errors"""
        # Setup
        mock_config = Mock()
        mock_config.validate.return_value = ["Database URL missing", "Redis URL invalid"]
        mock_config_class.return_value = mock_config
        
        # Execute & Assert
        with pytest.raises(ValueError) as exc_info:
            create_app()
        
        assert "Configuration issues" in str(exc_info.value)
        assert "Database URL missing" in str(exc_info.value)
        assert "Redis URL invalid" in str(exc_info.value)
    
    @patch('src.presentation.app.Config')
    @patch('src.presentation.app.DatabaseManager')
    @patch('src.presentation.app.JobQueue')
    def test_create_app_includes_all_routers(self, mock_job_queue, mock_db_manager_class, mock_config_class):
        """Test that all routers are included in the app"""
        # Setup mocks
        mock_config = Mock()
        mock_config.validate.return_value = []
        mock_config.api.cors_origins = ["*"]
        mock_config_class.return_value = mock_config
        
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = True
        mock_db_manager_class.return_value = mock_db_manager
        
        mock_job_queue.return_value = Mock()
        
        # Execute
        app = create_app()
        
        # Assert - check that routes exist
        routes = [route.path for route in app.routes]
        
        # Main routes
        assert "/" in routes
        assert "/health" in routes
        
        # API routes (prefixed routes)
        route_prefixes = [route.path.split('/')[1] for route in app.routes if '/' in route.path[1:]]
        assert "api" in route_prefixes or any("books" in path for path in routes)
    
    @patch('src.presentation.app.Config')
    @patch('src.presentation.app.DatabaseManager')
    @patch('src.presentation.app.JobQueue')
    def test_health_endpoint(self, mock_job_queue, mock_db_manager_class, mock_config_class):
        """Test health check endpoint"""
        from fastapi.testclient import TestClient
        
        # Setup mocks
        mock_config = Mock()
        mock_config.validate.return_value = []
        mock_config.api.cors_origins = ["*"]
        mock_config_class.return_value = mock_config
        
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = True
        mock_db_manager_class.return_value = mock_db_manager
        
        mock_job_queue.return_value = Mock()
        
        # Create app and client
        app = create_app()
        client = TestClient(app)
        
        # Execute
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "healthy"
    
    @patch('src.presentation.app.Config')
    @patch('src.presentation.app.DatabaseManager')
    @patch('src.presentation.app.JobQueue')
    def test_health_endpoint_database_unhealthy(self, mock_job_queue, mock_db_manager_class, mock_config_class):
        """Test health check endpoint with unhealthy database"""
        from fastapi.testclient import TestClient
        
        # Setup mocks
        mock_config = Mock()
        mock_config.validate.return_value = []
        mock_config.api.cors_origins = ["*"]
        mock_config_class.return_value = mock_config
        
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = False  # Database unhealthy
        mock_db_manager_class.return_value = mock_db_manager
        
        mock_job_queue.return_value = Mock()
        
        # Create app and client
        app = create_app()
        client = TestClient(app)
        
        # Execute
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "unhealthy"
        assert data["detail"]["database"] == "unhealthy"
    
    @patch('src.presentation.app.Config')
    @patch('src.presentation.app.DatabaseManager')
    @patch('src.presentation.app.JobQueue')
    def test_root_endpoint(self, mock_job_queue, mock_db_manager_class, mock_config_class):
        """Test root endpoint"""
        from fastapi.testclient import TestClient
        
        # Setup mocks
        mock_config = Mock()
        mock_config.validate.return_value = []
        mock_config.api.cors_origins = ["*"]
        mock_config_class.return_value = mock_config
        
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = True
        mock_db_manager_class.return_value = mock_db_manager
        
        mock_job_queue.return_value = Mock()
        
        # Create app and client
        app = create_app()
        client = TestClient(app)
        
        # Execute
        response = client.get("/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Magic Trick Analyzer API"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
    
    def test_get_config(self):
        """Test get_config function"""
        with patch('src.presentation.app.Config') as mock_config_class:
            mock_config = Mock()
            mock_config_class.return_value = mock_config
            
            # First call should create config
            config1 = get_config()
            assert config1 == mock_config
            
            # Second call should return same instance
            config2 = get_config()
            assert config2 == config1
            assert config1 is config2
    
    def test_get_db_manager_initialized(self):
        """Test get_db_manager when initialized"""
        with patch('src.presentation.app.Config'):
            with patch('src.presentation.app.DatabaseManager') as mock_db_class:
                with patch('src.presentation.app.JobQueue'):
                    mock_db = Mock()
                    mock_db_class.return_value = mock_db
                    
                    # Initialize app (which creates db_manager)
                    create_app()
                    
                    # Get db manager
                    result = get_db_manager()
                    assert result == mock_db
    
    def test_get_db_manager_not_initialized(self):
        """Test get_db_manager when not initialized"""
        # Reset global state
        import src.presentation.app as app_module
        original_db_manager = app_module.db_manager
        app_module.db_manager = None
        
        try:
            with pytest.raises(RuntimeError) as exc_info:
                get_db_manager()
            
            assert "Database manager not initialized" in str(exc_info.value)
        finally:
            # Restore original state
            app_module.db_manager = original_db_manager


class TestApplicationLifespan:
    """Test application lifespan events"""
    
    @patch('src.presentation.app.Config')
    @patch('src.presentation.app.DatabaseManager')
    @patch('src.presentation.app.JobQueue')
    def test_lifespan_startup(self, mock_job_queue, mock_db_manager_class, mock_config_class):
        """Test application startup lifespan"""
        # Setup mocks
        mock_config = Mock()
        mock_config.validate.return_value = []
        mock_config.api.cors_origins = ["*"]
        mock_config_class.return_value = mock_config
        
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = True
        mock_db_manager_class.return_value = mock_db_manager
        
        mock_job_queue.return_value = Mock()
        
        # Execute
        app = create_app()
        
        # Assert app was created successfully (lifespan context manager worked)
        assert app is not None


class TestApplicationConfiguration:
    """Test application configuration and middleware"""
    
    @patch('src.presentation.app.Config')
    @patch('src.presentation.app.DatabaseManager')
    @patch('src.presentation.app.JobQueue')
    def test_cors_middleware_configured(self, mock_job_queue, mock_db_manager_class, mock_config_class):
        """Test CORS middleware is properly configured"""
        # Setup
        mock_config = Mock()
        mock_config.validate.return_value = []
        mock_config.api.cors_origins = ["http://localhost:3000", "https://example.com"]
        mock_config_class.return_value = mock_config
        
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = True
        mock_db_manager_class.return_value = mock_db_manager
        
        mock_job_queue.return_value = Mock()
        
        # Execute
        app = create_app()
        
        # Assert - check that CORS middleware was added
        middleware_types = [type(middleware.cls).__name__ for middleware in app.user_middleware]
        assert "CORSMiddleware" in middleware_types


class TestApplicationIntegration:
    """Integration tests for the full application"""
    
    @pytest.mark.integration
    def test_app_creation_with_real_config(self):
        """Test app creation with real configuration (mocked external dependencies)"""
        with patch('src.presentation.app.DatabaseManager') as mock_db_class:
            with patch('src.presentation.app.JobQueue') as mock_queue_class:
                # Mock external dependencies but use real config
                mock_db = Mock()
                mock_db.health_check.return_value = True
                mock_db_class.return_value = mock_db
                
                mock_queue_class.return_value = Mock()
                
                # Set test environment variables
                test_env = {
                    "DATABASE_URL": "sqlite:///test.db",
                    "REDIS_URL": "redis://localhost:6379/15"
                }
                
                with patch.dict(os.environ, test_env):
                    app = create_app()
                    
                    # Assert app was created
                    assert app is not None
                    assert "Magic Trick Analyzer" in app.title