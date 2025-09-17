"""
Search API router - handles search endpoints.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ....application.use_cases.magic_use_cases import (
    SearchTricksUseCase, SearchTricksRequest
)
from ....domain.value_objects.common import EffectType
from .schemas import TrickSchema, SearchResultSchema


def create_router(search_tricks_use_case: SearchTricksUseCase) -> APIRouter:
    """Create search router with injected dependencies."""
    
    router = APIRouter()
    
    @router.get("/tricks", response_model=SearchResultSchema)
    async def search_tricks(
        q: Optional[str] = Query(None, description="Search query for trick names and descriptions"),
        effect_type: Optional[str] = Query(None, description="Filter by effect type"),
        props: Optional[List[str]] = Query(None, description="Filter by required props"),
        author: Optional[str] = Query(None, description="Filter by book author"),
        book_title: Optional[str] = Query(None, description="Filter by book title"),
        difficulty: Optional[List[str]] = Query(None, description="Filter by difficulty levels"),
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=500)
    ):
        """
        Search tricks across the entire collection with multiple filters.
        """
        try:
            # Build search request
            request = SearchTricksRequest(
                query=q,
                author=author,
                book_title=book_title,
                props=props,
                difficulty_levels=difficulty
            )
            
            # Validate and set effect type
            if effect_type:
                try:
                    request.effect_type = EffectType(effect_type.lower())
                except ValueError:
                    available_types = [e.value for e in EffectType]
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid effect type '{effect_type}'. Available types: {available_types}"
                    )
            
            # Execute search
            response = await search_tricks_use_case.execute(request)
            
            # Apply pagination
            total_results = len(response.tricks)
            paginated_tricks = response.tricks[skip:skip + limit]
            
            return SearchResultSchema(
                tricks=[TrickSchema.from_entity(trick) for trick in paginated_tricks],
                total_count=total_results,
                returned_count=len(paginated_tricks),
                skip=skip,
                limit=limit
            )
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
    
    @router.get("/tricks/by-description", response_model=List[TrickSchema])
    async def search_by_description(
        description: str = Query(..., description="Search in trick descriptions and methods"),
        limit: int = Query(20, ge=1, le=100)
    ):
        """Search tricks by description content."""
        try:
            request = SearchTricksRequest(query=description)
            response = await search_tricks_use_case.execute(request)
            
            # Limit results
            limited_tricks = response.tricks[:limit]
            return [TrickSchema.from_entity(trick) for trick in limited_tricks]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Description search error: {str(e)}")
    
    @router.get("/suggestions/effect-types")
    async def get_effect_type_suggestions():
        """Get available effect types for search filters."""
        return {
            "effect_types": [
                {
                    "value": effect.value,
                    "label": effect.value.replace("_", " ").title()
                }
                for effect in EffectType
            ]
        }
    
    @router.get("/suggestions/difficulties")
    async def get_difficulty_suggestions():
        """Get available difficulty levels for search filters."""
        return {
            "difficulties": [
                {"value": "beginner", "label": "Beginner"},
                {"value": "intermediate", "label": "Intermediate"},
                {"value": "advanced", "label": "Advanced"},
                {"value": "expert", "label": "Expert"}
            ]
        }
    
    return router
