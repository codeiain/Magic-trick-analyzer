"""
Cross-reference API router for magic tricks.
Provides endpoints to access cross-referenced tricks.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...infrastructure.database.database import DatabaseManager
import sqlite3
import json


class CrossReferenceResponse(BaseModel):
    """Response model for cross-reference data."""
    source_trick_id: str
    source_trick_name: str
    source_author: str
    source_book_title: str
    source_pages: str
    target_trick_id: str
    target_trick_name: str
    target_author: str
    target_book_title: str
    target_pages: str
    relationship_type: str
    similarity_score: float
    notes: Optional[str] = None


class TrickCrossReferences(BaseModel):
    """Model for a trick with its cross-references."""
    trick_id: str
    trick_name: str
    author: str
    book_title: str
    pages: str
    description: str
    difficulty: str
    cross_references: List[CrossReferenceResponse]


class CrossReferenceService:
    """Service for managing cross-references."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.db_path = "shared/data/magic_tricks.db"  # Direct path for now
    
    def get_cross_references_for_trick(self, trick_id: str) -> List[CrossReferenceResponse]:
        """Get all cross-references for a specific trick."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 
                    cr.source_trick_id,
                    t1.name as source_name,
                    b1.author as source_author,
                    b1.title as source_book,
                    CASE 
                        WHEN t1.page_start IS NOT NULL AND t1.page_end IS NOT NULL 
                        THEN t1.page_start || '-' || t1.page_end
                        WHEN t1.page_start IS NOT NULL 
                        THEN CAST(t1.page_start AS TEXT)
                        ELSE 'Unknown'
                    END as source_pages,
                    cr.target_trick_id,
                    t2.name as target_name,
                    b2.author as target_author,
                    b2.title as target_book,
                    CASE 
                        WHEN t2.page_start IS NOT NULL AND t2.page_end IS NOT NULL 
                        THEN t2.page_start || '-' || t2.page_end
                        WHEN t2.page_start IS NOT NULL 
                        THEN CAST(t2.page_start AS TEXT)
                        ELSE 'Unknown'
                    END as target_pages,
                    cr.relationship_type,
                    cr.similarity_score,
                    cr.notes
                FROM cross_references cr
                JOIN tricks t1 ON cr.source_trick_id = t1.id
                JOIN books b1 ON t1.book_id = b1.id
                JOIN tricks t2 ON cr.target_trick_id = t2.id
                JOIN books b2 ON t2.book_id = b2.id
                WHERE cr.source_trick_id = ? OR cr.target_trick_id = ?
                ORDER BY cr.similarity_score DESC
            """, (trick_id, trick_id))
            
            results = cursor.fetchall()
            cross_refs = []
            
            for result in results:
                (source_id, source_name, source_author, source_book, source_pages,
                 target_id, target_name, target_author, target_book, target_pages,
                 rel_type, similarity, notes) = result
                
                cross_refs.append(CrossReferenceResponse(
                    source_trick_id=source_id,
                    source_trick_name=source_name,
                    source_author=source_author,
                    source_book_title=source_book,
                    source_pages=source_pages,
                    target_trick_id=target_id,
                    target_trick_name=target_name,
                    target_author=target_author,
                    target_book_title=target_book,
                    target_pages=target_pages,
                    relationship_type=rel_type,
                    similarity_score=similarity,
                    notes=notes
                ))
            
            return cross_refs
            
        finally:
            conn.close()
    
    def get_cross_referenced_trick_details(self, trick_id: str) -> Optional[TrickCrossReferences]:
        """Get detailed information about a trick and all its cross-references."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get the main trick details
            cursor.execute("""
                SELECT t.id, t.name, b.author, b.title, t.description, t.difficulty,
                       CASE 
                           WHEN t.page_start IS NOT NULL AND t.page_end IS NOT NULL 
                           THEN t.page_start || '-' || t.page_end
                           WHEN t.page_start IS NOT NULL 
                           THEN CAST(t.page_start AS TEXT)
                           ELSE 'Unknown'
                       END as pages
                FROM tricks t
                JOIN books b ON t.book_id = b.id
                WHERE t.id = ?
            """, (trick_id,))
            
            trick_result = cursor.fetchone()
            if not trick_result:
                return None
            
            trick_id, name, author, book_title, description, difficulty, pages = trick_result
            
            # Get cross-references
            cross_refs = self.get_cross_references_for_trick(trick_id)
            
            return TrickCrossReferences(
                trick_id=trick_id,
                trick_name=name,
                author=author,
                book_title=book_title,
                pages=pages,
                description=description,
                difficulty=difficulty,
                cross_references=cross_refs
            )
            
        finally:
            conn.close()
    
    def find_tricks_by_name(self, name: str) -> List[TrickCrossReferences]:
        """Find all tricks with a given name and their cross-references."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT t.id, t.name, b.author, b.title, t.description, t.difficulty,
                       CASE 
                           WHEN t.page_start IS NOT NULL AND t.page_end IS NOT NULL 
                           THEN t.page_start || '-' || t.page_end
                           WHEN t.page_start IS NOT NULL 
                           THEN CAST(t.page_start AS TEXT)
                           ELSE 'Unknown'
                       END as pages
                FROM tricks t
                JOIN books b ON t.book_id = b.id
                WHERE t.name = ?
                ORDER BY b.author
            """, (name,))
            
            results = cursor.fetchall()
            tricks_with_refs = []
            
            for result in results:
                trick_id, name, author, book_title, description, difficulty, pages = result
                cross_refs = self.get_cross_references_for_trick(trick_id)
                
                tricks_with_refs.append(TrickCrossReferences(
                    trick_id=trick_id,
                    trick_name=name,
                    author=author,
                    book_title=book_title,
                    pages=pages,
                    description=description,
                    difficulty=difficulty,
                    cross_references=cross_refs
                ))
            
            return tricks_with_refs
            
        finally:
            conn.close()


def create_cross_reference_router(db_manager: DatabaseManager) -> APIRouter:
    """Create the cross-reference router."""
    router = APIRouter()
    service = CrossReferenceService(db_manager)
    
    @router.get("/trick/{trick_id}", response_model=TrickCrossReferences)
    async def get_trick_cross_references(trick_id: str):
        """Get a trick and all its cross-references."""
        result = service.get_cross_referenced_trick_details(trick_id)
        if not result:
            raise HTTPException(status_code=404, detail="Trick not found")
        return result
    
    @router.get("/by-name/{trick_name}", response_model=List[TrickCrossReferences])
    async def get_tricks_by_name_with_cross_references(trick_name: str):
        """Get all tricks with a specific name and their cross-references."""
        results = service.find_tricks_by_name(trick_name)
        if not results:
            raise HTTPException(status_code=404, detail="No tricks found with that name")
        return results
    
    @router.get("/search", response_model=List[TrickCrossReferences])
    async def search_cross_referenced_tricks(
        q: str = Query(..., description="Search query for trick names"),
        limit: int = Query(20, description="Maximum number of results")
    ):
        """Search for tricks by name and return with cross-references."""
        conn = sqlite3.connect(service.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT t.name
                FROM tricks t
                WHERE t.name LIKE ?
                ORDER BY t.name
                LIMIT ?
            """, (f"%{q}%", limit))
            
            names = [row[0] for row in cursor.fetchall()]
            
            all_results = []
            for name in names:
                tricks = service.find_tricks_by_name(name)
                all_results.extend(tricks)
            
            return all_results[:limit]
            
        finally:
            conn.close()
    
    @router.get("/stats")
    async def get_cross_reference_stats():
        """Get statistics about cross-references in the database."""
        conn = sqlite3.connect(service.db_path)
        cursor = conn.cursor()
        
        try:
            # Total cross-references
            cursor.execute("SELECT COUNT(*) FROM cross_references")
            total_refs = cursor.fetchone()[0]
            
            # By relationship type
            cursor.execute("""
                SELECT relationship_type, COUNT(*) 
                FROM cross_references 
                GROUP BY relationship_type
            """)
            by_type = dict(cursor.fetchall())
            
            # Tricks with cross-references
            cursor.execute("""
                SELECT COUNT(DISTINCT source_trick_id) 
                FROM cross_references
            """)
            tricks_with_refs = cursor.fetchone()[0]
            
            # Most cross-referenced tricks
            cursor.execute("""
                SELECT t.name, b.author, COUNT(cr.source_trick_id) as ref_count
                FROM cross_references cr
                JOIN tricks t ON cr.source_trick_id = t.id
                JOIN books b ON t.book_id = b.id
                GROUP BY t.name, b.author
                ORDER BY ref_count DESC
                LIMIT 5
            """)
            top_tricks = cursor.fetchall()
            
            return {
                "total_cross_references": total_refs,
                "by_relationship_type": by_type,
                "tricks_with_cross_references": tricks_with_refs,
                "most_cross_referenced": [
                    {"name": name, "author": author, "cross_reference_count": count}
                    for name, author, count in top_tricks
                ]
            }
            
        finally:
            conn.close()
    
    return router