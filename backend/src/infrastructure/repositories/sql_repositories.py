"""
SQLAlchemy repository implementations.
Concrete implementations of the domain repository interfaces.
"""
import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ...domain.entities.magic import Book, Trick, CrossReference
from ...domain.repositories.magic_repositories import (
    BookRepository, TrickRepository, CrossReferenceRepository
)
from ...domain.value_objects.common import (
    BookId, TrickId, Author, Title, EffectType, DifficultyLevel,
    Props, PageRange, Confidence
)
from ..database.models import BookModel, TrickModel, CrossReferenceModel, DatabaseConnection
from uuid import UUID


class SQLBookRepository(BookRepository):
    """SQLAlchemy implementation of BookRepository."""
    
    def __init__(self, db_connection: DatabaseConnection):
        self._db = db_connection
        self._logger = logging.getLogger(__name__)
    
    async def save(self, book: Book) -> None:
        """Save a book to the database."""
        session = self._db.get_session()
        try:
            # Check if book already exists
            existing = session.query(BookModel).filter_by(id=str(book.id)).first()
            
            if existing:
                # Update existing book
                existing.title = str(book.title)
                existing.author = str(book.author)
                existing.file_path = book.file_path
                existing.publication_year = book.publication_year
                existing.isbn = book.isbn
                existing.processed_at = book.processed_at
                existing.updated_at = book.updated_at
            else:
                # Create new book
                book_model = BookModel(
                    id=str(book.id),
                    title=str(book.title),
                    author=str(book.author),
                    file_path=book.file_path,
                    publication_year=book.publication_year,
                    isbn=book.isbn,
                    processed_at=book.processed_at,
                    created_at=book.created_at,
                    updated_at=book.updated_at
                )
                session.add(book_model)
            
            session.commit()
            self._logger.debug(f"Saved book: {book.title}")
            
        except Exception as e:
            session.rollback()
            self._logger.error(f"Error saving book {book.title}: {str(e)}")
            raise
        finally:
            session.close()
    
    async def find_by_id(self, book_id: BookId) -> Optional[Book]:
        """Find a book by its ID."""
        session = self._db.get_session()
        try:
            book_model = session.query(BookModel).filter_by(id=str(book_id)).first()
            return self._model_to_entity(book_model) if book_model else None
        finally:
            session.close()
    
    async def find_by_title_and_author(self, title: str, author: str) -> Optional[Book]:
        """Find a book by title and author."""
        session = self._db.get_session()
        try:
            book_model = session.query(BookModel).filter(
                and_(BookModel.title == title, BookModel.author == author)
            ).first()
            return self._model_to_entity(book_model) if book_model else None
        finally:
            session.close()
    
    async def find_by_file_path(self, file_path: str) -> Optional[Book]:
        """Find a book by its file path."""
        session = self._db.get_session()
        try:
            book_model = session.query(BookModel).filter_by(file_path=file_path).first()
            return self._model_to_entity(book_model) if book_model else None
        finally:
            session.close()
    
    async def find_all(self) -> List[Book]:
        """Find all books."""
        session = self._db.get_session()
        try:
            book_models = session.query(BookModel).all()
            return [self._model_to_entity(model) for model in book_models]
        finally:
            session.close()
    
    async def find_by_author(self, author: Author) -> List[Book]:
        """Find books by author."""
        session = self._db.get_session()
        try:
            book_models = session.query(BookModel).filter_by(author=str(author)).all()
            return [self._model_to_entity(model) for model in book_models]
        finally:
            session.close()
    
    async def find_unprocessed(self) -> List[Book]:
        """Find books that haven't been processed yet."""
        session = self._db.get_session()
        try:
            book_models = session.query(BookModel).filter(BookModel.processed_at.is_(None)).all()
            return [self._model_to_entity(model) for model in book_models]
        finally:
            session.close()
    
    async def delete(self, book_id: BookId) -> None:
        """Delete a book from the database."""
        session = self._db.get_session()
        try:
            book_model = session.query(BookModel).filter_by(id=str(book_id)).first()
            if book_model:
                session.delete(book_model)
                session.commit()
                self._logger.debug(f"Deleted book: {book_id}")
        except Exception as e:
            session.rollback()
            self._logger.error(f"Error deleting book {book_id}: {str(e)}")
            raise
        finally:
            session.close()
    
    async def exists(self, book_id: BookId) -> bool:
        """Check if a book exists."""
        session = self._db.get_session()
        try:
            return session.query(BookModel).filter_by(id=str(book_id)).first() is not None
        finally:
            session.close()
    
    def _model_to_entity(self, model: BookModel) -> Book:
        """Convert database model to domain entity."""
        book = Book(
            title=Title(model.title),
            author=Author(model.author),
            file_path=model.file_path,
            publication_year=model.publication_year,
            isbn=model.isbn,
            book_id=BookId(UUID(model.id)),
            processed_at=model.processed_at
        )
        # Set timestamps
        book._created_at = model.created_at
        book._updated_at = model.updated_at
        
        # Load associated tricks
        session = self._db.get_session()
        try:
            trick_models = session.query(TrickModel).filter_by(book_id=model.id).all()
            for trick_model in trick_models:
                trick = self._trick_model_to_entity(trick_model)
                book.add_trick(trick)
        finally:
            session.close()
        
        return book

    def _trick_model_to_entity(self, model: TrickModel) -> Trick:
        """Convert trick database model to domain entity."""
        from ...domain.value_objects.common import (
            TrickId, Title, EffectType, DifficultyLevel, Props, Confidence, PageRange
        )
        
        trick = Trick(
            name=Title(model.name),
            effect_type=EffectType(model.effect_type),
            description=model.description or "",
            difficulty=DifficultyLevel(model.difficulty),
            props=Props(model.props.split(',') if model.props else []),
            book_id=BookId(UUID(model.book_id)),
            confidence=Confidence(model.confidence) if model.confidence else None,
            page_range=PageRange(model.page_start, model.page_end) if model.page_start is not None else None,
            trick_id=TrickId(UUID(model.id))
        )
        
        # Set timestamps
        trick._created_at = model.created_at
        
        return trick


