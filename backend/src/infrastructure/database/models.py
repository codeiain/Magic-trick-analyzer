"""
Database infrastructure using SQLAlchemy with SQLite.
Implements the repository pattern from the domain layer.
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import event
import uuid
from datetime import datetime
from typing import Optional

Base = declarative_base()


class EffectTypeModel(Base):
    """SQLAlchemy model for EffectType entity."""
    
    __tablename__ = "effect_types"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)  # broader category like 'Close-up', 'Stage', etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with tricks
    tricks = relationship("TrickModel", back_populates="effect_type_ref")


class BookModel(Base):
    """SQLAlchemy model for Book entity."""
    
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
    
    # OCR content fields for processing
    text_content = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    character_count = Column(Integer, nullable=True)
    
    # Relationship with tricks
    tricks = relationship("TrickModel", back_populates="book", cascade="all, delete-orphan")


class TrickModel(Base):
    """SQLAlchemy model for Trick entity."""
    
    __tablename__ = "tricks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String, ForeignKey("books.id"), nullable=False)
    effect_type_id = Column(String, ForeignKey("effect_types.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    method = Column(Text, nullable=True)
    props = Column(Text, nullable=True)  # JSON string of props list
    difficulty = Column(String, nullable=False)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    book = relationship("BookModel", back_populates="tricks")
    effect_type_ref = relationship("EffectTypeModel", back_populates="tricks")
    source_cross_refs = relationship(
        "CrossReferenceModel", 
        back_populates="source_trick",
        foreign_keys="CrossReferenceModel.source_trick_id"
    )
    target_cross_refs = relationship(
        "CrossReferenceModel",
        back_populates="target_trick", 
        foreign_keys="CrossReferenceModel.target_trick_id"
    )
    
    @hybrid_property
    def effect_type_name(self):
        """Property to return effect type name."""
        return self.effect_type_ref.name if self.effect_type_ref else None


class CrossReferenceModel(Base):
    """SQLAlchemy model for CrossReference entity."""
    
    __tablename__ = "cross_references"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_trick_id = Column(String, ForeignKey("tricks.id"), nullable=False)
    target_trick_id = Column(String, ForeignKey("tricks.id"), nullable=False)
    relationship_type = Column(String, nullable=False)
    similarity_score = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source_trick = relationship(
        "TrickModel", 
        back_populates="source_cross_refs",
        foreign_keys=[source_trick_id]
    )
    target_trick = relationship(
        "TrickModel",
        back_populates="target_cross_refs",
        foreign_keys=[target_trick_id]
    )


class TrainingReviewModel(Base):
    """SQLAlchemy model for training data reviews."""
    
    __tablename__ = "training_reviews"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    trick_id = Column(String, ForeignKey("tricks.id"), nullable=False)
    book_id = Column(String, ForeignKey("books.id"), nullable=False)
    reviewer_id = Column(String, nullable=True)  # Future user system
    
    # Review status
    is_accurate = Column(Boolean, nullable=True)  # True=correct, False=incorrect, None=pending
    confidence_score = Column(Float, nullable=True)  # 0.0-1.0 reviewer confidence
    review_notes = Column(Text, nullable=True)
    
    # Corrected information (if original was wrong)
    corrected_name = Column(String, nullable=True)
    corrected_effect_type = Column(String, nullable=True)
    corrected_description = Column(Text, nullable=True)
    corrected_difficulty = Column(String, nullable=True)
    
    # Training flags
    use_for_training = Column(Boolean, default=True)
    quality_score = Column(Float, nullable=True)  # Overall quality assessment
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TrainingDatasetModel(Base):
    """SQLAlchemy model for training datasets."""
    
    __tablename__ = "training_datasets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String, nullable=False, default="1.0")
    
    # Dataset statistics
    total_tricks = Column(Integer, nullable=False, default=0)
    reviewed_tricks = Column(Integer, nullable=False, default=0)
    accuracy_rate = Column(Float, nullable=True)  # % of accurate detections
    
    # Dataset status
    status = Column(String, nullable=False, default="building")  # building, ready, training, trained, deployed
    is_active = Column(Boolean, default=False)
    
    # Training progress
    training_progress = Column(Integer, default=0)  # 0-100 percentage
    training_message = Column(String, nullable=True)
    
    # Training results
    last_training_job_id = Column(String, nullable=True)
    model_accuracy = Column(Float, nullable=True)
    validation_score = Column(Float, nullable=True)
    model_version = Column(String, nullable=True)
    training_duration = Column(Float, nullable=True)  # seconds
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DatabaseConnection:
    """
    Database connection manager for SQLite.
    """
    
    def __init__(self, database_url: str = "sqlite:///magic_tricks.db"):
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
