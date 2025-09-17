# Magic Trick Analyzer - Architecture & Flow Diagram

## System Overview

The Magic Trick Analyzer is a microservices-based system that processes PDF books to extract and analyze magic tricks using OCR and AI technologies.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MAGIC TRICK ANALYZER                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     FRONTEND    │    │     BACKEND     │    │      REDIS      │
│   (React/TS)    │    │   (FastAPI)     │    │   (Job Queue)   │
│                 │    │                 │    │                 │
│ • Upload UI     │◄──►│ • REST API      │◄──►│ • OCR Queue     │
│ • Job Monitor   │    │ • Job Manager   │    │ • AI Queue      │
│ • Book Library  │    │ • File Handler  │    │ • Status Store  │
│ • Status Track  │    │ • Auth/CORS     │    │                 │
│                 │    │                 │    │                 │
│ Port: 5173      │    │ Port: 8000      │    │ Port: 6379      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                        │                        │
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PROCESSING LAYER                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OCR SERVICE   │    │   AI SERVICE    │    │     DATABASE    │
│   (PyMuPDF)     │    │  (Transformers) │    │    (SQLite)     │
│                 │    │                 │    │                 │
│ • PDF Extract   │    │ • Text Analysis │    │ • Books Store   │
│ • Tesseract     │    │ • Trick Extract │    │ • OCR Results   │
│ • Text Clean    │◄──►│ • Embeddings    │◄──►│ • AI Results    │
│ • Validation    │    │ • Classification│    │ • Cross Refs    │
│ • Auto-Chain    │    │ • Cross-Ref     │    │ • Metadata      │
│                 │    │                 │    │                 │
│ Port: 8001      │    │ Port: 8002      │    │ File: SQLite    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Multi-Stage Workflow Flow