class SQLTrickRepository(TrickRepository):
    """SQLAlchemy implementation of TrickRepository."""
    
    def __init__(self, db_connection: DatabaseConnection):
        self._db = db_connection
        self._logger = logging.getLogger(__name__)
    
    async def save(self, trick: Trick) -> None:
        """Save a trick to the database."""
        session = self._db.get_session()
        try:
            existing = session.query(TrickModel).filter_by(id=str(trick.id)).first()
            
            if existing:
                # Update existing trick
                self._update_trick_model(existing, trick)
            else:
                # Create new trick
                trick_model = self._entity_to_model(trick)
                session.add(trick_model)
            
            session.commit()
            self._logger.debug(f"Saved trick: {trick.name}")
            
        except Exception as e:
            session.rollback()
            self._logger.error(f"Error saving trick {trick.name}: {str(e)}")
            raise
        finally:
            session.close()
    
    async def find_by_id(self, trick_id: TrickId) -> Optional[Trick]:
        """Find a trick by its ID."""
        session = self._db.get_session()
        try:
            trick_model = session.query(TrickModel).filter_by(id=str(trick_id)).first()
            return self._model_to_entity(trick_model) if trick_model else None
        finally:
            session.close()
    
    async def find_by_book_id(self, book_id: BookId) -> List[Trick]:
        """Find all tricks in a specific book."""
        session = self._db.get_session()
        try:
            trick_models = session.query(TrickModel).filter_by(book_id=str(book_id)).all()
            return [self._model_to_entity(model) for model in trick_models]
        finally:
            session.close()
    
    async def find_by_name(self, name: str) -> List[Trick]:
        """Find tricks by name (partial match)."""
        session = self._db.get_session()
        try:
            trick_models = session.query(TrickModel).filter(
                TrickModel.name.like(f"%{name}%")
            ).all()
            return [self._model_to_entity(model) for model in trick_models]
        finally:
            session.close()
    
    async def find_by_effect_type(self, effect_type: EffectType) -> List[Trick]:
        """Find tricks by effect type."""
        session = self._db.get_session()
        try:
            trick_models = session.query(TrickModel).filter_by(
                effect_type=effect_type.value
            ).all()
            return [self._model_to_entity(model) for model in trick_models]
        finally:
            session.close()
    
    async def find_by_props(self, props: List[str]) -> List[Trick]:
        """Find tricks that use specific props."""
        session = self._db.get_session()
        try:
            # This is a simplified implementation - in production you'd want
            # a proper JSON query or separate props table
            trick_models = session.query(TrickModel).all()
            matching_tricks = []
            
            for model in trick_models:
                if model.props:
                    try:
                        trick_props = json.loads(model.props)
                        if any(prop in trick_props for prop in props):
                            matching_tricks.append(self._model_to_entity(model))
                    except json.JSONDecodeError:
                        continue
            
            return matching_tricks
        finally:
            session.close()
    
    async def find_similar(self, trick: Trick, similarity_threshold: float = 0.7) -> List[Trick]:
        """Find similar tricks (placeholder - would use vector similarity)."""
        session = self._db.get_session()
        try:
            # Simplified implementation - in production would use vector embeddings
            trick_models = session.query(TrickModel).filter(
                and_(
                    TrickModel.effect_type == trick.effect_type.value,
                    TrickModel.id != str(trick.id)
                )
            ).all()
            return [self._model_to_entity(model) for model in trick_models]
        finally:
            session.close()
    
    async def search_by_description(self, query: str) -> List[Trick]:
        """Search tricks by description content."""
        session = self._db.get_session()
        try:
            trick_models = session.query(TrickModel).filter(
                or_(
                    TrickModel.description.like(f"%{query}%"),
                    TrickModel.method.like(f"%{query}%")
                )
            ).all()
            return [self._model_to_entity(model) for model in trick_models]
        finally:
            session.close()
    
    async def find_all(self) -> List[Trick]:
        """Find all tricks."""
        session = self._db.get_session()
        try:
            trick_models = session.query(TrickModel).all()
            return [self._model_to_entity(model) for model in trick_models]
        finally:
            session.close()
    
    async def delete(self, trick_id: TrickId) -> None:
        """Delete a trick from the database."""
        session = self._db.get_session()
        try:
            trick_model = session.query(TrickModel).filter_by(id=str(trick_id)).first()
            if trick_model:
                session.delete(trick_model)
                session.commit()
                self._logger.debug(f"Deleted trick: {trick_id}")
        except Exception as e:
            session.rollback()
            self._logger.error(f"Error deleting trick {trick_id}: {str(e)}")
            raise
        finally:
            session.close()
    
    async def exists(self, trick_id: TrickId) -> bool:
        """Check if a trick exists."""
        session = self._db.get_session()
        try:
            return session.query(TrickModel).filter_by(id=str(trick_id)).first() is not None
        finally:
            session.close()
    
    def _entity_to_model(self, trick: Trick) -> TrickModel:
        """Convert domain entity to database model."""
        return TrickModel(
            id=str(trick.id),
            book_id=str(trick.book_id),
            name=str(trick.name),
            effect_type=trick.effect_type.value,
            description=trick.description,
            method=trick.method,
            props=json.dumps(list(trick.props.items)) if trick.props else None,
            difficulty=trick.difficulty.value,
            page_start=trick.page_range.start if trick.page_range else None,
            page_end=trick.page_range.end if trick.page_range else None,
            confidence=trick.confidence.value if trick.confidence else None,
            created_at=trick.created_at,
            updated_at=trick.updated_at
        )
    
    def _update_trick_model(self, model: TrickModel, trick: Trick) -> None:
        """Update existing model with entity data."""
        model.name = str(trick.name)
        model.effect_type = trick.effect_type.value
        model.description = trick.description
        model.method = trick.method
        model.props = json.dumps(list(trick.props.items)) if trick.props else None
        model.difficulty = trick.difficulty.value
        model.page_start = trick.page_range.start if trick.page_range else None
        model.page_end = trick.page_range.end if trick.page_range else None
        model.confidence = trick.confidence.value if trick.confidence else None
        model.updated_at = trick.updated_at
    
    def _model_to_entity(self, model: TrickModel) -> Trick:
        """Convert database model to domain entity."""
        # Parse props
        props = Props([])
        if model.props:
            try:
                props = Props(json.loads(model.props))
            except json.JSONDecodeError:
                pass
        
        # Parse page range
        page_range = None
        if model.page_start:
            page_range = PageRange(model.page_start, model.page_end)
        
        # Parse confidence
        confidence = None
        if model.confidence is not None:
            confidence = Confidence(model.confidence)
        
        trick = Trick(
            name=Title(model.name),
            book_id=BookId(UUID(model.book_id)),
            effect_type=EffectType(model.effect_type),
            description=model.description,
            method=model.method,
            props=props,
            difficulty=DifficultyLevel(model.difficulty),
            page_range=page_range,
            confidence=confidence,
            trick_id=TrickId(UUID(model.id))
        )
        
        # Set timestamps
        trick._created_at = model.created_at
        trick._updated_at = model.updated_at
        
        return trick


