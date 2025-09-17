# Magic Trick Analyzer# Magic Trick Analyzer



An AI-powered system for analyzing and cataloging magic tricks from PDF books. The system extracts text content, identifies magic tricks, and provides a searchable database with training capabilities for improved detection accuracy.AI-powered service for extracting and cross-referencing magic tricks from PDF books.



![Magic Trick Analyzer](https://img.shields.io/badge/Python-3.11-blue)## Features

![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)

![React](https://img.shields.io/badge/React-TypeScript-blue)- 🎭 **AI-Powered Trick Detection**: Uses local NLP models to identify magic tricks in PDF documents

![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen)- 🧠 **Model Fine-Tuning**: Improve AI accuracy with user feedback and model training

- 🌐 **Review Interface**: Web dashboard for reviewing AI detections and providing feedback

## 🎭 Features- 📚 **Cross-Reference System**: Find similar tricks across different books

- 🔍 **Semantic Search**: Search for tricks by description, props, or technique

- **PDF Processing**: Upload PDF books and extract text content with OCR support- 📊 **Statistics & Analytics**: Track your magic library insights

- **AI-Powered Detection**: Automatically identify and categorize magic tricks using sentence transformers- 🐳 **Docker Ready**: Fully containerized with all dependencies

- **Interactive Training**: Train the AI model with user feedback for improved accuracy- 🚀 **Fast API**: Modern REST API with automatic documentation

- **Searchable Database**: Browse and search through extracted tricks with advanced filtering- 🔒 **Privacy-First**: No external APIs, all processing done locally

- **Modern Web Interface**: React/TypeScript frontend with real-time updates and beautiful UI

- **RESTful API**: FastAPI backend with comprehensive endpoints and automatic documentation## Architecture

- **Cross-References**: Find similar tricks across different books and authors

- **Statistics Dashboard**: Track model performance and library insightsBuilt using hexagonal (clean) architecture with SOLID principles:



## 🏗️ Architecture- **Domain Layer**: Core business logic and entities

- **Application Layer**: Use cases and orchestration

- **Backend**: FastAPI with Python 3.11- **Infrastructure Layer**: External dependencies (database, AI models, PDF processing)

- **Frontend**: React with TypeScript, Vite, and TanStack Query- **Presentation Layer**: REST API endpoints

- **Database**: SQLite with SQLAlchemy ORM

- **AI Models**: Sentence Transformers for text analysis and similarity detection## Quick Start

- **OCR**: Tesseract and OCRmyPDF with Ghostscript for scanned documents

- **Containerization**: Docker with Docker Compose orchestration### Docker Deployment (Recommended)

- **Reverse Proxy**: Nginx for frontend serving and API routing

1. **Build the container**:

## 🚀 Quick Start```bash

docker build -t magic-trick-analyzer .

### Prerequisites```



- Docker and Docker Compose2. **Run the service**:

- Git```bash

- 8GB+ RAM (recommended for AI models)docker run -d \

  --name magic-analyzer \

### Installation  -p 8000:8000 \

  -v $(pwd)/data:/app/data \

1. **Clone the repository**:  -v $(pwd)/logs:/app/logs \

```bash  -v $(pwd)/uploads:/app/uploads \

git clone https://github.com/codeiain/Magic-trick-analyzer.git  magic-trick-analyzer

cd Magic-trick-analyzer```

```

3. **Access the service**:

2. **Start the application**:- Review Dashboard: http://localhost:8000/api/v1/review/

```bash- API Documentation: http://localhost:8000/docs

docker-compose up -d- Health Check: http://localhost:8000/health

```

### Local Development

3. **Access the application**:

- **Web Interface**: http://localhost:30001. **Install dependencies**:

- **API Documentation**: http://localhost:8084/docs```bash

- **Health Check**: http://localhost:8084/healthpip install -r requirements.txt

python -m spacy download en_core_web_sm

The first startup may take several minutes as AI models are downloaded and cached.```



## 📱 Usage2. **Run the service**:

```bash

### Uploading Bookspython main.py

```

1. Navigate to the web interface at http://localhost:3000

2. Go to the Books section## Review Interface & Model Training

3. Click "Upload PDF" and select your magic book

4. The system will automatically process the PDF, extract text (with OCR if needed), and detect magic tricks### Web Dashboard

5. View extracted tricks in the Tricks section

Access the review dashboard at http://localhost:8000/api/v1/review/ to:

### Training the Model

- **Review AI Detections**: See all detected tricks with confidence scores

1. Navigate to the **Training** page in the web interface- **Provide Feedback**: Mark detections as correct/incorrect with detailed feedback

2. Review detected tricks and provide feedback:- **Track Performance**: View accuracy statistics and training progress

   - ✅ Mark correct detections- **Train Models**: Start fine-tuning with accumulated feedback data

   - ❌ Mark incorrect detections with explanations

3. Once you have enough training examples (minimum 10), click "Start Training"### Improving AI Accuracy

4. Monitor training progress and model performance metrics

The system learns from your feedback:

### Searching and Browsing

1. **Review Detected Tricks**: Go through AI-detected tricks and rate their accuracy

- **Tricks Page**: Browse all detected tricks with filters for effect type, difficulty, and confidence2. **Provide Corrections**: For incorrect detections, suggest better names/descriptions

- **Books Page**: View your magic library with processing status3. **Accumulate Training Data**: The system builds training examples from your feedback

- **Search**: Use semantic search to find tricks by description, props, or techniques4. **Fine-Tune Models**: Train the AI model with your specific magic book collection



## 🔧 Configuration### Training Workflow



### Environment Variables```bash

# View feedback statistics

Key configuration options (set in docker-compose.yml or environment):curl -X GET "http://localhost:8000/api/v1/review/stats"



```yaml# Submit feedback for a trick

TRANSFORMERS_CACHE: /app/modelscurl -X POST "http://localhost:8000/api/v1/review/feedback" \

SENTENCE_TRANSFORMERS_HOME: /app/models/sentence-transformers  -H "Content-Type: application/json" \

PYTHONUNBUFFERED: 1  -d '{

TOKENIZERS_PARALLELISM: false    "trick_id": "123e4567-e89b-12d3-a456-426614174000",

```    "is_correct": false,

    "suggested_name": "French Drop",

### File Upload Limits    "suggested_description": "Basic coin vanish technique",

    "user_notes": "This is a coin trick, not a card trick"

- **Maximum file size**: 500MB (configurable in nginx.conf)  }'

- **Supported formats**: PDF only

- **OCR timeout**: 5 minutes per file# Start model training

- **Concurrent uploads**: Processed in background queuecurl -X POST "http://localhost:8000/api/v1/review/train"



### AI Model Configuration# Check training status

curl -X GET "http://localhost:8000/api/v1/review/training-status"

The system uses:```

- **Base Model**: `all-MiniLM-L6-v2` for text embeddings

- **Fine-tuning**: Custom model trained on user feedback## API Usage

- **Confidence Threshold**: 0.6 (configurable)

- **Similarity Threshold**: 0.7 for cross-references### Upload and Process a Book



## 🛠️ Development```bash

curl -X POST "http://localhost:8000/api/v1/books/" \

### Project Structure  -H "Content-Type: multipart/form-data" \

  -F "file=@your_magic_book.pdf" \

```  -F "title=The Royal Road to Card Magic" \

magic-trick-analyzer/  -F "author=Roberto Giobbi"

├── backend/                 # FastAPI backend```

│   ├── src/

│   │   ├── application/     # Business logic and use cases### Search for Tricks

│   │   ├── domain/         # Domain models and entities

│   │   ├── infrastructure/ # External services (DB, AI, PDF)```bash

│   │   └── presentation/   # API endpoints and schemascurl -X GET "http://localhost:8000/api/v1/search/tricks?query=card+trick+ambitious&limit=10"

│   ├── config/             # Configuration files```

│   ├── Dockerfile          # Backend container definition

│   └── requirements.txt    # Python dependencies### Find Similar Tricks

├── frontend/               # React frontend

│   ├── src/```bash

│   │   ├── components/     # Reusable UI componentscurl -X GET "http://localhost:8000/api/v1/tricks/{trick_id}/similar?limit=5"

│   │   ├── pages/          # Page components```

│   │   ├── lib/           # Utilities and API client

│   │   └── types/         # TypeScript definitions### Get Cross-References

│   ├── nginx.conf         # Nginx configuration

│   ├── Dockerfile         # Frontend container definition```bash

│   └── package.json       # Node.js dependenciescurl -X GET "http://localhost:8000/api/v1/search/cross-references?technique=double+lift"

├── shared/                # Docker volumes```

│   ├── data/             # SQLite database files

│   ├── logs/             # Application logs## Configuration

│   └── models/           # AI model cache

├── docker-compose.yml    # Docker orchestrationConfiguration can be done via:

└── README.md            # This file

```1. **YAML file** (`config/config.yaml`)

2. **Environment variables**

### API Documentation

### Key Environment Variables

When running, visit http://localhost:8084/docs for interactive API documentation with:

- Complete endpoint reference```bash

- Request/response schemas# Database

- Try-it-out functionalityDATABASE_URL=sqlite:///data/magic_tricks.db



Key API endpoints:# AI Models

- `POST /api/v1/books/upload` - Upload PDF booksAI_MODEL=all-MiniLM-L6-v2

- `GET /api/v1/books/` - List all booksCONFIDENCE_THRESHOLD=0.6

- `GET /api/v1/tricks/` - Search and filter tricksSIMILARITY_THRESHOLD=0.7

- `POST /api/v1/review/feedback` - Provide training feedbackENABLE_FINE_TUNING=true

- `POST /api/v1/review/train` - Start model trainingTRAINING_BATCH_SIZE=16

- `GET /api/v1/review/stats` - Get training statisticsTRAINING_EPOCHS=3



## 🐛 Troubleshooting# API

API_PORT=8000

### Common IssuesAPI_HOST=0.0.0.0



1. **OCR Fails with "gs not found"**:# PDF Processing

   - Ensure Ghostscript is installed in backend containerENABLE_OCR=true

   - Rebuild with: `docker-compose build --no-cache`UPLOAD_DIRECTORY=/app/uploads

```

2. **Large File Upload Fails (413 Error)**:

   - Check nginx file size limits in `frontend/nginx.conf`## Development

   - Current limit: 500MB

### Project Structure

3. **Training Won't Start**:

   - Need minimum 10 training examples with user feedback```

   - Check training statistics at `/api/v1/review/stats`magic-trick-analyzer/

├── src/

4. **AI Models Not Loading**:│   ├── domain/           # Business logic and entities

   - Ensure sufficient RAM (8GB+ recommended)│   ├── application/      # Use cases and services

   - Check model download logs: `docker logs magic-trick-analyzer`│   ├── infrastructure/   # External dependencies

   - Models are cached in `./shared/models/`│   └── presentation/     # API layer

├── tests/               # Test files

### Viewing Logs├── config/              # Configuration files

├── data/                # Database and persistent data

```bash├── logs/                # Application logs

# Backend logs└── Dockerfile

docker logs magic-trick-analyzer -f```



# Frontend logs### Running Tests

docker logs magic-trick-analyzer-frontend -f

```bash

# All container logspython -m pytest tests/ -v

docker-compose logs -f```

```

### Adding New Features

## 🤝 Contributing

1. Start with domain entities and value objects

1. Fork the repository on GitHub2. Define repository interfaces in domain

2. Create a feature branch: `git checkout -b feature/amazing-feature`3. Implement use cases in application layer

3. Make your changes and add tests where applicable4. Add infrastructure implementations

4. Commit your changes: `git commit -m 'Add amazing feature'`5. Expose via presentation layer APIs

5. Push to your branch: `git push origin feature/amazing-feature`

6. Open a Pull Request with a detailed description## AI Models



## 📜 LicenseThe service uses local AI models for privacy and performance:



This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.- **Sentence Transformers**: For semantic similarity and embeddings

- **spaCy**: For natural language processing and entity extraction

## 🙏 Acknowledgments- **PyMuPDF + OCRmyPDF**: For PDF text extraction and OCR



- **FastAPI**: Modern Python web frameworkModels are automatically downloaded and cached on first run.

- **React**: Frontend library

- **Sentence Transformers**: AI embeddings library## Docker Integration

- **Tesseract/OCRmyPDF**: OCR processing

- **PyMuPDF**: PDF text extractionThe service can be integrated with existing Docker Compose setups:

- **TanStack Query**: Data fetching and caching

- **Tailwind CSS**: Utility-first CSS framework```yaml

services:

## 📞 Support  magic-analyzer:

    build: ./magic-trick-analyzer

- **Issues**: [GitHub Issues](https://github.com/codeiain/Magic-trick-analyzer/issues)    ports:

- **Documentation**: http://localhost:8084/docs (when running)      - "8000:8000"
    volumes:
      - ./data/magic-analyzer:/app/data
      - ./logs/magic-analyzer:/app/logs
      - ./uploads:/app/uploads
    environment:
      - DATABASE_URL=sqlite:///data/magic_tricks.db
      - LOG_LEVEL=INFO
```

## Health Monitoring

- Health endpoint: `GET /health`
- Logs: Available in `/app/logs/` directory
- Metrics: Statistics API provides usage metrics

## Security

- No external API calls (privacy-first)
- Non-root container user
- Input validation on all endpoints
- File type restrictions for uploads
- Rate limiting (configurable)

## Performance

- Async processing for file operations
- Model caching for fast inference
- SQLite with proper indexing
- Configurable batch processing

## Contributing

1. Follow hexagonal architecture patterns
2. Maintain SOLID principles
3. Add tests for new functionality
4. Update API documentation
5. Use type hints throughout

## License

[Your License Here]

## Support

- Review Dashboard: http://localhost:8000/api/v1/review/
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Logs: Check `/app/logs/magic_analyzer.log`
