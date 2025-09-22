"""
Value objects for the Magic Trick Analyzer domain.
These are immutable objects that are defined by their values.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from uuid import UUID


class DifficultyLevel(Enum):
    """Enumeration for trick difficulty levels."""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


@dataclass(frozen=True)
class BookId:
    """Value object for Book identifier."""
    value: UUID
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class TrickId:
    """Value object for Trick identifier."""
    value: UUID
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Author:
    """Value object representing a book author."""
    name: str
    
    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Author name cannot be empty")
    
    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Title:
    """Value object representing a book or trick title."""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Title cannot be empty")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Props:
    """Value object representing required props for a magic trick."""
    items: List[str]
    
    def __post_init__(self):
        # Ensure list is immutable by converting to tuple
        object.__setattr__(self, 'items', tuple(self.items))
    
    def __iter__(self):
        return iter(self.items)
    
    def __len__(self) -> int:
        return len(self.items)
    
    def __contains__(self, item: str) -> bool:
        return item in self.items


@dataclass(frozen=True)
class PageRange:
    """Value object representing a range of pages in a book."""
    start: int
    end: Optional[int] = None
    
    def __post_init__(self):
        if self.start < 1:
            raise ValueError("Start page must be positive")
        if self.end is not None and self.end < self.start:
            raise ValueError("End page must be greater than or equal to start page")
    
    def __str__(self) -> str:
        if self.end is None:
            return str(self.start)
        if self.start == self.end:
            return str(self.start)
        return f"{self.start}-{self.end}"


@dataclass(frozen=True)
class Confidence:
    """Value object representing AI confidence score."""
    value: float
    
    def __post_init__(self):
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        return self.value >= threshold
    
    def __str__(self) -> str:
        return f"{self.value:.2%}"
