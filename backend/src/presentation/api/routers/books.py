"""Books API router - handles book-related endpoints."""
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import List
from uuid import UUID
import tempfile
import os

from ....application.use_cases.magic_use_cases import ProcessBooksUseCase, ProcessBooksRequest
from ....domain.repositories.magic_repositories import BookRepository
from ....domain.value_objects.common import BookId
from .schemas import BookSchema, BookDetailSchema, ProcessingStatusSchema


def create_router(
    process_books_use_case: ProcessBooksUseCase,
    book_repository: BookRepository,
    statistics_use_case = None  # Optional statistics use case
) -> APIRouter:
    """Create books router with injected dependencies."""
    
    router = APIRouter()
    
    @router.get("/recent", response_model=List[dict])
    async def get_recent_books(limit: int = Query(10, description="Number of recent books to return")):
        """Get recently processed books for dashboard activity feed."""
        try:
            from ....infrastructure.database.models import BookModel
            from ....infrastructure.database.database import DatabaseManager
            from ....infrastructure.config import get_config
            from sqlalchemy import desc
            
            # Get database connection
            config = get_config()
            db_manager = DatabaseManager(config)
            if db_manager.engine is None:
                db_manager.initialize()
            
            session = db_manager.get_session()
            
            # Query recent books that have been processed, ordered by processed_at desc
            recent_books = session.query(BookModel).filter(
                BookModel.processed_at.isnot(None)
            ).order_by(desc(BookModel.processed_at)).limit(limit).all()
            
            # Convert to the format expected by the frontend
            result = []
            for book in recent_books:
                book_data = {
                    "id": str(book.id),
                    "title": book.title,
                    "author": book.author,
                    "processed_at": book.processed_at.isoformat() if book.processed_at else None,
                    "status": "processed",
                    "trick_count": len(book.tricks) if hasattr(book, 'tricks') and book.tricks else 0
                }
                result.append(book_data)
            
            session.close()
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving recent books: {str(e)}")
    
    @router.get("/", response_model=List[BookSchema])
    async def list_books(
        skip: int = 0, 
        limit: int = 100,
        sort: str = Query("created_at", description="Field to sort by (created_at, processed_at, title)"),
        order: str = Query("desc", description="Sort order (asc, desc)")
    ):
        """List all books in the collection with optional sorting."""
        try:
            from ....infrastructure.database.models import BookModel
            from ....infrastructure.database.database import DatabaseManager
            from ....infrastructure.config import get_config
            from sqlalchemy import desc, asc
            
            # Get database connection for advanced querying
            config = get_config()
            db_manager = DatabaseManager(config)
            if db_manager.engine is None:
                db_manager.initialize()
            
            session = db_manager.get_session()
            
            # Build query with sorting
            query = session.query(BookModel)
            
            # Apply sorting
            if sort == "processed_at":
                order_field = BookModel.processed_at
            elif sort == "title":
                order_field = BookModel.title
            else:  # default to created_at
                order_field = BookModel.created_at
                
            if order.lower() == "asc":
                query = query.order_by(asc(order_field))
            else:  # default to desc
                query = query.order_by(desc(order_field))
            
            # Apply pagination
            books_models = query.offset(skip).limit(limit).all()
            
            # Convert to domain entities and then to schemas
            books = []
            for book_model in books_models:
                # Convert to the expected format
                book_data = {
                    "id": str(book_model.id),
                    "title": book_model.title,
                    "author": book_model.author,
                    "publication_year": getattr(book_model, 'publication_year', None),
                    "isbn": getattr(book_model, 'isbn', None),
                    "processed_at": book_model.processed_at.isoformat() if book_model.processed_at else None,
                    "status": "processed" if book_model.processed_at else "pending",
                    "trick_count": len(book_model.tricks) if hasattr(book_model, 'tricks') and book_model.tricks else 0,
                    "created_at": book_model.created_at.isoformat() if book_model.created_at else None
                }
                books.append(book_data)
            
            session.close()
            return books
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving books: {str(e)}")
    
    @router.get("/{book_id}", response_model=BookDetailSchema)
    async def get_book(book_id: str):
        """Get detailed information about a specific book."""
        try:
            book_uuid = UUID(book_id)
            book = await book_repository.find_by_id(BookId(book_uuid))
            if not book:
                raise HTTPException(status_code=404, detail="Book not found")
            return BookDetailSchema.from_entity(book)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid book ID format")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving book: {str(e)}")
    
    @router.get("/processed/list")
    async def get_processed_books():
        """Get all books that have been processed (have processed_at timestamp)."""
        try:
            from ....infrastructure.database.models import BookModel
            from ....infrastructure.database.database import DatabaseManager
            from ....infrastructure.config import get_config
            from sqlalchemy import text
            
            # Get database connection using backend infrastructure
            config = get_config()
            db_manager = DatabaseManager(config)
            if db_manager.engine is None:
                db_manager.initialize()
            
            session = db_manager.get_session()
            
            # Check if the new columns exist and add them if they don't
            try:
                # Try to add missing columns if they don't exist
                with db_manager.engine.connect() as conn:
                    # Check if columns exist
                    result = conn.execute(text("PRAGMA table_info(books);"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'text_content' not in columns:
                        conn.execute(text("ALTER TABLE books ADD COLUMN text_content TEXT;"))
                        conn.commit()
                    
                    if 'ocr_confidence' not in columns:
                        conn.execute(text("ALTER TABLE books ADD COLUMN ocr_confidence REAL;"))
                        conn.commit()
                    
                    if 'character_count' not in columns:
                        conn.execute(text("ALTER TABLE books ADD COLUMN character_count INTEGER;"))
                        conn.commit()
                        
            except Exception as e:
                # If we can't modify the table, continue without these columns
                pass
            
            # Query books that have been processed
            processed_books = session.query(BookModel).filter(
                BookModel.processed_at.isnot(None)
            ).all()
            
            result = []
            for book in processed_books:
                book_data = {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "file_path": book.file_path,
                    "processed_at": book.processed_at.isoformat() if book.processed_at else None,
                    "created_at": book.created_at.isoformat() if book.created_at else None,
                    "publication_year": book.publication_year,
                    "isbn": book.isbn
                }
                
                # Add OCR fields if they exist
                if hasattr(book, 'text_content'):
                    book_data["text_content"] = getattr(book, 'text_content', None)
                if hasattr(book, 'ocr_confidence'):
                    book_data["ocr_confidence"] = getattr(book, 'ocr_confidence', None)
                if hasattr(book, 'character_count'):
                    book_data["character_count"] = getattr(book, 'character_count', None)
                
                result.append(book_data)
                
            session.close()
            
            return {"processed_books": result, "count": len(result)}
            
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error retrieving processed books: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error retrieving processed books: {str(e)}")
    
    @router.get("/processed/{book_id}")
    async def get_processed_book(book_id: str):
        """Get a specific processed book by ID."""
        try:
            from ....infrastructure.database.models import BookModel
            from ....infrastructure.database.database import DatabaseManager
            from ....infrastructure.config import get_config
            
            # Get database connection using backend infrastructure
            config = get_config()
            db_manager = DatabaseManager(config)
            if db_manager.engine is None:
                db_manager.initialize()
            
            session = db_manager.get_session()
            
            # Query specific book that has been processed
            book = session.query(BookModel).filter(
                BookModel.id == book_id,
                BookModel.processed_at.isnot(None)
            ).first()
            
            if not book:
                session.close()
                raise HTTPException(status_code=404, detail="Processed book not found")
            
            result = {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "file_path": book.file_path,
                "processed_at": book.processed_at.isoformat() if book.processed_at else None,
                "created_at": book.created_at.isoformat() if book.created_at else None,
                "updated_at": book.updated_at.isoformat() if book.updated_at else None,
                "publication_year": book.publication_year,
                "isbn": book.isbn,
                "text_content": book.text_content,
                "ocr_confidence": book.ocr_confidence,
                "character_count": book.character_count
            }
                
            session.close()
            
            return result
            
        except HTTPException:
            raise  # Re-raise HTTP exceptions as-is
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error retrieving processed book {book_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error retrieving processed book: {str(e)}")
    
    @router.post("/upload", response_model=ProcessingStatusSchema)
    async def upload_pdf(
        file: UploadFile = File(...),
        reprocess: bool = False
    ):
        """Upload a PDF file for processing."""
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        try:
            # Save uploaded file to temp directory
            import uuid
            file_id = str(uuid.uuid4())
            temp_filename = f"{file_id}_{file.filename}"
            temp_path = os.path.join("/app/temp", temp_filename)
            
            # Ensure temp directory exists
            os.makedirs("/app/temp", exist_ok=True)
            
            # Save uploaded file
            with open(temp_path, "wb") as temp_file:
                content = await file.read()
                temp_file.write(content)
            
            # Submit to job queue instead of processing directly
            from src.infrastructure.queue.job_queue import get_job_queue
            job_queue = get_job_queue()
            
            # Prepare book metadata
            book_metadata = {
                'title': file.filename,
                'book_id': file_id,
                'original_filename': file.filename,
                'reprocess': reprocess
            }
            
            job_id = job_queue.enqueue_ocr_job(
                file_path=temp_path,
                book_metadata=book_metadata
            )
            
            return ProcessingStatusSchema(
                status="queued",
                message="File uploaded successfully. Processing queued.",
                file_path=temp_path,
                job_id=job_id
            )
            
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Upload error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")
    
    @router.get("/job/{job_id}")
    async def get_job_status(job_id: str):
        """Get the status and results of a processing job."""
        try:
            from src.infrastructure.queue.job_queue import get_job_queue
            job_queue = get_job_queue()
            
            job_status = job_queue.get_job_status(job_id)
            if not job_status:
                raise HTTPException(status_code=404, detail="Job not found")
            
            return {
                "job_id": job_id,
                "status": job_status.get('rq_status', job_status.get('status', 'unknown')),
                "type": job_status.get('type'),
                "created_at": job_status.get('created_at'),
                "updated_at": job_status.get('updated_at'),
                "file_path": job_status.get('file_path'),
                "result": job_status.get('result'),
                "error": job_status.get('error')
            }
            
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting job status: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}")
    
    @router.post("/{book_id}/reprocess")
    async def reprocess_book(book_id: str):
        """Reprocess an existing book's OCR text with AI analysis."""
        try:
            # Get existing book with OCR text content
            from ....infrastructure.database.models import BookModel
            from ....infrastructure.database.database import DatabaseManager
            from ....infrastructure.config import get_config
            from src.infrastructure.queue.job_queue import get_job_queue
            
            # Get database connection using backend infrastructure
            config = get_config()
            db_manager = DatabaseManager(config)
            if db_manager.engine is None:
                db_manager.initialize()
            
            session = db_manager.get_session()
            
            # Find book with existing OCR content
            book = session.query(BookModel).filter(
                BookModel.id == book_id,
                BookModel.text_content.isnot(None),
                BookModel.processed_at.isnot(None)
            ).first()
            
            if not book:
                session.close()
                raise HTTPException(
                    status_code=404, 
                    detail="Book not found or no OCR content available for reprocessing"
                )
            
            # Check if we have sufficient text content for AI processing
            if not book.text_content or len(book.text_content.strip()) < 50:
                session.close()
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient text content for AI reprocessing"
                )
            
            session.close()
            
            # Queue AI processing job using existing OCR text
            job_queue = get_job_queue()
            ai_job_id = job_queue.enqueue_ai_job(
                book_id=book_id,
                text_content=book.text_content,
                parent_job_id=None,  # No parent OCR job for reprocessing
                source='reprocess_ui'
            )
            
            return {
                "status": "success",
                "message": f"AI reprocessing queued for book '{book.title}'",
                "job_id": ai_job_id,
                "book_id": book_id,
                "book_title": book.title,
                "text_length": len(book.text_content),
                "ocr_confidence": book.ocr_confidence
            }
            
        except HTTPException:
            raise  # Re-raise HTTP exceptions as-is
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid book ID format")
        except Exception as e:
            import traceback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error reprocessing book {book_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error reprocessing book: {str(e)}")

    @router.get("/{book_id}/reprocess")
    async def reprocess_book_info(book_id: str):
        """Get information about reprocessing a book (deprecated - use POST instead)."""
    @router.get("/{book_id}/reprocess")
    async def reprocess_book_info(book_id: str):
        """Get information about reprocessing a book (deprecated - use POST instead)."""
        try:
            book_uuid = UUID(book_id)
            book = await book_repository.find_by_id(BookId(book_uuid))
            
            if not book:
                raise HTTPException(status_code=404, detail="Book not found")
            
            # Recommend using the new POST endpoint for actual reprocessing
            return {
                "status": "info", 
                "message": f"To reprocess '{book.title}' with AI analysis, use the POST endpoint.",
                "book_id": book_id,
                "reprocess_endpoint": f"/api/v1/books/{book_id}/reprocess",
                "method": "POST",
                "description": "POST to this endpoint will reprocess existing OCR text with updated AI algorithms"
            }
            
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid book ID format")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting reprocess info: {str(e)}")
    
    return router
