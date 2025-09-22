"""
FastAPI application for the Magic Trick Analyzer.
Presentation layer following hexagonal architecture.
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import List, Optional, Dict, Any
import uvicorn
from pathlib import Path
import tempfile
import os

from ..api.routers import books, tricks, search, statistics, training
from ...application.use_cases.magic_use_cases import (
    ProcessBooksUseCase, SearchTricksUseCase, FindSimilarTricksUseCase,
    GenerateCrossReferencesUseCase, GetBookStatisticsUseCase
)
from ...infrastructure.database.models import DatabaseConnection
from ...infrastructure.repositories.sql_repositories import (
    SQLBookRepository, SQLTrickRepository, SQLCrossReferenceRepository
)
from ...infrastructure.pdf.pdf_extractor import PDFTextExtractor
# TODO: Remove AI dependencies - moved to ai-service  
# from ...infrastructure.ai.trick_detector import TrickDetector
from ...application.services.pdf_processing import PDFProcessingService
from ...domain.services.magic_analysis import TrickAnalysisService, CrossReferenceService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MagicTrickAnalyzerApp:
    """
    Main application class that wires up all dependencies.
    Follows dependency injection and inversion of control principles.
    """
    
    def __init__(self, database_url: str = "sqlite:///magic_tricks.db"):
        self.database_url = database_url
        self.app = FastAPI(
            title="Magic Trick Analyzer API",
            description="AI-powered analysis and cross-referencing of magic tricks from PDF books",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Initialize dependencies
        self._setup_dependencies()
        self._setup_middleware()
        self._setup_routes()
        self._setup_startup_events()
    
    def _setup_dependencies(self):
        """Setup dependency injection container."""
        # Database
        self.db_connection = DatabaseConnection(self.database_url)
        
        # Repositories
        self.book_repository = SQLBookRepository(self.db_connection)
        self.trick_repository = SQLTrickRepository(self.db_connection)
        self.cross_ref_repository = SQLCrossReferenceRepository(self.db_connection)
        
        # Infrastructure services
        self.pdf_extractor = PDFTextExtractor(enable_ocr=True)
        # TODO: TrickDetector moved to ai-service
        # self.trick_detector = TrickDetector()
        
        # Domain services
        self.trick_analysis_service = TrickAnalysisService()
        self.cross_ref_service = CrossReferenceService(self.trick_analysis_service)
        
        # Application services
        self.pdf_processing_service = PDFProcessingService(
            self.book_repository,
            self.pdf_extractor,
            self.trick_detector,
            logger
        )
        
        # Use cases
        self.process_books_use_case = ProcessBooksUseCase(
            self.pdf_processing_service,
            self.book_repository
        )
        self.search_tricks_use_case = SearchTricksUseCase(
            self.trick_repository,
            self.book_repository
        )
        self.find_similar_tricks_use_case = FindSimilarTricksUseCase(
            self.trick_repository,
            self.cross_ref_repository,
            self.trick_analysis_service,
            self.cross_ref_service
        )
        self.generate_cross_refs_use_case = GenerateCrossReferencesUseCase(
            self.trick_repository,
            self.cross_ref_repository,
            self.cross_ref_service
        )
        self.get_statistics_use_case = GetBookStatisticsUseCase(
            self.book_repository,
            self.trick_repository
        )
    
    def _setup_middleware(self):
        """Setup middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup API routes."""
        # Include routers
        self.app.include_router(
            books.create_router(
                self.process_books_use_case,
                self.book_repository,
                self.get_statistics_use_case
            ),
            prefix="/api/v1/books",
            tags=["books"]
        )
        
        self.app.include_router(
            tricks.create_router(
                self.search_tricks_use_case,
                self.find_similar_tricks_use_case,
                self.trick_repository,
                self.book_repository,
                self.cross_ref_repository
            ),
            prefix="/api/v1/tricks",
            tags=["tricks"]
        )
        
        self.app.include_router(
            search.create_router(self.search_tricks_use_case),
            prefix="/api/v1/search",
            tags=["search"]
        )
        
        self.app.include_router(
            statistics.create_router(self.get_statistics_use_case),
            prefix="/api/v1/statistics",
            tags=["statistics"]
        )
        
        self.app.include_router(
            training.router,
            prefix="/api/v1/training",
            tags=["training"]
        )
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": "magic-trick-analyzer"}
    
    def _setup_startup_events(self):
        """Setup startup and shutdown events."""
        
        @self.app.on_event("startup")
        async def startup_event():
            logger.info("Starting Magic Trick Analyzer API...")
            
            # Create database tables
            self.db_connection.create_tables()
            logger.info("Database tables created/verified")
            
            # Initialize AI models
            await self.trick_detector.initialize()
            logger.info("AI models loaded")
            
            logger.info("Magic Trick Analyzer API started successfully")
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            logger.info("Shutting down Magic Trick Analyzer API...")
            self.db_connection.close()
            logger.info("Database connection closed")
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
        """Run the FastAPI application."""
        uvicorn.run(
            "main:app" if reload else self.app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )


# Create the application instance
def create_app(database_url: str = None) -> FastAPI:
    """Factory function to create the FastAPI app."""
    db_url = database_url or os.getenv("DATABASE_URL", "sqlite:///magic_tricks.db")
    analyzer_app = MagicTrickAnalyzerApp(db_url)
    return analyzer_app.app


# Default app instance
app = create_app()


if __name__ == "__main__":
    # For development
    analyzer_app = MagicTrickAnalyzerApp()
    analyzer_app.run(reload=True)
