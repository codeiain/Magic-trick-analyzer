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
    
    @router.get("/", response_model=List[BookSchema])
    async def list_books(skip: int = 0, limit: int = 100):
        """List all books in the collection."""
        try:
            books = await book_repository.find_all()
            paginated_books = books[skip:skip + limit]
            return [BookSchema.from_entity(book) for book in paginated_books]
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
            import sys
            sys.path.append('/app')
            from shared_database import get_database_connection, BookModel
            
            # Get database connection
            db = get_database_connection()
            session = db.get_session()
            
            # Query books that have been processed
            processed_books = session.query(BookModel).filter(
                BookModel.processed_at.isnot(None)
            ).all()
            
            result = []
            for book in processed_books:
                result.append({
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "file_path": book.file_path,
                    "processed_at": book.processed_at.isoformat() if book.processed_at else None,
                    "created_at": book.created_at.isoformat() if book.created_at else None,
                    "publication_year": book.publication_year,
                    "isbn": book.isbn
                })
                
            session.close()
            db.close()
            
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
            import sys
            sys.path.append('/app')
            from shared_database import get_database_connection, BookModel
            
            # Get database connection
            db = get_database_connection()
            session = db.get_session()
            
            # Query specific book that has been processed
            book = session.query(BookModel).filter(
                BookModel.id == book_id,
                BookModel.processed_at.isnot(None)
            ).first()
            
            if not book:
                session.close()
                db.close()
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
                "isbn": book.isbn
            }
                
            session.close()
            db.close()
            
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
    
    @router.get("/{book_id}/reprocess")
    async def reprocess_book(book_id: str):
        """Reprocess an existing book with updated algorithms."""
        try:
            book_uuid = UUID(book_id)
            book = await book_repository.find_by_id(BookId(book_uuid))
            
            if not book:
                raise HTTPException(status_code=404, detail="Book not found")
            
            # For reprocessing, we now recommend re-uploading via the job queue
            return {
                "status": "info", 
                "message": f"To reprocess '{book.title}', please re-upload the PDF file using the upload endpoint. The new job queue system will handle the processing asynchronously.",
                "book_id": book_id,
                "upload_endpoint": "/api/v1/books/upload?reprocess=true"
            }
            
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid book ID format")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reprocessing book: {str(e)}")
    
    return router
