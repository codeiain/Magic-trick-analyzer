"""
Tricks API router - handles trick-related endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID

from ....application.use_cases.magic_use_cases import (
    SearchTricksUseCase, SearchTricksRequest, FindSimilarTricksUseCase
)
from ....domain.repositories.magic_repositories import TrickRepository
from ....domain.value_objects.common import TrickId, EffectType
from .schemas import TrickSchema, TrickDetailSchema, CrossReferenceSchema


def create_router(
    search_tricks_use_case: SearchTricksUseCase,
    find_similar_use_case: FindSimilarTricksUseCase,
    trick_repository: TrickRepository
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
                try:
                    request.effect_type = EffectType(effect_type.lower())
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid effect type: {effect_type}")
            
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
            return [TrickSchema.from_entity(trick, include_book_info) for trick in paginated_tricks]
            
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
            return TrickDetailSchema.from_entity(trick)
            
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
            return [TrickSchema.from_entity(trick, include_book_info=True) for trick in limited_tricks]
            
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
            # Validate effect type
            try:
                effect_enum = EffectType(effect_type.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid effect type: {effect_type}")
            
            tricks = await trick_repository.find_by_effect_type(effect_enum)
            
            # Apply pagination
            paginated_tricks = tricks[skip:skip + limit]
            return [TrickSchema.from_entity(trick, include_book_info=True) for trick in paginated_tricks]
            
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
            return [TrickSchema.from_entity(trick, include_book_info=True) for trick in paginated_tricks]
            
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
