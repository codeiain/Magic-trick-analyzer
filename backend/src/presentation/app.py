"""
FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .api.routers import books, tricks, search, statistics
from .api.routers.review import create_review_router
from ..application.use_cases.magic_use_cases import SearchTricksUseCase
from ..infrastructure.config import Config
from ..infrastructure.database.database import DatabaseManager
from ..infrastructure.repositories.sql_repositories import (
    SQLTrickRepository, SQLBookRepository
)
from ..infrastructure.ai.model_training import (
    TrainingDataGenerator, ModelFineTuner, AdaptiveTrickDetector
)

# Global configuration and database manager
config = None
db_manager = None

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    global config, db_manager
    
    # Load configuration
    config = Config()
    config.setup_logging()
    
    # Validate configuration
    issues = config.validate()
    if issues:
        raise ValueError(f"Configuration issues: {', '.join(issues)}")
    
    # Initialize database
    db_manager = DatabaseManager(config)
    db_manager.initialize()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Magic Trick Analyzer API...")
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager."""
        # Startup
        logger.info("Application starting up...")
        
        # Pre-load AI models (they'll be cached on first use)
        logger.info("AI models will be loaded on first request")
        
        yield
        
        # Shutdown
        logger.info("Application shutting down...")
    
    # Create FastAPI app
    app = FastAPI(
        title="Magic Trick Analyzer",
        description="AI-powered magic trick extraction and cross-referencing service",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create use cases with repositories
    trick_repository = SQLTrickRepository(db_manager)
    book_repository = SQLBookRepository(db_manager)
    search_use_case = SearchTricksUseCase(trick_repository, book_repository)
    
    # Initialize training components
    training_data_generator = TrainingDataGenerator(trick_repository, "data/user_feedback.json")
    model_fine_tuner = ModelFineTuner(config.ai.sentence_transformer_model, "temp/magic-tuned-model")
    adaptive_detector = AdaptiveTrickDetector(config.ai.sentence_transformer_model, "temp/magic-tuned-model")
    
    # Create routers with dependencies
    from ..application.use_cases.magic_use_cases import (
        ProcessBooksUseCase, GetBookStatisticsUseCase, FindSimilarTricksUseCase
    )
    from ..application.services.pdf_processing import PDFProcessingService
    from ..infrastructure.pdf.pdf_extractor import PDFTextExtractor  
    from ..infrastructure.ai.trick_detector import TrickDetector
    
    # Create infrastructure services
    pdf_extractor = PDFTextExtractor(enable_ocr=True)
    trick_detector = TrickDetector(model_name="all-MiniLM-L6-v2")
    pdf_processing_service = PDFProcessingService(
        book_repository=book_repository,
        trick_repository=trick_repository,
        pdf_extractor=pdf_extractor,
        trick_detector=trick_detector
    )
    
    # Create use cases
    process_books_use_case = ProcessBooksUseCase(pdf_processing_service, book_repository)
    statistics_use_case = GetBookStatisticsUseCase(book_repository, trick_repository)
    
    # Create FindSimilarTricksUseCase with minimal dependencies for now
    # TODO: Add proper analysis and cross-reference services when needed
    find_similar_use_case = None  # Will be created when services are implemented
    
    # Include routers
    app.include_router(books.create_router(process_books_use_case, book_repository, statistics_use_case), 
                      prefix="/api/v1/books", tags=["Books"])
    app.include_router(tricks.create_router(search_use_case, find_similar_use_case, trick_repository), 
                      prefix="/api/v1/tricks", tags=["Tricks"])
    app.include_router(search.create_router(search_use_case), 
                      prefix="/api/v1/search", tags=["Search"])
    app.include_router(statistics.create_router(statistics_use_case), 
                      prefix="/api/v1/statistics", tags=["Statistics"])
    
    # Cross-reference router
    try:
        from .api.routers.cross_references import create_cross_reference_router
        app.include_router(create_cross_reference_router(db_manager),
                          prefix="/api/v1/cross-references", tags=["Cross-References"])
        logger.info("Cross-reference router loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load cross-reference router: {e}")
    
    review_router = create_review_router(
        trick_repository=trick_repository,
        book_repository=book_repository,
        search_use_case=search_use_case,
        training_data_generator=training_data_generator,
        model_fine_tuner=model_fine_tuner,
        adaptive_detector=adaptive_detector
    )
    
    app.include_router(review_router, prefix="/api/v1/review", tags=["Review"])
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Magic Trick Analyzer API",
            "version": "1.0.0",
            "docs": "/docs"
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        # Check database health
        db_healthy = db_manager.health_check()
        
        status = "healthy" if db_healthy else "unhealthy"
        status_code = 200 if db_healthy else 503
        
        response = {
            "status": status,
            "database": "healthy" if db_healthy else "unhealthy"
        }
        
        if not db_healthy:
            raise HTTPException(status_code=status_code, detail=response)
        
        return response
    
    return app

# Create the app instance
app = create_app()

def get_config() -> Config:
    """Get the global configuration."""
    global config
    if config is None:
        config = Config()
    return config

def get_db_manager() -> DatabaseManager:
    """Get the global database manager."""
    global db_manager
    if db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return db_manager
