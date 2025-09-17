"""
Pydantic schemas for API request/response models.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from ....domain.entities.magic import Book, Trick, CrossReference


class TrickSchema(BaseModel):
    """Schema for trick representation in API responses."""
    
    id: str
    name: str
    effect_type: str
    description: str
    difficulty: str
    props: List[str]
    confidence: Optional[float] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    created_at: datetime
    
    # Additional fields for review interface
    book_title: Optional[str] = None
    book_author: Optional[str] = None
    method: Optional[str] = None
    
    @classmethod
    def from_entity(cls, trick: Trick, include_book_info: bool = False) -> 'TrickSchema':
        """Create schema from domain entity."""
        schema_data = {
            "id": str(trick.id),
            "name": str(trick.name),
            "effect_type": trick.effect_type.value,
            "description": trick.description,
            "difficulty": trick.difficulty.value,
            "props": list(trick.props.items),
            "confidence": trick.confidence.value if trick.confidence else None,
            "page_start": trick.page_range.start if trick.page_range else None,
            "page_end": trick.page_range.end if trick.page_range else None,
            "created_at": trick.created_at
        }
        
        # Include additional fields for review interface
        if include_book_info and hasattr(trick, 'book'):
            schema_data["book_title"] = str(trick.book.title) if trick.book else None
            schema_data["book_author"] = str(trick.book.author) if trick.book else None
            schema_data["method"] = trick.method
        
        return cls(**schema_data)
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Ambitious Card",
                "effect_type": "card_trick",
                "description": "A selected card repeatedly rises to the top of the deck",
                "difficulty": "intermediate",
                "props": ["deck of cards"],
                "confidence": 0.95,
                "page_start": 42,
                "page_end": 45,
                "created_at": "2023-01-15T10:30:00",
                "book_title": "Expert Card Technique",
                "book_author": "Jean Hugard",
                "method": "Double lift and side steal combination"
            }
        }


class TrickDetailSchema(TrickSchema):
    """Extended schema with additional details for single trick view."""
    
    method: Optional[str] = None
    book_id: str
    updated_at: datetime
    
    @classmethod
    def from_entity(cls, trick: Trick) -> 'TrickDetailSchema':
        """Create detailed schema from domain entity."""
        base_data = TrickSchema.from_entity(trick, include_book_info=True).dict()
        return cls(
            **base_data,
            book_id=str(trick.book_id),
            updated_at=trick.updated_at
        )


class BookSchema(BaseModel):
    """Schema for book representation in API responses."""
    
    id: str
    title: str
    author: str
    publication_year: Optional[int] = None
    isbn: Optional[str] = None
    processed_at: Optional[datetime] = None
    trick_count: int
    created_at: datetime
    
    @classmethod
    def from_entity(cls, book: Book) -> 'BookSchema':
        """Create schema from domain entity."""
        return cls(
            id=str(book.id),
            title=str(book.title),
            author=str(book.author),
            publication_year=book.publication_year,
            isbn=book.isbn,
            processed_at=book.processed_at,
            trick_count=len(book.tricks),
            created_at=book.created_at
        )
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Expert Card Technique",
                "author": "Jean Hugard",
                "publication_year": 1940,
                "isbn": "978-0486217550",
                "processed_at": "2023-01-15T10:30:00",
                "trick_count": 24,
                "created_at": "2023-01-15T09:15:00"
            }
        }


class BookDetailSchema(BookSchema):
    """Extended schema with additional details and tricks."""
    
    file_path: str
    updated_at: datetime
    tricks: List[TrickSchema]
    
    @classmethod
    def from_entity(cls, book: Book) -> 'BookDetailSchema':
        """Create detailed schema from domain entity."""
        base_data = BookSchema.from_entity(book).dict()
        return cls(
            **base_data,
            file_path=book.file_path,
            updated_at=book.updated_at,
            tricks=[TrickSchema.from_entity(trick) for trick in book.tricks]
        )


class CrossReferenceSchema(BaseModel):
    """Schema for cross-reference representation."""
    
    id: str
    source_trick_id: str
    target_trick_id: str
    relationship_type: str
    similarity_score: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    
    @classmethod
    def from_entity(cls, cross_ref: CrossReference) -> 'CrossReferenceSchema':
        """Create schema from domain entity."""
        return cls(
            id=str(cross_ref.id),
            source_trick_id=str(cross_ref.source_trick_id),
            target_trick_id=str(cross_ref.target_trick_id),
            relationship_type=cross_ref.relationship_type,
            similarity_score=cross_ref.similarity_score.value if cross_ref.similarity_score else None,
            notes=cross_ref.notes,
            created_at=cross_ref.created_at
        )


class SearchResultSchema(BaseModel):
    """Schema for search results with metadata."""
    
    tricks: List[TrickSchema]
    total_count: int
    returned_count: int
    skip: int
    limit: int
    
    class Config:
        schema_extra = {
            "example": {
                "tricks": [],
                "total_count": 156,
                "returned_count": 20,
                "skip": 0,
                "limit": 20
            }
        }


class ProcessingStatusSchema(BaseModel):
    """Schema for processing status responses."""
    
    status: str = Field(..., description="Processing status: queued, processing, completed, failed")
    message: str
    job_id: Optional[str] = Field(None, description="Job ID for tracking async processing")
    file_path: Optional[str] = Field(None, description="Path to the processed file")
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "queued",
                "message": "PDF uploaded and queued for processing",
                "job_id": "abc123-def456-ghi789",
                "file_path": "/app/temp/example.pdf",
                "details": {"estimated_time": "5-10 minutes"}
            }
        }


class ErrorSchema(BaseModel):
    """Schema for error responses."""
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid effect type provided",
                "details": {"valid_types": ["card_trick", "coin_magic", "mentalism"]}
            }
        }


class StatisticsSchema(BaseModel):
    """Schema for collection statistics."""
    
    total_books: int
    total_tricks: int
    processed_books: int
    effect_distribution: Dict[str, int]
    difficulty_distribution: Dict[str, int]
    top_authors: List[tuple]
    
    class Config:
        schema_extra = {
            "example": {
                "total_books": 45,
                "total_tricks": 892,
                "processed_books": 43,
                "effect_distribution": {
                    "card_trick": 234,
                    "coin_magic": 156,
                    "mentalism": 89
                },
                "difficulty_distribution": {
                    "beginner": 145,
                    "intermediate": 423,
                    "advanced": 234,
                    "expert": 90
                },
                "top_authors": [
                    ["David Roth", 67],
                    ["Roberto Giobbi", 45],
                    ["Jean Hugard", 38]
                ]
            }
        }


class FeedbackSchema(BaseModel):
    """Schema for user feedback on trick detections."""
    trick_id: str
    is_correct: bool
    user_notes: Optional[str] = None
    suggested_name: Optional[str] = None
    suggested_description: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "trick_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_correct": False,
                "user_notes": "This is actually a coin trick, not a card trick",
                "suggested_name": "French Drop",
                "suggested_description": "A fundamental sleight for making a coin disappear"
            }
        }


class TrainingStatusSchema(BaseModel):
    """Schema for training status responses."""
    status: str  # ready, training, completed, error
    progress: int  # 0-100
    message: str
    model_info: Optional[dict] = None

    class Config:
        schema_extra = {
            "example": {
                "status": "training",
                "progress": 75,
                "message": "Fine-tuning model with 127 training examples",
                "model_info": {
                    "base_model": "all-MiniLM-L6-v2",
                    "training_examples": 127,
                    "epochs": 3
                }
            }
        }


class ModelInfoSchema(BaseModel):
    """Schema for model information."""
    base_model: str
    is_fine_tuned: bool
    fine_tuned_path: Optional[str] = None
    model_exists: bool
    training_available: bool

    class Config:
        schema_extra = {
            "example": {
                "base_model": "all-MiniLM-L6-v2",
                "is_fine_tuned": True,
                "fine_tuned_path": "/models/fine_tuned/magic_model_v2",
                "model_exists": True,
                "training_available": True
            }
        }


class ReviewStatsSchema(BaseModel):
    """Schema for review statistics."""
    total_tricks: int
    pending_review: int
    accuracy: float
    training_examples: int
    correct_detections: int
    incorrect_detections: int

    class Config:
        schema_extra = {
            "example": {
                "total_tricks": 456,
                "pending_review": 23,
                "accuracy": 0.87,
                "training_examples": 89,
                "correct_detections": 67,
                "incorrect_detections": 22
            }
        }
