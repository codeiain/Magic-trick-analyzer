"""Books API router - handles book-related endpoints."""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Query
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
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        reprocess: bool = False
    ):
        """Upload a PDF file for processing."""
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_path = temp_file.name
            
            request = ProcessBooksRequest(
                file_paths=[temp_path],
                reprocess_existing=reprocess,
                original_filenames=[file.filename]
            )
            
            async def process_and_cleanup():
                try:
                    await process_books_use_case.execute(request)
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
            
            background_tasks.add_task(process_and_cleanup)
            
            return ProcessingStatusSchema(
                status="processing",
                message="File uploaded successfully. Processing started in background.",
                file_path=temp_path
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")
    
    @router.get("/{book_id}/reprocess")
    async def reprocess_book(book_id: str, background_tasks: BackgroundTasks):
        """Reprocess an existing book with updated algorithms."""
        try:
            book_uuid = UUID(book_id)
            book = await book_repository.find_by_id(BookId(book_uuid))
            
            if not book:
                raise HTTPException(status_code=404, detail="Book not found")
            
            return {
                "status": "info", 
                "message": f"To reprocess '{book.title}', please re-upload the PDF file.",
                "book_id": book_id
            }
            
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid book ID format")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reprocessing book: {str(e)}")
    
    return router
