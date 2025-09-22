"""
Database module for OCR service.
This imports the shared database functions from the mounted shared volume.
"""
import sys
import os

# Add the shared directory to Python path if mounted
shared_path = '/app/shared'
if os.path.exists(shared_path) and shared_path not in sys.path:
    sys.path.insert(0, shared_path)

try:
    # Try to import from shared module
    from database import save_book_ocr_results, get_database_connection, BookModel
    print("Successfully imported shared database module")
except ImportError as e:
    print(f"Failed to import shared database module: {e}")
    
    # Fallback: implement basic database functions locally
    from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    import uuid
    from datetime import datetime
    
    Base = declarative_base()
    
    class BookModel(Base):
        """Local SQLAlchemy model for Book entity."""
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
        text_content = Column(Text, nullable=True)
        ocr_confidence = Column(Float, nullable=True)
        character_count = Column(Integer, nullable=True)
    
    class DatabaseConnection:
        """Local database connection manager."""
        
        def __init__(self, database_url: str = None):
            if database_url is None:
                database_url = os.getenv("DATABASE_URL", "sqlite:///data/magic_tricks.db")
                
            self.database_url = database_url
            self.engine = create_engine(
                database_url,
                echo=False,
                connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
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
        """Save OCR results to the database."""
        try:
            db = get_database_connection()
            db.create_tables()  # Ensure tables exist
            session = db.get_session()
            
            # Check if book already exists
            existing_book = session.query(BookModel).filter(BookModel.id == book_id).first()
            
            if existing_book:
                # Update existing book with OCR results
                existing_book.text_content = text_content
                existing_book.ocr_confidence = confidence
                existing_book.character_count = character_count
                existing_book.processed_at = datetime.utcnow()
                existing_book.updated_at = datetime.utcnow()
                print(f"Updated existing book {book_id} with OCR content")
            else:
                # Create new book record with OCR content
                book = BookModel(
                    id=book_id,
                    title=title,
                    author="Unknown",
                    file_path=file_path,
                    text_content=text_content,
                    ocr_confidence=confidence,
                    character_count=character_count,
                    processed_at=datetime.utcnow()
                )
                session.add(book)
                print(f"Created new book record for {book_id} with OCR content")
            
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

# Export the functions that OCR processor expects
__all__ = ['save_book_ocr_results', 'get_database_connection', 'BookModel']