class SQLCrossReferenceRepository(CrossReferenceRepository):
    """SQLAlchemy implementation of CrossReferenceRepository."""
    
    def __init__(self, db_connection: DatabaseConnection):
        self._db = db_connection
        self._logger = logging.getLogger(__name__)
    
    async def save(self, cross_ref: CrossReference) -> None:
        """Save a cross reference to the database."""
        session = self._db.get_session()
        try:
            existing = session.query(CrossReferenceModel).filter_by(id=str(cross_ref.id)).first()
            
            if existing:
                # Update existing
                existing.relationship_type = cross_ref.relationship_type
                existing.similarity_score = cross_ref.similarity_score.value if cross_ref.similarity_score else None
                existing.notes = cross_ref.notes
            else:
                # Create new
                cross_ref_model = CrossReferenceModel(
                    id=str(cross_ref.id),
                    source_trick_id=str(cross_ref.source_trick_id),
                    target_trick_id=str(cross_ref.target_trick_id),
                    relationship_type=cross_ref.relationship_type,
                    similarity_score=cross_ref.similarity_score.value if cross_ref.similarity_score else None,
                    notes=cross_ref.notes,
                    created_at=cross_ref.created_at
                )
                session.add(cross_ref_model)
            
            session.commit()
            self._logger.debug(f"Saved cross reference: {cross_ref.relationship_type}")
            
        except Exception as e:
            session.rollback()
            self._logger.error(f"Error saving cross reference: {str(e)}")
            raise
        finally:
            session.close()
    
    async def find_by_id(self, cross_ref_id: UUID) -> Optional[CrossReference]:
        """Find a cross reference by its ID."""
        session = self._db.get_session()
        try:
            model = session.query(CrossReferenceModel).filter_by(id=str(cross_ref_id)).first()
            return self._model_to_entity(model) if model else None
        finally:
            session.close()
    
    async def find_by_source_trick(self, trick_id: TrickId) -> List[CrossReference]:
        """Find cross references where trick is the source."""
        session = self._db.get_session()
        try:
            models = session.query(CrossReferenceModel).filter_by(
                source_trick_id=str(trick_id)
            ).all()
            return [self._model_to_entity(model) for model in models]
        finally:
            session.close()
    
    async def find_by_target_trick(self, trick_id: TrickId) -> List[CrossReference]:
        """Find cross references where trick is the target."""
        session = self._db.get_session()
        try:
            models = session.query(CrossReferenceModel).filter_by(
                target_trick_id=str(trick_id)
            ).all()
            return [self._model_to_entity(model) for model in models]
        finally:
            session.close()
    
    async def find_by_relationship_type(self, relationship_type: str) -> List[CrossReference]:
        """Find cross references by relationship type."""
        session = self._db.get_session()
        try:
            models = session.query(CrossReferenceModel).filter_by(
                relationship_type=relationship_type
            ).all()
            return [self._model_to_entity(model) for model in models]
        finally:
            session.close()
    
    async def find_bidirectional_for_trick(self, trick_id: TrickId) -> List[CrossReference]:
        """Find all cross references for a trick."""
        session = self._db.get_session()
        try:
            models = session.query(CrossReferenceModel).filter(
                or_(
                    CrossReferenceModel.source_trick_id == str(trick_id),
                    CrossReferenceModel.target_trick_id == str(trick_id)
                )
            ).all()
            return [self._model_to_entity(model) for model in models]
        finally:
            session.close()
    
    async def find_all(self) -> List[CrossReference]:
        """Find all cross references."""
        session = self._db.get_session()
        try:
            models = session.query(CrossReferenceModel).all()
            return [self._model_to_entity(model) for model in models]
        finally:
            session.close()
    
    async def delete(self, cross_ref_id: UUID) -> None:
        """Delete a cross reference."""
        session = self._db.get_session()
        try:
            model = session.query(CrossReferenceModel).filter_by(id=str(cross_ref_id)).first()
            if model:
                session.delete(model)
                session.commit()
                self._logger.debug(f"Deleted cross reference: {cross_ref_id}")
        except Exception as e:
            session.rollback()
            self._logger.error(f"Error deleting cross reference {cross_ref_id}: {str(e)}")
            raise
        finally:
            session.close()
    
    async def exists(self, source_id: TrickId, target_id: TrickId, relationship_type: str) -> bool:
        """Check if a cross reference already exists."""
        session = self._db.get_session()
        try:
            model = session.query(CrossReferenceModel).filter(
                and_(
                    CrossReferenceModel.source_trick_id == str(source_id),
                    CrossReferenceModel.target_trick_id == str(target_id),
                    CrossReferenceModel.relationship_type == relationship_type
                )
            ).first()
            return model is not None
        finally:
            session.close()
    
    def _model_to_entity(self, model: CrossReferenceModel) -> CrossReference:
        """Convert database model to domain entity."""
        similarity_score = None
        if model.similarity_score is not None:
            similarity_score = Confidence(model.similarity_score)
        
        return CrossReference(
            source_trick_id=TrickId(UUID(model.source_trick_id)),
            target_trick_id=TrickId(UUID(model.target_trick_id)),
            relationship_type=model.relationship_type,
            similarity_score=similarity_score,
            notes=model.notes,
            cross_ref_id=UUID(model.id)
        )
