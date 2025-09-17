# Magic Trick Analyzer MCP Server

This is a Model Context Protocol (MCP) server that provides AI assistants with tools to interact with the Magic Trick Analyzer database and system.

## Features

The MCP server provides the following tools:

### Database Tools
- **search_tricks**: Search for magic tricks by name, effect type, description, or difficulty
- **get_trick_details**: Get detailed information about a specific trick including cross-references
- **list_books**: List all processed books in the database
- **get_book_details**: Get detailed information about a book including all its tricks
- **get_cross_references**: Find similar tricks across different books
- **get_stats**: Get database statistics and distribution information

### Search Tools  
- **search_by_description**: Find tricks matching a natural language description of an effect

## Usage

The MCP server runs as a separate Docker container and communicates with AI assistants via the Model Context Protocol standard.

### Available Tools

#### search_tricks
Search for magic tricks with optional filters:
```json
{
  "query": "card prediction",
  "effect_type": "Card", 
  "difficulty": "Intermediate",
  "limit": 10
}
```

#### get_trick_details
Get complete information about a specific trick:
```json
{
  "trick_id": "trick-uuid-here"
}
```

#### list_books
List all books in the database (no parameters required).

#### get_book_details  
Get complete information about a book including all tricks:
```json
{
  "book_id": "book-uuid-here"
}
```

#### get_cross_references
Find similar tricks with similarity threshold:
```json
{
  "trick_id": "trick-uuid-here",
  "min_similarity": 0.7
}
```

#### get_stats
Get database statistics (no parameters required).

#### search_by_description
Find tricks matching a natural language description:
```json
{
  "description": "a trick where a coin vanishes from the magician's hand",
  "limit": 5
}
```

## Docker Configuration

The MCP server runs in its own container with:

- **Read-only access** to the shared database
- **Minimal resource usage** (512MB RAM, 0.5 CPU limit)
- **Isolated environment** with non-root user
- **Health checks** for monitoring
- **Shared logging** with main application

## Environment Variables

- `DATABASE_PATH`: Path to the SQLite database file
- `API_BASE_URL`: URL of the main Magic Trick Analyzer API
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)
- `PYTHONUNBUFFERED`: Python output buffering setting

## Security

- Runs as non-root user (`mcpuser`)
- Read-only access to database
- No external network access required
- Isolated container environment

## Development

To modify the MCP server:

1. Edit `magic_trick_mcp_server.py`
2. Update `requirements.txt` if adding dependencies  
3. Rebuild container: `docker-compose build magic-trick-analyzer-mcp`
4. Restart: `docker-compose up -d magic-trick-analyzer-mcp`

## Monitoring

Check MCP server status:
```bash
# Check container health
docker-compose ps magic-trick-analyzer-mcp

# View logs
docker-compose logs magic-trick-analyzer-mcp

# Check resource usage
docker stats magic-trick-analyzer-mcp
```