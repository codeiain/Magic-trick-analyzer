"""
Domain entities for the Magic Trick Analyzer.
These represent the core business objects with identity and lifecycle.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from ..value_objects.common import (
    Author, BookId, Title, TrickId, Props, PageRange, 
    DifficultyLevel, EffectType, Confidence
)


class Book:
    """
    Book entity representing a magic book in the collection.
    Following Domain-Driven Design principles with clear identity.
    """
    
    def __init__(
        self,
        title: Title,
        author: Author,
        file_path: str,
        publication_year: Optional[int] = None,
        isbn: Optional[str] = None,
        book_id: Optional[BookId] = None,
        processed_at: Optional[datetime] = None
    ):
        self._id = book_id or BookId(uuid4())
        self._title = title
        self._author = author
        self._file_path = file_path
        self._publication_year = publication_year
        self._isbn = isbn
        self._processed_at = processed_at
        self._tricks: List['Trick'] = []
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
    
    @property
    def id(self) -> BookId:
        return self._id
    
    @property
    def title(self) -> Title:
        return self._title
    
    @property
    def author(self) -> Author:
        return self._author
    
    @property
    def file_path(self) -> str:
        return self._file_path
    
    @property
    def publication_year(self) -> Optional[int]:
        return self._publication_year
    
    @property
    def isbn(self) -> Optional[str]:
        return self._isbn
    
    @property
    def processed_at(self) -> Optional[datetime]:
        return self._processed_at
    
    @property
    def tricks(self) -> List['Trick']:
        return self._tricks.copy()  # Return copy to maintain encapsulation
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    def add_trick(self, trick: 'Trick') -> None:
        """Add a trick to this book."""
        if trick not in self._tricks:
            self._tricks.append(trick)
            self._updated_at = datetime.utcnow()
    
    def remove_trick(self, trick: 'Trick') -> None:
        """Remove a trick from this book."""
        if trick in self._tricks:
            self._tricks.remove(trick)
            self._updated_at = datetime.utcnow()
    
    def mark_as_processed(self) -> None:
        """Mark the book as processed."""
        self._processed_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
    
    def is_processed(self) -> bool:
        """Check if the book has been processed."""
        return self._processed_at is not None
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Book):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        return hash(self._id)
    
    def __str__(self) -> str:
        return f"{self._title} by {self._author}"
    
    def __repr__(self) -> str:
        return f"Book(id={self._id}, title='{self._title}', author='{self._author}')"


class Trick:
    """
    Trick entity representing a magic trick with its properties and relationships.
    """
    
    def __init__(
        self,
        name: Title,
        book_id: BookId,
        effect_type: EffectType,
        description: str,
        method: Optional[str] = None,
        props: Optional[Props] = None,
        difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
        page_range: Optional[PageRange] = None,
        confidence: Optional[Confidence] = None,
        trick_id: Optional[TrickId] = None
    ):
        self._id = trick_id or TrickId(uuid4())
        self._name = name
        self._book_id = book_id
        self._effect_type = effect_type
        self._description = description
        self._method = method
        self._props = props or Props([])
        self._difficulty = difficulty
        self._page_range = page_range
        self._confidence = confidence
        self._cross_references: List['CrossReference'] = []
        self._created_at = datetime.utcnow()
        self._updated_at = datetime.utcnow()
    
    @property
    def id(self) -> TrickId:
        return self._id
    
    @property
    def name(self) -> Title:
        return self._name
    
    @property
    def book_id(self) -> BookId:
        return self._book_id
    
    @property
    def effect_type(self) -> EffectType:
        return self._effect_type
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def method(self) -> Optional[str]:
        return self._method
    
    @property
    def props(self) -> Props:
        return self._props
    
    @property
    def difficulty(self) -> DifficultyLevel:
        return self._difficulty
    
    @property
    def page_range(self) -> Optional[PageRange]:
        return self._page_range
    
    @property
    def confidence(self) -> Optional[Confidence]:
        return self._confidence
    
    @property
    def cross_references(self) -> List['CrossReference']:
        return self._cross_references.copy()
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    def update_description(self, description: str) -> None:
        """Update the trick description."""
        self._description = description
        self._updated_at = datetime.utcnow()
    
    def update_method(self, method: str) -> None:
        """Update the trick method."""
        self._method = method
        self._updated_at = datetime.utcnow()
    
    def set_difficulty(self, difficulty: DifficultyLevel) -> None:
        """Set the difficulty level."""
        self._difficulty = difficulty
        self._updated_at = datetime.utcnow()
    
    def add_cross_reference(self, cross_ref: 'CrossReference') -> None:
        """Add a cross reference to this trick."""
        if cross_ref not in self._cross_references:
            self._cross_references.append(cross_ref)
            self._updated_at = datetime.utcnow()
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if the trick was identified with high confidence."""
        return self._confidence is not None and self._confidence.is_high_confidence(threshold)
    
    def requires_props(self) -> bool:
        """Check if the trick requires props."""
        return len(self._props) > 0
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Trick):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        return hash(self._id)
    
    def __str__(self) -> str:
        return f"{self._name} ({self._effect_type.value})"
    
    def __repr__(self) -> str:
        return f"Trick(id={self._id}, name='{self._name}', effect_type={self._effect_type})"


class CrossReference:
    """
    Entity representing relationships between tricks across different books.
    """
    
    def __init__(
        self,
        source_trick_id: TrickId,
        target_trick_id: TrickId,
        relationship_type: str,
        similarity_score: Optional[Confidence] = None,
        notes: Optional[str] = None,
        cross_ref_id: Optional[UUID] = None
    ):
        self._id = cross_ref_id or uuid4()
        self._source_trick_id = source_trick_id
        self._target_trick_id = target_trick_id
        self._relationship_type = relationship_type
        self._similarity_score = similarity_score
        self._notes = notes
        self._created_at = datetime.utcnow()
    
    @property
    def id(self) -> UUID:
        return self._id
    
    @property
    def source_trick_id(self) -> TrickId:
        return self._source_trick_id
    
    @property
    def target_trick_id(self) -> TrickId:
        return self._target_trick_id
    
    @property
    def relationship_type(self) -> str:
        return self._relationship_type
    
    @property
    def similarity_score(self) -> Optional[Confidence]:
        return self._similarity_score
    
    @property
    def notes(self) -> Optional[str]:
        return self._notes
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    def is_bidirectional(self) -> bool:
        """Check if this is a bidirectional relationship."""
        return self._relationship_type in ["variation", "similar", "related"]
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, CrossReference):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        return hash(self._id)
    
    def __str__(self) -> str:
        return f"{self._relationship_type}: {self._source_trick_id} -> {self._target_trick_id}"
    
    def __repr__(self) -> str:
        return f"CrossReference(id={self._id}, type='{self._relationship_type}')"
