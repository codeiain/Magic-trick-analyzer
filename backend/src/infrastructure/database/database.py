"""
Database initialization and management.
"""
import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from .models import Base
from ..config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and initialization."""
    
    def __init__(self, config: Config):
        self.config = config
        self.engine = None
        self.SessionLocal = None
    
    def initialize(self):
        """Initialize database connection and create tables."""
        logger.info("Initializing database connection...")
        
        # Create engine
        self.engine = create_engine(
            self.config.get_database_url(),
            echo=self.config.database.echo,
            pool_pre_ping=True  # Handle disconnects gracefully
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        self.create_tables()
        
        logger.info("Database initialized successfully")
    
    def create_tables(self):
        """Create all tables in the database."""
        logger.info("Creating database tables...")
        
        # Check if tables exist
        inspector = inspect(self.engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            logger.info("No existing tables found, creating all tables...")
            Base.metadata.create_all(bind=self.engine)
        else:
            logger.info(f"Found existing tables: {existing_tables}")
            # Still create all to handle any new tables
            Base.metadata.create_all(bind=self.engine)
        
        logger.info("Database tables ready")
    
    def get_session(self):
        """Get a database session."""
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Check database health."""
        try:
            if self.engine is None:
                return False
            
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