```
USER INTERACTION FLOW
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  1. Upload PDF   2. Job Created   3. OCR Process   4. AI Process   5. Done  │
│  ┌───────────┐  ┌───────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────┐ │
│  │    📄     │  │   ⏳ Queued   │ │  🔍 OCR     │ │  🤖 AI      │ │  ✅   │ │
│  │  Upload   │─►│   Job ID:     │►│  Extract    │►│  Analyze    │►│ Ready │ │
│  │   File    │  │   abc-123     │ │  Text       │ │  Tricks     │ │       │ │
│  └───────────┘  └───────────────┘ └─────────────┘ └─────────────┘ └───────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

DETAILED PROCESSING FLOW
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│ Frontend        Backend         Redis          OCR Service    AI Service    │
│    │               │              │                │             │          │
│    │─── POST ─────►│              │                │             │          │
│    │ /books/upload │              │                │             │          │
│    │               │─── ENQUEUE ─►│                │             │          │
│    │               │ ocr_job      │                │             │          │
│    │◄── job_id ────│              │                │             │          │
│    │               │              │                │             │          │
│    │─── GET ──────►│              │                │             │          │ 
│    │ /jobs/{id}    │──── STATUS ─►│                │             │          │
│    │◄── status ────│◄─── info ────│                │             │          │
│    │               │              │                │             │          │
│    │               │              │─── DEQUEUE ───►│             │          │
│    │               │              │ ocr_processor │             │          │
│    │               │              │                │             │          │
│    │               │              │                │─── OCR ────►│          │
│    │               │              │                │ process_pdf │          │
│    │               │              │                │             │          │
│    │               │              │                │◄── TEXT ────│          │
│    │               │              │                │ extracted   │          │
│    │               │              │                │             │          │
│    │               │◄─── UPDATE ──│◄─── CALLBACK ──│             │          │
│    │               │ job_status   │                │             │          │
│    │               │              │                │─── QUEUE ──►│          │
│    │               │              │                │ ai_job      │          │
│    │               │              │                │             │          │
│    │               │              │───── AI ──────►│             │          │
│    │               │              │ dequeue       │             │          │
│    │               │              │                │             │──► AI    │
│    │               │              │                │             │ analyze  │
│    │               │              │                │             │          │
│    │               │              │                │             │◄── DONE │
│    │               │              │                │             │ results  │
│    │               │              │                │             │          │
│    │◄─ COMPLETE ───│◄──── DONE ───│◄────── FINISH ─│◄─ COMPLETE ─│          │
│    │ ai_results    │ multi-stage  │ both_jobs     │ ai_process  │          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend (React/TypeScript)
- **Technology**: Vite + React + TypeScript + TailwindCSS
- **Features**: 
  - File upload with drag & drop
  - Real-time job status monitoring
  - Multi-stage progress visualization
  - Book library management
  - Search and filtering
- **Port**: 5173
- **Key Files**: 
  - `src/pages/BooksPage.tsx` - Main UI
  - `src/hooks/useJobStatus.ts` - Status polling
  - `src/lib/api.ts` - API client

### Backend (FastAPI)
- **Technology**: Python FastAPI + SQLAlchemy
- **Features**:
  - RESTful API endpoints
  - Job queue management
  - File upload handling
  - Multi-stage job orchestration
  - Database operations
- **Port**: 8000
- **Key Endpoints**:
  - `POST /api/v1/books/upload` - File upload
  - `GET /api/v1/jobs/{job_id}` - Job status
  - `POST /api/v1/jobs/ai/queue` - Queue AI job
  - `GET /api/v1/books/processed/list` - Book list

### OCR Service (Python)
- **Technology**: PyMuPDF + Tesseract + pdf2image
- **Features**:
  - PDF text extraction
  - Image-based OCR processing
  - Text validation and cleaning
  - Auto-trigger AI processing
  - Database result storage
- **Port**: 8001
- **Key Functions**:
  - `process_pdf()` - Main OCR processing
  - `trigger_ai_processing()` - AI job chaining
  - Text extraction and validation

### AI Service (Python)
- **Technology**: PyTorch + Sentence Transformers + scikit-learn
- **Features**:
  - Text analysis and classification
  - Magic trick extraction
  - Similarity matching
  - Cross-reference generation
  - Knowledge base building
- **Port**: 8002
- **Key Functions**:
  - `process_text()` - Main AI analysis
  - Embedding generation
  - Trick classification

### Redis (Job Queue)
- **Technology**: Redis + RQ (Redis Queue)
- **Features**:
  - Asynchronous job processing
  - Multi-queue support (ocr, ai, training)
  - Job status persistence
  - Worker coordination
- **Port**: 6379
- **Queues**:
  - `ocr` - OCR processing jobs
  - `ai` - AI analysis jobs
  - `training` - Model training jobs

### Database (SQLite)
- **Technology**: SQLite with SQLAlchemy ORM
- **Features**:
  - Book metadata storage
  - OCR results persistence
  - AI analysis results
  - Cross-reference data
- **Tables**:
  - `books` - Book metadata
  - `ocr_results` - Text extraction data
  - `magic_tricks` - Extracted tricks
  - `cross_references` - Similarity links

## Data Flow

### 1. Upload Phase
```
User → Frontend → Backend → Redis OCR Queue → OCR Service
```

### 2. OCR Processing Phase
```
OCR Worker → PDF Processing → Text Extraction → Database Storage → AI Job Queue
```

### 3. AI Processing Phase
```
AI Worker → Text Analysis → Trick Extraction → Database Storage → Complete
```

### 4. Status Monitoring
```
Frontend → Backend → Redis → Job Status → Multi-stage Progress Display
```

## Key Design Patterns

### 1. Microservices Architecture
- **Separation of Concerns**: Each service handles specific functionality
- **Independent Scaling**: Services can be scaled independently
- **Technology Diversity**: Each service uses optimal tech stack

### 2. Event-Driven Processing
- **Asynchronous Jobs**: Non-blocking processing pipeline
- **Job Chaining**: OCR automatically triggers AI processing
- **Status Updates**: Real-time progress tracking

### 3. Multi-Stage Workflows
- **Pipeline Processing**: Upload → OCR → AI → Complete
- **Stage Independence**: Each stage can succeed/fail independently
- **Progress Visibility**: Users see current stage status

### 4. Non-Blocking UI
- **Immediate Response**: Upload returns job ID immediately
- **Background Processing**: Work continues without user interaction
- **Resumable Sessions**: Users can navigate away and return

## Configuration & Deployment

### Docker Compose Services
```yaml
services:
  frontend:     # React dev server
  backend:      # FastAPI application  
  ocr-service:  # OCR processing worker
  ai-service:   # AI analysis worker
  redis:        # Job queue and cache
```

### Environment Variables
- `REDIS_URL` - Redis connection string
- `DATABASE_URL` - Database connection
- `BACKEND_URL` - Backend service URL
- `OCR_MODELS_PATH` - OCR model location
- `AI_MODELS_PATH` - AI model location

### Ports & Networking
- Frontend: `localhost:5173`
- Backend API: `localhost:8000`
- OCR Service: `localhost:8001`
- AI Service: `localhost:8002`
- Redis: `localhost:6379`

## Security & Performance

### Security Features
- CORS configuration for frontend access
- File type validation
- Input sanitization
- Error handling and logging

### Performance Optimizations
- Async processing with Redis queues
- Database connection pooling
- Model caching in AI service
- Efficient file handling
- Progress streaming

## Monitoring & Debugging

### Logging
- Structured logging across all services
- Job execution tracking
- Error capture and reporting
- Performance metrics

### Status Tracking
- Real-time job status updates
- Multi-stage progress indicators
- Error state handling
- Completion notifications

This architecture provides a robust, scalable, and user-friendly system for processing magic trick books with comprehensive workflow management and real-time feedback.