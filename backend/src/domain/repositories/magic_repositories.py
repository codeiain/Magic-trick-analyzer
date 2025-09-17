"""
Repository interfaces (ports) for the Magic Trick Analyzer domain.
These define the contracts for data persistence without implementation details.
Following the Repository pattern and Dependency Inversion Principle.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.magic import Book, Trick, CrossReference
from ..value_objects.common import BookId, TrickId, Author, EffectType


class BookRepository(ABC):
    """Abstract repository interface for Book entities."""
    
    @abstractmethod
    async def save(self, book: Book) -> None:
        """Save a book to the repository."""
        pass
    
    @abstractmethod
    async def find_by_id(self, book_id: BookId) -> Optional[Book]:
        """Find a book by its ID."""
        pass
    
    @abstractmethod
    async def find_by_title_and_author(self, title: str, author: str) -> Optional[Book]:
        """Find a book by title and author."""
        pass
    
    @abstractmethod
    async def find_by_file_path(self, file_path: str) -> Optional[Book]:
        """Find a book by its file path."""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Book]:
        """Find all books in the repository."""
        pass
    
    @abstractmethod
    async def find_by_author(self, author: Author) -> List[Book]:
        """Find books by author."""
        pass
    
    @abstractmethod
    async def find_unprocessed(self) -> List[Book]:
        """Find books that haven't been processed yet."""
        pass
    
    @abstractmethod
    async def delete(self, book_id: BookId) -> None:
        """Delete a book from the repository."""
        pass
    
    @abstractmethod
    async def exists(self, book_id: BookId) -> bool:
        """Check if a book exists in the repository."""
        pass


class TrickRepository(ABC):
    """Abstract repository interface for Trick entities."""
    
    @abstractmethod
    async def save(self, trick: Trick) -> None:
        """Save a trick to the repository."""
        pass
    
    @abstractmethod
    async def find_by_id(self, trick_id: TrickId) -> Optional[Trick]:
        """Find a trick by its ID."""
        pass
    
    @abstractmethod
    async def find_by_book_id(self, book_id: BookId) -> List[Trick]:
        """Find all tricks in a specific book."""
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> List[Trick]:
        """Find tricks by name (partial match)."""
        pass
    
    @abstractmethod
    async def find_by_effect_type(self, effect_type: EffectType) -> List[Trick]:
        """Find tricks by effect type."""
        pass
    
    @abstractmethod
    async def find_by_props(self, props: List[str]) -> List[Trick]:
        """Find tricks that use specific props."""
        pass
    
    @abstractmethod
    async def find_similar(self, trick: Trick, similarity_threshold: float = 0.7) -> List[Trick]:
        """Find similar tricks based on content similarity."""
        pass
    
    @abstractmethod
    async def search_by_description(self, query: str) -> List[Trick]:
        """Search tricks by description content."""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Trick]:
        """Find all tricks in the repository."""
        pass
    
    @abstractmethod
    async def delete(self, trick_id: TrickId) -> None:
        """Delete a trick from the repository."""
        pass
    
    @abstractmethod
    async def exists(self, trick_id: TrickId) -> bool:
        """Check if a trick exists in the repository."""
        pass


class CrossReferenceRepository(ABC):
    """Abstract repository interface for CrossReference entities."""
    
    @abstractmethod
    async def save(self, cross_ref: CrossReference) -> None:
        """Save a cross reference to the repository."""
        pass
    
    @abstractmethod
    async def find_by_id(self, cross_ref_id: UUID) -> Optional[CrossReference]:
        """Find a cross reference by its ID."""
        pass
    
    @abstractmethod
    async def find_by_source_trick(self, trick_id: TrickId) -> List[CrossReference]:
        """Find all cross references where the trick is the source."""
        pass
    
    @abstractmethod
    async def find_by_target_trick(self, trick_id: TrickId) -> List[CrossReference]:
        """Find all cross references where the trick is the target."""
        pass
    
    @abstractmethod
    async def find_by_relationship_type(self, relationship_type: str) -> List[CrossReference]:
        """Find cross references by relationship type."""
        pass
    
    @abstractmethod
    async def find_bidirectional_for_trick(self, trick_id: TrickId) -> List[CrossReference]:
        """Find all cross references (both source and target) for a trick."""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[CrossReference]:
        """Find all cross references in the repository."""
        pass
    
    @abstractmethod
    async def delete(self, cross_ref_id: UUID) -> None:
        """Delete a cross reference from the repository."""
        pass
    
    @abstractmethod
    async def exists(self, source_id: TrickId, target_id: TrickId, relationship_type: str) -> bool:
        """Check if a cross reference already exists."""
        pass
