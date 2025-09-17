"""
Statistics API router - handles analytics and statistics endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ....application.use_cases.magic_use_cases import GetBookStatisticsUseCase


def create_router(statistics_use_case: GetBookStatisticsUseCase) -> APIRouter:
    """Create statistics router with injected dependencies."""
    
    router = APIRouter()
    
    @router.get("/overview", response_model=Dict[str, Any])
    async def get_collection_overview():
        """Get comprehensive statistics about the magic trick collection."""
        try:
            stats = await statistics_use_case.execute()
            return {
                "collection_summary": {
                    "total_books": stats["total_books"],
                    "total_tricks": stats["total_tricks"],
                    "processed_books": stats["processed_books"],
                    "processing_rate": (
                        stats["processed_books"] / stats["total_books"] * 100 
                        if stats["total_books"] > 0 else 0
                    )
                },
                "content_analysis": {
                    "effects_by_type": stats["effect_distribution"],
                    "difficulty_breakdown": stats["difficulty_distribution"],
                    "top_authors": stats["top_authors"]
                },
                "insights": {
                    "most_common_effect": max(
                        stats["effect_distribution"].items(), 
                        key=lambda x: x[1]
                    )[0] if stats["effect_distribution"] else None,
                    "most_common_difficulty": max(
                        stats["difficulty_distribution"].items(),
                        key=lambda x: x[1]
                    )[0] if stats["difficulty_distribution"] else None,
                    "average_tricks_per_book": (
                        stats["total_tricks"] / stats["processed_books"]
                        if stats["processed_books"] > 0 else 0
                    )
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating statistics: {str(e)}")
    
    @router.get("/effects")
    async def get_effect_statistics():
        """Get detailed statistics about effect types."""
        try:
            stats = await statistics_use_case.execute()
            effect_stats = stats["effect_distribution"]
            
            total_tricks = sum(effect_stats.values())
            
            return {
                "total_tricks": total_tricks,
                "effect_types": [
                    {
                        "effect_type": effect_type,
                        "count": count,
                        "percentage": (count / total_tricks * 100) if total_tricks > 0 else 0
                    }
                    for effect_type, count in sorted(
                        effect_stats.items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating effect statistics: {str(e)}")
    
    @router.get("/difficulties")
    async def get_difficulty_statistics():
        """Get detailed statistics about difficulty levels."""
        try:
            stats = await statistics_use_case.execute()
            difficulty_stats = stats["difficulty_distribution"]
            
            total_tricks = sum(difficulty_stats.values())
            
            return {
                "total_tricks": total_tricks,
                "difficulty_levels": [
                    {
                        "difficulty": difficulty,
                        "count": count,
                        "percentage": (count / total_tricks * 100) if total_tricks > 0 else 0
                    }
                    for difficulty, count in sorted(
                        difficulty_stats.items(),
                        key=lambda x: ["beginner", "intermediate", "advanced", "expert"].index(x[0])
                    )
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating difficulty statistics: {str(e)}")
    
    @router.get("/authors")
    async def get_author_statistics():
        """Get statistics about authors and their contributions."""
        try:
            stats = await statistics_use_case.execute()
            top_authors = stats["top_authors"]
            
            return {
                "total_authors": len(top_authors),
                "top_contributors": [
                    {
                        "author": author,
                        "trick_count": count,
                        "rank": idx + 1
                    }
                    for idx, (author, count) in enumerate(top_authors)
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating author statistics: {str(e)}")
    
    @router.get("/dashboard")
    async def get_dashboard_stats():
        """Get dashboard statistics summary."""
        try:
            stats = await statistics_use_case.execute()
            
            return {
                "total_tricks": stats["total_tricks"],
                "pending_review": 0,  # TODO: Implement when review system is complete
                "books_processed": stats["processed_books"],
                "accuracy": 0.85  # TODO: Calculate based on actual model performance
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating dashboard statistics: {str(e)}")
    
    return router
