"""
Use cases for the Magic Trick Analyzer application.
These represent the application's entry points and orchestrate business logic.
Following Clean Architecture principles.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from ..services.pdf_processing import PDFProcessingService
from ...domain.entities.magic import Book, Trick, CrossReference
from ...domain.repositories.magic_repositories import (
    BookRepository, TrickRepository, CrossReferenceRepository
)
from ...domain.services.magic_analysis import (
    TrickAnalysisService, CrossReferenceService
)
from ...domain.value_objects.common import BookId, TrickId, EffectType


@dataclass
class ProcessBooksRequest:
    """Request object for processing books."""
    file_paths: List[str]
    reprocess_existing: bool = False
    original_filenames: Optional[List[str]] = None


@dataclass
class ProcessBooksResponse:
    """Response object for book processing."""
    processed_books: List[Book]
    failed_files: List[str]
    total_tricks_found: int


@dataclass
class SearchTricksRequest:
    """Request object for searching tricks."""
    query: Optional[str] = None
    effect_type: Optional[EffectType] = None
    props: Optional[List[str]] = None
    author: Optional[str] = None
    book_title: Optional[str] = None
    difficulty_levels: Optional[List[str]] = None


@dataclass
class SearchTricksResponse:
    """Response object for trick search."""
    tricks: List[Trick]
    total_count: int


class ProcessBooksUseCase:
    """
    Use case for processing PDF books to extract magic tricks.
    """
    
    def __init__(
        self,
        pdf_processing_service: PDFProcessingService,
        book_repository: BookRepository
    ):
        self._pdf_processing_service = pdf_processing_service
        self._book_repository = book_repository
    
    async def execute(self, request: ProcessBooksRequest) -> ProcessBooksResponse:
        """
        Execute the process books use case.
        """
        processed_books = []
        failed_files = []
        total_tricks = 0
        
        for i, file_path in enumerate(request.file_paths):
            try:
                # Check if file exists
                if not Path(file_path).exists():
                    failed_files.append(file_path)
                    continue
                
                # Get original filename if provided
                original_filename = None
                if request.original_filenames and i < len(request.original_filenames):
                    original_filename = request.original_filenames[i]
                
                # Check if already processed
                if not request.reprocess_existing:
                    existing = await self._book_repository.find_by_file_path(file_path)
                    if existing and existing.is_processed():
                        processed_books.append(existing)
                        total_tricks += len(existing.tricks)
                        continue
                
                # Process the book
                book = await self._pdf_processing_service.process_pdf_file(file_path, original_filename)
                if book:
                    processed_books.append(book)
                    total_tricks += len(book.tricks)
                else:
                    failed_files.append(file_path)
                    
            except Exception as e:
                failed_files.append(file_path)
                # Log error (assuming logger is injected into service)
                continue
        
        return ProcessBooksResponse(
            processed_books=processed_books,
            failed_files=failed_files,
            total_tricks_found=total_tricks
        )


class SearchTricksUseCase:
    """
    Use case for searching tricks across the collection.
    """
    
    def __init__(
        self,
        trick_repository: TrickRepository,
        book_repository: BookRepository
    ):
        self._trick_repository = trick_repository
        self._book_repository = book_repository
    
    async def execute(self, request: SearchTricksRequest) -> SearchTricksResponse:
        """
        Execute the search tricks use case.
        """
        tricks = []
        
        # Start with all tricks if no specific filters
        if self._is_empty_search(request):
            tricks = await self._trick_repository.find_all()
        else:
            # Apply filters progressively
            if request.effect_type:
                tricks = await self._trick_repository.find_by_effect_type(request.effect_type)
            
            if request.props:
                prop_tricks = await self._trick_repository.find_by_props(request.props)
                tricks = self._intersect_tricks(tricks, prop_tricks)
            
            if request.query:
                query_tricks = await self._trick_repository.search_by_description(request.query)
                name_tricks = await self._trick_repository.find_by_name(request.query)
                query_results = query_tricks + name_tricks
                tricks = self._intersect_tricks(tricks, query_results) if tricks else query_results
            
            if request.author or request.book_title:
                book_tricks = await self._filter_by_book_criteria(request.author, request.book_title)
                tricks = self._intersect_tricks(tricks, book_tricks) if tricks else book_tricks
            
            # Filter by difficulty if specified
            if request.difficulty_levels:
                tricks = [
                    trick for trick in tricks 
                    if trick.difficulty.value in request.difficulty_levels
                ]
        
        return SearchTricksResponse(
            tricks=tricks,
            total_count=len(tricks)
        )
    
    def _is_empty_search(self, request: SearchTricksRequest) -> bool:
        """Check if the search request has no filters."""
        return not any([
            request.query,
            request.effect_type,
            request.props,
            request.author,
            request.book_title,
            request.difficulty_levels
        ])
    
    def _intersect_tricks(self, list1: List[Trick], list2: List[Trick]) -> List[Trick]:
        """Get intersection of two trick lists."""
        ids1 = {trick.id for trick in list1}
        return [trick for trick in list2 if trick.id in ids1]
    
    async def _filter_by_book_criteria(
        self, 
        author: Optional[str], 
        book_title: Optional[str]
    ) -> List[Trick]:
        """Filter tricks by book criteria."""
        books = []
        
        if author:
            # This would require implementing author search in book repository
            all_books = await self._book_repository.find_all()
            books = [book for book in all_books if author.lower() in str(book.author).lower()]
        
        if book_title:
            all_books = books if books else await self._book_repository.find_all()
            books = [book for book in all_books if book_title.lower() in str(book.title).lower()]
        
        # Get all tricks from matching books
        tricks = []
        for book in books:
            book_tricks = await self._trick_repository.find_by_book_id(book.id)
            tricks.extend(book_tricks)
        
        return tricks


class FindSimilarTricksUseCase:
    """
    Use case for finding similar tricks and cross-references.
    """
    
    def __init__(
        self,
        trick_repository: TrickRepository,
        cross_reference_repository: CrossReferenceRepository,
        analysis_service: TrickAnalysisService,
        cross_ref_service: CrossReferenceService
    ):
        self._trick_repository = trick_repository
        self._cross_ref_repository = cross_reference_repository
        self._analysis_service = analysis_service
        self._cross_ref_service = cross_ref_service
    
    async def execute(self, trick_id: TrickId, similarity_threshold: float = 0.7) -> List[Trick]:
        """
        Find tricks similar to the specified trick.
        """
        source_trick = await self._trick_repository.find_by_id(trick_id)
        if not source_trick:
            return []
        
        # Get similar tricks from repository (this would use AI similarity)
        similar_tricks = await self._trick_repository.find_similar(
            source_trick, similarity_threshold
        )
        
        # Apply domain logic to filter results
        filtered_tricks = []
        for trick in similar_tricks:
            if self._analysis_service.are_tricks_similar(source_trick, trick):
                filtered_tricks.append(trick)
        
        return filtered_tricks


class GenerateCrossReferencesUseCase:
    """
    Use case for generating cross-references between tricks.
    """
    
    def __init__(
        self,
        trick_repository: TrickRepository,
        cross_reference_repository: CrossReferenceRepository,
        cross_ref_service: CrossReferenceService
    ):
        self._trick_repository = trick_repository
        self._cross_ref_repository = cross_ref_service
        self._cross_ref_service = cross_ref_service
    
    async def execute(self, book_id: Optional[BookId] = None) -> List[CrossReference]:
        """
        Generate cross-references for tricks (all tricks or specific book).
        """
        # Get tricks to analyze
        if book_id:
            tricks = await self._trick_repository.find_by_book_id(book_id)
        else:
            tricks = await self._trick_repository.find_all()
        
        generated_refs = []
        
        # Compare each trick with others
        for i, source_trick in enumerate(tricks):
            for target_trick in tricks[i+1:]:  # Avoid duplicate comparisons
                
                # Use AI to get similarity score (would be injected service)
                similarity_score = await self._calculate_similarity(source_trick, target_trick)
                
                # Check if cross-reference should be created
                if self._cross_ref_service.should_create_cross_reference(
                    source_trick, target_trick, similarity_score
                ):
                    cross_ref = self._cross_ref_service.create_cross_reference(
                        source_trick, target_trick, similarity_score
                    )
                    
                    # Save cross-reference
                    await self._cross_ref_repository.save(cross_ref)
                    generated_refs.append(cross_ref)
        
        return generated_refs
    
    async def _calculate_similarity(self, trick1: Trick, trick2: Trick) -> float:
        """
        Calculate similarity between tricks.
        This would delegate to AI service in infrastructure layer.
        """
        # Placeholder - would use injected AI similarity service
        return 0.5


class GetBookStatisticsUseCase:
    """
    Use case for getting statistics about books and tricks.
    """
    
    def __init__(
        self,
        book_repository: BookRepository,
        trick_repository: TrickRepository
    ):
        self._book_repository = book_repository
        self._trick_repository = trick_repository
    
    async def execute(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the collection.
        """
        books = await self._book_repository.find_all()
        all_tricks = await self._trick_repository.find_all()
        
        # Basic counts
        stats = {
            "total_books": len(books),
            "total_tricks": len(all_tricks),
            "processed_books": len([book for book in books if book.is_processed()]),
        }
        
        # Effect type distribution
        effect_distribution = {}
        for trick in all_tricks:
            effect_type = trick.effect_type.value
            effect_distribution[effect_type] = effect_distribution.get(effect_type, 0) + 1
        
        stats["effect_distribution"] = effect_distribution
        
        # Difficulty distribution
        difficulty_distribution = {}
        for trick in all_tricks:
            difficulty = trick.difficulty.value
            difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1
        
        stats["difficulty_distribution"] = difficulty_distribution
        
        # Top authors by trick count
        author_counts = {}
        for book in books:
            author = str(book.author)
            trick_count = len(book.tricks)
            author_counts[author] = author_counts.get(author, 0) + trick_count
        
        top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        stats["top_authors"] = top_authors
        
        return stats
