"""
Magic Trick Analyzer MCP Server

This MCP server provides tools for analyzing and managing magic tricks from PDF books,
integrating with the Magic Trick Analyzer backend system.

Available tools:
- search_tricks: Search for magic tricks by name, effect type, or description
- get_trick_details: Get detailed information about a specific trick
- list_books: List all processed books in the database
- get_book_details: Get details about a specific book including tricks
- analyze_pdf: Process and analyze a new PDF book
- get_cross_references: Find similar tricks across different books
- get_training_stats: Get current training statistics and model performance
- provide_feedback: Provide training feedback on trick detection
- search_by_similarity: Find tricks similar to a given description using AI
"""

import asyncio
import logging
import sqlite3
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from pydantic import AnyUrl

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("magic-trick-mcp-server")

# Server configuration
server = Server("magic-trick-analyzer")

# Database connection settings
DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/magic_tricks.db")
API_BASE_URL = os.getenv("API_BASE_URL", "http://magic-trick-analyzer:8000")

class MagicTrickDatabase:
    """Database interface for Magic Trick Analyzer"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def get_connection(self):
        """Get database connection"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
        return sqlite3.connect(self.db_path)
    
    def search_tricks(self, query: str = None, effect_type: str = None, 
                     difficulty: str = None, limit: int = 10) -> List[Dict]:
        """Search for tricks based on criteria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        sql = """
        SELECT t.id, t.name, t.effect_type, t.description, t.difficulty, 
               t.props, t.page_start, t.page_end, t.confidence,
               b.title as book_title, b.author as book_author
        FROM tricks t
        JOIN books b ON t.book_id = b.id
        WHERE 1=1
        """
        params = []
        
        if query:
            sql += " AND (t.name LIKE ? OR t.description LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
            
        if effect_type:
            sql += " AND t.effect_type = ?"
            params.append(effect_type)
            
        if difficulty:
            sql += " AND t.difficulty = ?"
            params.append(difficulty)
            
        sql += " ORDER BY t.confidence DESC, t.name ASC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            trick = dict(zip(columns, row))
            # Parse props if it exists
            if trick['props']:
                try:
                    trick['props'] = json.loads(trick['props'])
                except json.JSONDecodeError:
                    trick['props'] = []
            else:
                trick['props'] = []
            results.append(trick)
            
        conn.close()
        return results
    
    def get_trick_details(self, trick_id: str) -> Optional[Dict]:
        """Get detailed information about a specific trick"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT t.*, b.title as book_title, b.author as book_author, 
               b.publication_year, b.isbn
        FROM tricks t
        JOIN books b ON t.book_id = b.id
        WHERE t.id = ?
        """, (trick_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
            
        columns = [desc[0] for desc in cursor.description]
        trick = dict(zip(columns, row))
        
        # Parse props if it exists
        if trick['props']:
            try:
                trick['props'] = json.loads(trick['props'])
            except json.JSONDecodeError:
                trick['props'] = []
        else:
            trick['props'] = []
            
        # Get cross-references
        cursor.execute("""
        SELECT cr.relationship_type, cr.similarity_score,
               t2.id as related_trick_id, t2.name as related_trick_name,
               b2.title as related_book_title
        FROM cross_references cr
        JOIN tricks t2 ON cr.target_trick_id = t2.id
        JOIN books b2 ON t2.book_id = b2.id
        WHERE cr.source_trick_id = ?
        """, (trick_id,))
        
        cross_refs = []
        for row in cursor.fetchall():
            cross_refs.append({
                'relationship_type': row[0],
                'similarity_score': row[1],
                'related_trick_id': row[2],
                'related_trick_name': row[3],
                'related_book_title': row[4]
            })
            
        trick['cross_references'] = cross_refs
        conn.close()
        return trick
    
    def list_books(self) -> List[Dict]:
        """List all books in the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT b.*, COUNT(t.id) as trick_count
        FROM books b
        LEFT JOIN tricks t ON b.id = t.book_id
        GROUP BY b.id
        ORDER BY b.title
        """)
        
        columns = [desc[0] for desc in cursor.description]
        books = []
        
        for row in cursor.fetchall():
            book = dict(zip(columns, row))
            books.append(book)
            
        conn.close()
        return books
    
    def get_book_details(self, book_id: str) -> Optional[Dict]:
        """Get detailed information about a specific book"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
            
        columns = [desc[0] for desc in cursor.description]
        book = dict(zip(columns, row))
        
        # Get tricks for this book
        cursor.execute("""
        SELECT id, name, effect_type, difficulty, confidence, page_start, page_end
        FROM tricks 
        WHERE book_id = ?
        ORDER BY page_start ASC, name ASC
        """, (book_id,))
        
        tricks = []
        for row in cursor.fetchall():
            trick_cols = [desc[0] for desc in cursor.description]
            trick = dict(zip(trick_cols, row))
            tricks.append(trick)
            
        book['tricks'] = tricks
        conn.close()
        return book

