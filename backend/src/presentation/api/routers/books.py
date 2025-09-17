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
            from src.infrastructure.queue.job_queue import JobQueue
            job_queue = JobQueue()
            
            job_id = job_queue.enqueue_pdf_processing(
                file_path=temp_path,
                book_id=file_id,
                original_filename=file.filename,
                reprocess=reprocess
            )
            
            return ProcessingStatusSchema(
                status="queued",
                message="File uploaded successfully. Processing queued.",
                file_path=temp_path,
                job_id=job_id
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")
    
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
