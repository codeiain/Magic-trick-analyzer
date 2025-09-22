"""
Tricks API router - handles trick-related endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID

from ....application.use_cases.magic_use_cases import (
    SearchTricksUseCase, SearchTricksRequest, FindSimilarTricksUseCase
)
from ....domain.repositories.magic_repositories import TrickRepository, CrossReferenceRepository
from ....domain.value_objects.common import TrickId
from .schemas import TrickSchema, TrickDetailSchema, CrossReferenceSchema


def create_router(
    search_tricks_use_case: SearchTricksUseCase,
    find_similar_use_case: FindSimilarTricksUseCase,
    trick_repository: TrickRepository,
    book_repository, # Add book repository
    cross_reference_repository: CrossReferenceRepository = None
) -> APIRouter:
    """Create tricks router with injected dependencies."""
    
    router = APIRouter()
    
    @router.get("/", response_model=List[TrickSchema])
    async def list_tricks(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        effect_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        author: Optional[str] = None,
        book_title: Optional[str] = None,
        include_book_info: bool = Query(False, description="Include book information in response")
    ):
        """List tricks with optional filters."""
        try:
            # Build search request
            request = SearchTricksRequest()
            
            if effect_type:
                # effect_type is now a string, so just pass it directly
                request.effect_type = effect_type.lower()
            
            if difficulty:
                request.difficulty_levels = [difficulty.lower()]
            
            if author:
                request.author = author
            
            if book_title:
                request.book_title = book_title
            
            # Execute search
            response = await search_tricks_use_case.execute(request)
            
            # Apply pagination
            paginated_tricks = response.tricks[skip:skip + limit]
            
            # Convert to schemas, including book info if requested
            schemas = []
            for trick in paginated_tricks:
                book_title = None
                book_author = None
                
                if include_book_info:
                    # Fetch book information
                    book = await book_repository.find_by_id(trick.book_id)
                    if book:
                        book_title = str(book.title)
                        book_author = str(book.author)
                
                schemas.append(TrickSchema.from_entity(trick, include_book_info, book_title, book_author))
            
            return schemas
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving tricks: {str(e)}")
    
    @router.get("/{trick_id}", response_model=TrickDetailSchema)
    async def get_trick(trick_id: str):
        """Get detailed information about a specific trick."""
        try:
            trick_uuid = UUID(trick_id)
            trick = await trick_repository.find_by_id(TrickId(trick_uuid))
            if not trick:
                raise HTTPException(status_code=404, detail="Trick not found")
            
            # Get cross-references and similar tricks
            cross_references = []
            similar_tricks = []
            
            if cross_reference_repository:
                try:
                    # Find bidirectional cross-references
                    cross_refs = await cross_reference_repository.find_bidirectional_for_trick(TrickId(trick_uuid))
                    
                    # Get referenced tricks (identical or similar versions)
                    for cross_ref in cross_refs:
                        # Determine which trick ID to fetch (the one that's not the current trick)
                        ref_trick_id = (cross_ref.target_trick_id 
                                       if cross_ref.source_trick_id.value == trick_uuid 
                                       else cross_ref.source_trick_id)
                        
                        ref_trick = await trick_repository.find_by_id(ref_trick_id)
                        if ref_trick and cross_ref.similarity_score and cross_ref.similarity_score.value >= 0.8:
                            cross_references.append(ref_trick)
                        elif ref_trick:
                            similar_tricks.append(ref_trick)
                            
                except Exception as e:
                    # Log error but don't fail the request
                    print(f"Error fetching cross-references for trick {trick_id}: {e}")
            
            return TrickDetailSchema.from_entity(trick, cross_references, similar_tricks)
            
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid trick ID format")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving trick: {str(e)}")
    
    @router.get("/{trick_id}/similar", response_model=List[TrickSchema])
    async def find_similar_tricks(
        trick_id: str,
        similarity_threshold: float = Query(0.7, ge=0.0, le=1.0),
        limit: int = Query(20, ge=1, le=100)
    ):
        """Find tricks similar to the specified trick."""
        try:
            trick_uuid = UUID(trick_id)
            similar_tricks = await find_similar_use_case.execute(
                TrickId(trick_uuid), 
                similarity_threshold
            )
            
            # Apply limit
            limited_tricks = similar_tricks[:limit]
            
            # Convert to schemas with book info
            schemas = []
            for trick in limited_tricks:
                book = await book_repository.find_by_id(trick.book_id)
                book_title = str(book.title) if book else None
                book_author = str(book.author) if book else None
                schemas.append(TrickSchema.from_entity(trick, True, book_title, book_author))
            
            return schemas
            
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid trick ID format")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error finding similar tricks: {str(e)}")
    
    @router.get("/by-effect/{effect_type}", response_model=List[TrickSchema])
    async def get_tricks_by_effect_type(
        effect_type: str,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000)
    ):
        """Get tricks by effect type."""
        try:
            # effect_type is now a string, pass it directly
            tricks = await trick_repository.find_by_effect_type(effect_type.lower())
            
            # Apply pagination
            paginated_tricks = tricks[skip:skip + limit]
            
            # Convert to schemas with book info
            schemas = []
            for trick in paginated_tricks:
                book = await book_repository.find_by_id(trick.book_id)
                book_title = str(book.title) if book else None
                book_author = str(book.author) if book else None
                schemas.append(TrickSchema.from_entity(trick, True, book_title, book_author))
            
            return schemas
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving tricks: {str(e)}")
    
    @router.get("/by-props/", response_model=List[TrickSchema])
    async def get_tricks_by_props(
        props: List[str] = Query(..., description="List of props to search for"),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000)
    ):
        """Get tricks that use specific props."""
        try:
            tricks = await trick_repository.find_by_props(props)
            
            # Apply pagination
            paginated_tricks = tricks[skip:skip + limit]
            
            # Convert to schemas with book info
            schemas = []
            for trick in paginated_tricks:
                book = await book_repository.find_by_id(trick.book_id)
                book_title = str(book.title) if book else None
                book_author = str(book.author) if book else None
                schemas.append(TrickSchema.from_entity(trick, True, book_title, book_author))
            
            return schemas
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving tricks: {str(e)}")
    
    @router.delete("/{trick_id}")
    async def delete_trick(trick_id: str):
        """Delete a specific trick."""
        try:
            trick_uuid = UUID(trick_id)
            trick = await trick_repository.find_by_id(TrickId(trick_uuid))
            if not trick:
                raise HTTPException(status_code=404, detail="Trick not found")
            
            await trick_repository.delete(TrickId(trick_uuid))
            return {"message": f"Trick '{trick.name}' deleted successfully"}
            
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid trick ID format")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting trick: {str(e)}")
    
    return router