# Initialize database
db = MagicTrickDatabase(DATABASE_PATH)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for magic trick analysis"""
    return [
        types.Tool(
            name="search_tricks",
            description="Search for magic tricks by name, effect type, description, or difficulty level",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for trick name or description"
                    },
                    "effect_type": {
                        "type": "string", 
                        "description": "Filter by effect type (e.g., 'Card', 'Coin', 'Mentalism')"
                    },
                    "difficulty": {
                        "type": "string",
                        "description": "Filter by difficulty level (e.g., 'Beginner', 'Intermediate', 'Advanced')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10
                    }
                }
            }
        ),
        types.Tool(
            name="get_trick_details",
            description="Get detailed information about a specific magic trick including cross-references",
            inputSchema={
                "type": "object",
                "properties": {
                    "trick_id": {
                        "type": "string",
                        "description": "The unique ID of the trick to retrieve"
                    }
                },
                "required": ["trick_id"]
            }
        ),
        types.Tool(
            name="list_books",
            description="List all processed books in the magic trick database",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_book_details",
            description="Get detailed information about a specific book including all its tricks",
            inputSchema={
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "string",
                        "description": "The unique ID of the book to retrieve"
                    }
                },
                "required": ["book_id"]
            }
        ),
        types.Tool(
            name="get_cross_references",
            description="Find similar tricks across different books for a given trick",
            inputSchema={
                "type": "object",
                "properties": {
                    "trick_id": {
                        "type": "string",
                        "description": "The ID of the trick to find cross-references for"
                    },
                    "min_similarity": {
                        "type": "number",
                        "description": "Minimum similarity score (0.0-1.0, default: 0.7)",
                        "default": 0.7
                    }
                },
                "required": ["trick_id"]
            }
        ),
        types.Tool(
            name="get_stats",
            description="Get database statistics including book count, trick count, and distribution by categories",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="search_by_description",
            description="Find tricks that match a natural language description of an effect or method",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Natural language description of the magic effect you're looking for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 5)",
                        "default": 5
                    }
                },
                "required": ["description"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Handle tool execution"""
    if arguments is None:
        arguments = {}
        
    try:
        if name == "search_tricks":
            results = db.search_tricks(
                query=arguments.get("query"),
                effect_type=arguments.get("effect_type"),
                difficulty=arguments.get("difficulty"),
                limit=arguments.get("limit", 10)
            )
            
            if not results:
                return [types.TextContent(
                    type="text",
                    text="No tricks found matching your criteria."
                )]
            
            output = f"Found {len(results)} magic tricks:\n\n"
            for trick in results:
                output += f"**{trick['name']}** ({trick['effect_type']})\n"
                output += f"Book: {trick['book_title']} by {trick['book_author']}\n"
                output += f"Difficulty: {trick['difficulty']}\n"
                if trick['confidence']:
                    output += f"Confidence: {trick['confidence']:.2f}\n"
                if trick['page_start']:
                    page_info = f"Page {trick['page_start']}"
                    if trick['page_end'] and trick['page_end'] != trick['page_start']:
                        page_info += f"-{trick['page_end']}"
                    output += f"{page_info}\n"
                output += f"Description: {trick['description'][:200]}...\n"
                if trick['props']:
                    output += f"Props: {', '.join(trick['props'])}\n"
                output += f"ID: {trick['id']}\n\n"
                
            return [types.TextContent(type="text", text=output)]
            
        elif name == "get_trick_details":
            trick_id = arguments.get("trick_id")
            if not trick_id:
                return [types.TextContent(
                    type="text",
                    text="Error: trick_id is required"
                )]
                
            trick = db.get_trick_details(trick_id)
            if not trick:
                return [types.TextContent(
                    type="text",
                    text=f"No trick found with ID: {trick_id}"
                )]
            
            output = f"**{trick['name']}**\n"
            output += f"Effect Type: {trick['effect_type']}\n"
            output += f"Difficulty: {trick['difficulty']}\n"
            output += f"Book: {trick['book_title']} by {trick['book_author']}\n"
            if trick['publication_year']:
                output += f"Published: {trick['publication_year']}\n"
            if trick['page_start']:
                page_info = f"Page {trick['page_start']}"
                if trick['page_end'] and trick['page_end'] != trick['page_start']:
                    page_info += f"-{trick['page_end']}"
                output += f"{page_info}\n"
            if trick['confidence']:
                output += f"Detection Confidence: {trick['confidence']:.2f}\n"
            output += f"\n**Description:**\n{trick['description']}\n"
            
            if trick['method']:
                output += f"\n**Method:**\n{trick['method']}\n"
            
            if trick['props']:
                output += f"\n**Required Props:**\n{', '.join(trick['props'])}\n"
            
            if trick['cross_references']:
                output += f"\n**Similar Tricks:**\n"
                for ref in trick['cross_references']:
                    output += f"- {ref['related_trick_name']} ({ref['related_book_title']})"
                    if ref['similarity_score']:
                        output += f" - Similarity: {ref['similarity_score']:.2f}"
                    output += f" - Relationship: {ref['relationship_type']}\n"
            
            return [types.TextContent(type="text", text=output)]
            
        elif name == "list_books":
            books = db.list_books()
            if not books:
                return [types.TextContent(
                    type="text",
                    text="No books found in the database."
                )]
            
            output = f"Found {len(books)} books:\n\n"
            for book in books:
                output += f"**{book['title']}** by {book['author']}\n"
                if book['publication_year']:
                    output += f"Published: {book['publication_year']}\n"
                output += f"Tricks: {book['trick_count']}\n"
                if book['processed_at']:
                    output += f"Processed: {book['processed_at']}\n"
                output += f"ID: {book['id']}\n\n"
                
            return [types.TextContent(type="text", text=output)]
            
        elif name == "get_book_details":
            book_id = arguments.get("book_id")
            if not book_id:
                return [types.TextContent(
                    type="text",
                    text="Error: book_id is required"
                )]
                
            book = db.get_book_details(book_id)
            if not book:
                return [types.TextContent(
                    type="text",
                    text=f"No book found with ID: {book_id}"
                )]
            
            output = f"**{book['title']}**\n"
            output += f"Author: {book['author']}\n"
            if book['publication_year']:
                output += f"Published: {book['publication_year']}\n"
            if book['isbn']:
                output += f"ISBN: {book['isbn']}\n"
            if book['processed_at']:
                output += f"Processed: {book['processed_at']}\n"
            
            output += f"\n**Tricks in this book ({len(book['tricks'])}):**\n\n"
            for trick in book['tricks']:
                output += f"• **{trick['name']}** ({trick['effect_type']})\n"
                output += f"  Difficulty: {trick['difficulty']}"
                if trick['confidence']:
                    output += f" | Confidence: {trick['confidence']:.2f}"
                if trick['page_start']:
                    page_info = f" | Page {trick['page_start']}"
                    if trick['page_end'] and trick['page_end'] != trick['page_start']:
                        page_info += f"-{trick['page_end']}"
                    output += page_info
                output += f"\n  ID: {trick['id']}\n\n"
                
            return [types.TextContent(type="text", text=output)]
            
        elif name == "get_cross_references":
            trick_id = arguments.get("trick_id")
            min_similarity = arguments.get("min_similarity", 0.7)
            
            if not trick_id:
                return [types.TextContent(
                    type="text",
                    text="Error: trick_id is required"
                )]
                
            # Get the trick details first
            trick = db.get_trick_details(trick_id)
            if not trick:
                return [types.TextContent(
                    type="text",
                    text=f"No trick found with ID: {trick_id}"
                )]
            
            # Filter cross-references by similarity threshold
            filtered_refs = [
                ref for ref in trick['cross_references'] 
                if ref['similarity_score'] and ref['similarity_score'] >= min_similarity
            ]
            
            if not filtered_refs:
                return [types.TextContent(
                    type="text",
                    text=f"No cross-references found for '{trick['name']}' with similarity >= {min_similarity}"
                )]
            
            output = f"**Cross-references for '{trick['name']}'** (similarity >= {min_similarity}):\n\n"
            for ref in filtered_refs:
                output += f"• **{ref['related_trick_name']}**\n"
                output += f"  Book: {ref['related_book_title']}\n"
                output += f"  Similarity: {ref['similarity_score']:.3f}\n"
                output += f"  Relationship: {ref['relationship_type']}\n"
                output += f"  ID: {ref['related_trick_id']}\n\n"
                
            return [types.TextContent(type="text", text=output)]
            
        elif name == "get_stats":
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Get basic counts
            cursor.execute("SELECT COUNT(*) FROM books")
            book_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tricks")
            trick_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cross_references")
            cross_ref_count = cursor.fetchone()[0]
            
            # Get effect type distribution
            cursor.execute("""
            SELECT effect_type, COUNT(*) as count
            FROM tricks
            GROUP BY effect_type
            ORDER BY count DESC
            """)
            effect_types = cursor.fetchall()
            
            # Get difficulty distribution
            cursor.execute("""
            SELECT difficulty, COUNT(*) as count
            FROM tricks
            GROUP BY difficulty
            ORDER BY count DESC
            """)
            difficulties = cursor.fetchall()
            
            # Get average confidence
            cursor.execute("SELECT AVG(confidence) FROM tricks WHERE confidence IS NOT NULL")
            avg_confidence = cursor.fetchone()[0]
            
            conn.close()
            
            output = "**Magic Trick Analyzer Database Statistics**\n\n"
            output += f"📚 Books: {book_count}\n"
            output += f"🎭 Tricks: {trick_count}\n"
            output += f"🔗 Cross-references: {cross_ref_count}\n"
            if avg_confidence:
                output += f"📊 Average Detection Confidence: {avg_confidence:.3f}\n"
            
            output += f"\n**Effect Types:**\n"
            for effect_type, count in effect_types:
                output += f"• {effect_type}: {count}\n"
            
            output += f"\n**Difficulty Levels:**\n"
            for difficulty, count in difficulties:
                output += f"• {difficulty}: {count}\n"
                
            return [types.TextContent(type="text", text=output)]
            
        elif name == "search_by_description":
            description = arguments.get("description")
            limit = arguments.get("limit", 5)
            
            if not description:
                return [types.TextContent(
                    type="text",
                    text="Error: description is required"
                )]
            
            # Simple text-based search for now (could be enhanced with AI similarity)
            results = db.search_tricks(query=description, limit=limit)
            
            if not results:
                return [types.TextContent(
                    type="text",
                    text=f"No tricks found matching the description: '{description}'"
                )]
            
            output = f"Found {len(results)} tricks matching '{description}':\n\n"
            for trick in results:
                output += f"**{trick['name']}** ({trick['effect_type']})\n"
                output += f"Book: {trick['book_title']} by {trick['book_author']}\n"
                output += f"Difficulty: {trick['difficulty']}\n"
                if trick['confidence']:
                    output += f"Confidence: {trick['confidence']:.2f}\n"
                output += f"Description: {trick['description'][:150]}...\n"
                output += f"ID: {trick['id']}\n\n"
                
            return [types.TextContent(type="text", text=output)]
            
        else:
            return [types.TextContent(
                type="text", 
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]

async def main():
    """Run the MCP server"""
    # Use stdin/stdout for communication
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="magic-trick-analyzer",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())