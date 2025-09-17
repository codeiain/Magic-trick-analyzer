"""
Shared database models and connection for microservices.
This file contains the core database models that are shared across services.
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import event
import uuid
import os
from datetime import datetime
from typing import Optional

Base = declarative_base()


class BookModel(Base):
    """SQLAlchemy model for Book entity - matching existing database schema."""
    
    __tablename__ = "books"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    file_path = Column(String, nullable=False, unique=True)
    publication_year = Column(Integer, nullable=True)
    isbn = Column(String, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TrickModel(Base):
    """SQLAlchemy model for Trick entity."""
    
    __tablename__ = "tricks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String, ForeignKey("books.id"), nullable=False)
    name = Column(String, nullable=False)
    effect_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    method = Column(Text, nullable=True)
    props = Column(Text, nullable=True)  # JSON string of props list
    difficulty = Column(String, nullable=False)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DatabaseConnection:
    """
    Database connection manager for microservices.
    """
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # Try to get from environment or use default
            database_url = os.getenv("DATABASE_URL", "sqlite:///data/magic_tricks.db")
            
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Enable foreign key constraints for SQLite
        if "sqlite" in database_url:
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def close(self):
        """Close the database connection."""
        self.engine.dispose()


def get_database_connection() -> DatabaseConnection:
    """Get a database connection instance."""
    return DatabaseConnection()


def save_book_ocr_results(book_id: str, title: str, file_path: str, text_content: str, 
                         confidence: float, character_count: int) -> bool:
    """
    Save OCR results to the database using existing schema.
    
    Args:
        book_id: Unique identifier for the book
        title: Title of the book 
        file_path: Path to the processed file
        text_content: Extracted text content
        confidence: OCR confidence score
        character_count: Number of characters extracted
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        db = get_database_connection()
        session = db.get_session()
        
        # Check if book already exists
        existing_book = session.query(BookModel).filter(BookModel.id == book_id).first()
        
        if existing_book:
            # Update existing book with basic info
            existing_book.processed_at = datetime.utcnow()
            existing_book.updated_at = datetime.utcnow()
            print(f"Updated existing book {book_id}")
        else:
            # Create new book record using only existing columns
            book = BookModel(
                id=book_id,
                title=title,
                author="Unknown",  # Will be updated later if available
                file_path=file_path,
                processed_at=datetime.utcnow()
            )
            session.add(book)
            print(f"Created new book record for {book_id}")
        
        session.commit()
        session.close()
        db.close()
        
        print(f"Successfully saved book {book_id} ({character_count} chars, {confidence:.2f} confidence)")
        return True
        
    except Exception as e:
        print(f"Error saving OCR results to database: {e}")
        if 'session' in locals():
            try:
                session.rollback()
                session.close()
            except:
                pass
        if 'db' in locals():
            try:
                db.close()
            except:
                pass
        return False