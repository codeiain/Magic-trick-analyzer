# Magic Trick Analyzer

An AI-powered system for analyzing and cataloging magic tricks from PDF books. The system extracts text content, identifies magic tricks, and provides a searchable database with training capabilities for improved detection accuracy.

![Magic Trick Analyzer](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![React](https://img.shields.io/badge/React-TypeScript-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen)

## 🎭 Features

- **PDF Processing**: Upload PDF books and extract text content with OCR support
- **AI-Powered Detection**: Automatically identify and categorize magic tricks using sentence transformers
- **Interactive Training**: Train the AI model with user feedback for improved accuracy
- **Searchable Database**: Browse and search through extracted tricks with advanced filtering
- **Modern Web Interface**: React/TypeScript frontend with real-time updates and beautiful UI
- **RESTful API**: FastAPI backend with comprehensive endpoints and automatic documentation
- **Cross-References**: Find similar tricks across different books and authors
- **Statistics Dashboard**: Track model performance and library insights
- **MCP Server Integration**: Model Context Protocol server for AI assistant integration

## 🏗️ Architecture

- **Backend**: FastAPI with Python 3.11
- **Frontend**: React with TypeScript, Vite, and TanStack Query
- **Database**: SQLite with SQLAlchemy ORM
- **AI Models**: Sentence Transformers for text analysis and similarity detection
- **OCR**: Tesseract and OCRmyPDF with Ghostscript for scanned documents
- **Containerization**: Docker with Docker Compose orchestration
- **Reverse Proxy**: Nginx for frontend serving and API routing
- **MCP Server**: Model Context Protocol server for AI assistant integration

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- 8GB+ RAM (recommended for AI models)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/codeiain/Magic-trick-analyzer.git
cd Magic-trick-analyzer
```

2. **Start the application**:
```bash
docker-compose up -d
```

3. **Access the application**:
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8084/docs
- **Health Check**: http://localhost:8084/health

The first startup may take several minutes as AI models are downloaded and cached.

## 📱 Usage

### Uploading Books

1. Navigate to the web interface at http://localhost:3000
2. Go to the Books section
3. Click "Upload PDF" and select your magic book
4. The system will automatically process the PDF, extract text (with OCR if needed), and detect magic tricks
5. View extracted tricks in the Tricks section

### Training the Model

1. Navigate to the **Training** page in the web interface
2. Review detected tricks and provide feedback:
   - ✅ Mark correct detections
   - ❌ Mark incorrect detections with explanations
3. Once you have enough training examples (minimum 10), click "Start Training"
4. Monitor training progress and model performance metrics

### Searching and Browsing

- **Tricks Page**: Browse all detected tricks with filters for effect type, difficulty, and confidence
- **Books Page**: View your magic library with processing status
- **Search**: Use semantic search to find tricks by description, props, or techniques

## 🤖 MCP Server Integration

The Magic Trick Analyzer includes a Model Context Protocol (MCP) server that allows AI assistants to interact with your magic trick database.

### Available Tools

The MCP server provides these tools for AI assistants:

- **search_tricks**: Search for tricks by name, effect type, description, or difficulty
- **get_trick_details**: Get detailed information about a specific trick including cross-references
- **list_books**: List all processed books in the database
- **get_book_details**: Get detailed information about a book including all its tricks
- **get_cross_references**: Find similar tricks across different books
- **get_stats**: Get database statistics and distribution information
- **search_by_description**: Find tricks matching a natural language description

### MCP Server Features

- **Isolated Container**: Runs in its own Docker container for security and stability
- **Read-Only Access**: Only has read access to the database for safety
- **Minimal Resources**: Uses only 512MB RAM and 0.5 CPU by default
- **Health Monitoring**: Includes health checks and logging
- **Standard Protocol**: Compatible with any MCP-enabled AI assistant

### Using the MCP Server

The MCP server automatically starts with the main application:

```bash
# Check MCP server status
docker-compose ps magic-trick-analyzer-mcp

# View MCP server logs
docker-compose logs magic-trick-analyzer-mcp

# Restart MCP server only
docker-compose restart magic-trick-analyzer-mcp
```

AI assistants can connect to the MCP server to:
- Search your magic trick collection
- Get detailed trick information and cross-references
- Analyze your library statistics
- Find tricks matching natural language descriptions
- Browse books and their contents

## 🔧 Configuration

### Environment Variables

Key configuration options (set in docker-compose.yml or environment):

```yaml
TRANSFORMERS_CACHE: /app/models
SENTENCE_TRANSFORMERS_HOME: /app/models/sentence-transformers
PYTHONUNBUFFERED: 1
TOKENIZERS_PARALLELISM: false
```

### File Upload Limits

- **Maximum file size**: 500MB (configurable in nginx.conf)
- **Supported formats**: PDF only
- **OCR timeout**: 5 minutes per file
- **Concurrent uploads**: Processed in background queue

### AI Model Configuration

The system uses:
- **Base Model**: `all-MiniLM-L6-v2` for text embeddings
- **Fine-tuning**: Custom model trained on user feedback
- **Confidence Threshold**: 0.6 (configurable)
- **Similarity Threshold**: 0.7 for cross-references

## 🛠️ Development

### Project Structure

```
magic-trick-analyzer/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── application/     # Business logic and use cases
│   │   ├── domain/         # Domain models and entities
│   │   ├── infrastructure/ # External services (DB, AI, PDF)
│   │   └── presentation/   # API endpoints and schemas
│   ├── config/             # Configuration files
│   ├── Dockerfile          # Backend container definition
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── lib/           # Utilities and API client
│   │   └── types/         # TypeScript definitions
│   ├── nginx.conf         # Nginx configuration
│   ├── Dockerfile         # Frontend container definition
│   └── package.json       # Node.js dependencies
├── mcp-server/            # MCP server
│   ├── magic_trick_mcp_server.py  # MCP server implementation
│   ├── Dockerfile         # MCP container definition
│   ├── requirements.txt   # MCP dependencies
│   └── README.md          # MCP server documentation
├── shared/                # Docker volumes
│   ├── data/             # SQLite database files
│   ├── logs/             # Application logs
│   └── models/           # AI model cache
├── docker-compose.yml    # Docker orchestration
└── README.md            # This file
```

### API Documentation

When running, visit http://localhost:8084/docs for interactive API documentation with:
- Complete endpoint reference
- Request/response schemas
- Try-it-out functionality

Key API endpoints:
- `POST /api/v1/books/upload` - Upload PDF books
- `GET /api/v1/books/` - List all books
- `GET /api/v1/tricks/` - Search and filter tricks
- `POST /api/v1/review/feedback` - Provide training feedback
- `POST /api/v1/review/train` - Start model training
- `GET /api/v1/review/stats` - Get training statistics

## � Training Data Creation

The system includes a comprehensive script to create training data from multiple magic books:

```bash
# Create training data for all supported books
python create_comprehensive_training_data.py

# Create data for specific datasets only
python create_comprehensive_training_data.py --datasets dai_vernon david_roth

# Use custom database path
python create_comprehensive_training_data.py --db-path custom_path.db
```

### Supported Datasets

- **dai_vernon**: The Dai Vernon Book of Magic (1957)
- **david_roth**: Expert Coin Magic (1982)
- **hugard**: Coin Magic by Jean Hugard (1954)
- **mentalism**: Encyclopedic Dictionary of Mentalism - Volume 3 (2005)

The script automatically:
- Creates database tables if they don't exist
- Inserts book and trick data
- Creates cross-references between similar tricks
- Provides verification and statistics

## �🐛 Troubleshooting

### Common Issues

1. **OCR Fails with "gs not found"**:
   - Ensure Ghostscript is installed in backend container
   - Rebuild with: `docker-compose build --no-cache`

2. **Large File Upload Fails (413 Error)**:
   - Check nginx file size limits in `frontend/nginx.conf`
   - Current limit: 500MB

3. **Training Won't Start**:
   - Need minimum 10 training examples with user feedback
   - Check training statistics at `/api/v1/review/stats`

4. **AI Models Not Loading**:
   - Ensure sufficient RAM (8GB+ recommended)
   - Check model download logs: `docker logs magic-trick-analyzer`
   - Models are cached in `./shared/models/`

5. **MCP Server Not Responding**:
   - Check MCP server logs: `docker logs magic-trick-analyzer-mcp`
   - Verify database access: ensure `./shared/data/` contains database files
   - Restart MCP server: `docker-compose restart magic-trick-analyzer-mcp`

### Viewing Logs

```bash
# Backend logs
docker logs magic-trick-analyzer -f

# Frontend logs
docker logs magic-trick-analyzer-frontend -f

# MCP server logs
docker logs magic-trick-analyzer-mcp -f

# All container logs
docker-compose logs -f
```

## 🤝 Contributing

1. Fork the repository on GitHub
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests where applicable
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to your branch: `git push origin feature/amazing-feature`
6. Open a Pull Request with a detailed description

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI**: Modern Python web framework
- **React**: Frontend library
- **Sentence Transformers**: AI embeddings library
- **Tesseract/OCRmyPDF**: OCR processing
- **PyMuPDF**: PDF text extraction
- **TanStack Query**: Data fetching and caching
- **Tailwind CSS**: Utility-first CSS framework
- **Model Context Protocol**: AI assistant integration standard

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/codeiain/Magic-trick-analyzer/issues)
- **Documentation**: http://localhost:8084/docs (when running)
- **MCP Server**: See `mcp-server/README.md` for detailed MCP integration guide