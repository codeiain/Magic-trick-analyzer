"""
Unit tests for Magic Trick MCP Server

Tests the MCP server functionality including database operations
and tool handlers for magic trick analysis.
"""

import pytest
import sqlite3
import tempfile
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

import mcp.types as types
from magic_trick_mcp_server import MagicTrickDatabase, server, handle_call_tool, handle_list_tools


class TestMagicTrickDatabase:
    """Test cases for MagicTrickDatabase class"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        db_path = temp_file.name
        temp_file.close()
        
        # Create test database schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create test tables
        cursor.execute('''
        CREATE TABLE books (
            id TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            publication_year INTEGER,
            isbn TEXT,
            processed_at TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE tricks (
            id TEXT PRIMARY KEY,
            name TEXT,
            description TEXT,
            method TEXT,
            effect_type TEXT,
            difficulty TEXT,
            props TEXT,
            page_start INTEGER,
            page_end INTEGER,
            confidence REAL,
            book_id TEXT,
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE cross_references (
            id INTEGER PRIMARY KEY,
            source_trick_id TEXT,
            target_trick_id TEXT,
            relationship_type TEXT,
            similarity_score REAL,
            FOREIGN KEY (source_trick_id) REFERENCES tricks (id),
            FOREIGN KEY (target_trick_id) REFERENCES tricks (id)
        )
        ''')
        
        # Insert test data
        cursor.execute('''
        INSERT INTO books (id, title, author, publication_year, isbn, processed_at)
        VALUES ('book_1', 'Magic Fundamentals', 'John Doe', 2020, '978-1234567890', '2023-01-01')
        ''')
        
        cursor.execute('''
        INSERT INTO books (id, title, author, publication_year, isbn, processed_at)
        VALUES ('book_2', 'Advanced Magic', 'Jane Smith', 2021, '978-0987654321', '2023-01-02')
        ''')
        
        cursor.execute('''
        INSERT INTO tricks (id, name, description, method, effect_type, difficulty, props, 
                          page_start, page_end, confidence, book_id)
        VALUES ('trick_1', 'Card Force', 'Force a specific card on spectator', 'Use Hindu shuffle', 
                'Card', 'Beginner', '["deck of cards"]', 10, 12, 0.9, 'book_1')
        ''')
        
        cursor.execute('''
        INSERT INTO tricks (id, name, description, method, effect_type, difficulty, props,
                          page_start, page_end, confidence, book_id)
        VALUES ('trick_2', 'Coin Vanish', 'Make coin disappear', 'French drop', 
                'Coin', 'Intermediate', '["coin"]', 25, 27, 0.8, 'book_1')
        ''')
        
        cursor.execute('''
        INSERT INTO tricks (id, name, description, method, effect_type, difficulty, props,
                          page_start, page_end, confidence, book_id)
        VALUES ('trick_3', 'Advanced Card Control', 'Control card position', 'Complex shuffle', 
                'Card', 'Advanced', '["deck of cards"]', 5, 8, 0.85, 'book_2')
        ''')
        
        cursor.execute('''
        INSERT INTO cross_references (source_trick_id, target_trick_id, relationship_type, similarity_score)
        VALUES ('trick_1', 'trick_3', 'similar', 0.75)
        ''')
        
        conn.commit()
        conn.close()
        
        yield db_path
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def db(self, temp_db):
        """Create database instance with test data"""
        return MagicTrickDatabase(temp_db)

    def test_init_with_valid_path(self, temp_db):
        """Test database initialization with valid path"""
        db = MagicTrickDatabase(temp_db)
        assert db.db_path == temp_db

    def test_get_connection_success(self, db):
        """Test successful database connection"""
        conn = db.get_connection()
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_connection_file_not_found(self):
        """Test database connection with non-existent file"""
        db = MagicTrickDatabase("/nonexistent/path.db")
        with pytest.raises(FileNotFoundError):
            db.get_connection()

    def test_search_tricks_no_filters(self, db):
        """Test searching tricks without filters"""
        results = db.search_tricks()
        assert len(results) == 3
        assert all('id' in result for result in results)
        assert all('name' in result for result in results)

    def test_search_tricks_with_query(self, db):
        """Test searching tricks with query filter"""
        results = db.search_tricks(query="card")
        assert len(results) == 2  # Should find both card tricks
        assert all('card' in result['name'].lower() or 'card' in result['description'].lower() 
                  for result in results)

    def test_search_tricks_with_effect_type(self, db):
        """Test searching tricks with effect type filter"""
        results = db.search_tricks(effect_type="Card")
        assert len(results) == 2
        assert all(result['effect_type'] == 'Card' for result in results)

    def test_search_tricks_with_difficulty(self, db):
        """Test searching tricks with difficulty filter"""
        results = db.search_tricks(difficulty="Beginner")
        assert len(results) == 1
        assert results[0]['difficulty'] == 'Beginner'

    def test_search_tricks_with_limit(self, db):
        """Test searching tricks with result limit"""
        results = db.search_tricks(limit=1)
        assert len(results) == 1

    def test_search_tricks_combined_filters(self, db):
        """Test searching tricks with multiple filters"""
        results = db.search_tricks(query="card", effect_type="Card", difficulty="Beginner")
        assert len(results) == 1
        assert results[0]['name'] == 'Card Force'

    def test_search_tricks_props_parsing(self, db):
        """Test that props are properly parsed from JSON"""
        results = db.search_tricks(query="Card Force")
        assert len(results) == 1
        assert results[0]['props'] == ["deck of cards"]

    def test_search_tricks_invalid_props(self, db):
        """Test handling of invalid JSON in props"""
        # Manually insert trick with invalid JSON props
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO tricks (id, name, props, book_id)
        VALUES ('trick_bad_props', 'Test Trick', 'invalid json', 'book_1')
        ''')
        conn.commit()
        conn.close()
        
        results = db.search_tricks(query="Test Trick")
        assert len(results) == 1
        assert results[0]['props'] == []  # Should default to empty list

    def test_get_trick_details_success(self, db):
        """Test getting trick details successfully"""
        result = db.get_trick_details('trick_1')
        
        assert result is not None
        assert result['id'] == 'trick_1'
        assert result['name'] == 'Card Force'
        assert result['book_title'] == 'Magic Fundamentals'
        assert result['book_author'] == 'John Doe'
        assert 'cross_references' in result

    def test_get_trick_details_with_cross_references(self, db):
        """Test getting trick details with cross-references"""
        result = db.get_trick_details('trick_1')
        
        assert len(result['cross_references']) == 1
        cross_ref = result['cross_references'][0]
        assert cross_ref['relationship_type'] == 'similar'
        assert cross_ref['similarity_score'] == 0.75
        assert cross_ref['related_trick_name'] == 'Advanced Card Control'

    def test_get_trick_details_not_found(self, db):
        """Test getting details for non-existent trick"""
        result = db.get_trick_details('nonexistent_trick')
        assert result is None

    def test_list_books_success(self, db):
        """Test listing books successfully"""
        results = db.list_books()
        
        assert len(results) == 2
        assert results[0]['title'] == 'Advanced Magic'  # Sorted by title
        assert results[1]['title'] == 'Magic Fundamentals'
        assert all('trick_count' in book for book in results)

    def test_list_books_with_trick_counts(self, db):
        """Test that book listing includes correct trick counts"""
        results = db.list_books()
        
        book_1 = next(book for book in results if book['id'] == 'book_1')
        book_2 = next(book for book in results if book['id'] == 'book_2')
        
        assert book_1['trick_count'] == 2  # Has 2 tricks
        assert book_2['trick_count'] == 1  # Has 1 trick

    def test_get_book_details_success(self, db):
        """Test getting book details successfully"""
        result = db.get_book_details('book_1')
        
        assert result is not None
        assert result['id'] == 'book_1'
        assert result['title'] == 'Magic Fundamentals'
        assert len(result['tricks']) == 2

    def test_get_book_details_tricks_sorted(self, db):
        """Test that book details include properly sorted tricks"""
        result = db.get_book_details('book_1')
        
        tricks = result['tricks']
        # Should be sorted by page_start, then name
        assert tricks[0]['page_start'] <= tricks[1]['page_start']

    def test_get_book_details_not_found(self, db):
        """Test getting details for non-existent book"""
        result = db.get_book_details('nonexistent_book')
        assert result is None


class TestMCPToolHandlers:
    """Test cases for MCP tool handlers"""

    @pytest.fixture
    def mock_db(self):
        """Mock database for testing tool handlers"""
        mock_db = Mock()
        return mock_db

    @pytest.mark.asyncio
    async def test_handle_list_tools(self):
        """Test listing available MCP tools"""
        tools = await handle_list_tools()
        
        assert len(tools) == 7  # Expected number of tools
        tool_names = [tool.name for tool in tools]
        
        expected_tools = [
            'search_tricks', 'get_trick_details', 'list_books', 
            'get_book_details', 'get_cross_references', 'get_stats',
            'search_by_description'
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_handle_list_tools_schema_validation(self):
        """Test that tool schemas are properly structured"""
        tools = await handle_list_tools()
        
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            assert 'type' in tool.inputSchema
            assert tool.inputSchema['type'] == 'object'

    @pytest.mark.asyncio
    async def test_search_tricks_tool_success(self, mock_db):
        """Test search_tricks tool with successful results"""
        mock_results = [
            {
                'id': 'trick_1',
                'name': 'Card Force',
                'effect_type': 'Card',
                'description': 'Force a specific card',
                'difficulty': 'Beginner',
                'confidence': 0.9,
                'page_start': 10,
                'page_end': 12,
                'props': ['deck of cards'],
                'book_title': 'Magic Book',
                'book_author': 'Author'
            }
        ]
        
        with patch('magic_trick_mcp_server.db', mock_db):
            mock_db.search_tricks.return_value = mock_results
            
            result = await handle_call_tool('search_tricks', {'query': 'card'})
            
            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)
            content = result[0].text
            assert 'Card Force' in content
            assert 'Magic Book' in content

    @pytest.mark.asyncio
    async def test_search_tricks_tool_no_results(self, mock_db):
        """Test search_tricks tool with no results"""
        with patch('magic_trick_mcp_server.db', mock_db):
            mock_db.search_tricks.return_value = []
            
            result = await handle_call_tool('search_tricks', {'query': 'nonexistent'})
            
            assert len(result) == 1
            content = result[0].text
            assert 'No tricks found' in content

    @pytest.mark.asyncio
    async def test_get_trick_details_tool_success(self, mock_db):
        """Test get_trick_details tool with successful result"""
        mock_trick = {
            'id': 'trick_1',
            'name': 'Card Force',
            'effect_type': 'Card',
            'description': 'Detailed description',
            'method': 'Method details',
            'difficulty': 'Beginner',
            'props': ['deck'],
            'confidence': 0.9,
            'page_start': 10,
            'page_end': 12,
            'book_title': 'Magic Book',
            'book_author': 'Author',
            'publication_year': 2020,
            'cross_references': [
                {
                    'related_trick_name': 'Similar Trick',
                    'related_book_title': 'Another Book',
                    'similarity_score': 0.8,
                    'relationship_type': 'similar'
                }
            ]
        }
        
        with patch('magic_trick_mcp_server.db', mock_db):
            mock_db.get_trick_details.return_value = mock_trick
            
            result = await handle_call_tool('get_trick_details', {'trick_id': 'trick_1'})
            
            assert len(result) == 1
            content = result[0].text
            assert 'Card Force' in content
            assert 'Detailed description' in content
            assert 'Method details' in content
            assert 'Similar Tricks:' in content

    @pytest.mark.asyncio
    async def test_get_trick_details_tool_not_found(self, mock_db):
        """Test get_trick_details tool with non-existent trick"""
        with patch('magic_trick_mcp_server.db', mock_db):
            mock_db.get_trick_details.return_value = None
            
            result = await handle_call_tool('get_trick_details', {'trick_id': 'nonexistent'})
            
            assert len(result) == 1
            content = result[0].text
            assert 'No trick found' in content

    @pytest.mark.asyncio
    async def test_get_trick_details_tool_missing_id(self):
        """Test get_trick_details tool with missing trick_id"""
        result = await handle_call_tool('get_trick_details', {})
        
        assert len(result) == 1
        content = result[0].text
        assert 'trick_id is required' in content

    @pytest.mark.asyncio
    async def test_list_books_tool_success(self, mock_db):
        """Test list_books tool with successful results"""
        mock_books = [
            {
                'id': 'book_1',
                'title': 'Magic Book',
                'author': 'Author',
                'publication_year': 2020,
                'trick_count': 5,
                'processed_at': '2023-01-01'
            }
        ]
        
        with patch('magic_trick_mcp_server.db', mock_db):
            mock_db.list_books.return_value = mock_books
            
            result = await handle_call_tool('list_books', {})
            
            assert len(result) == 1
            content = result[0].text
            assert 'Magic Book' in content
            assert 'Tricks: 5' in content

    @pytest.mark.asyncio
    async def test_get_book_details_tool_success(self, mock_db):
        """Test get_book_details tool with successful result"""
        mock_book = {
            'id': 'book_1',
            'title': 'Magic Book',
            'author': 'Author',
            'publication_year': 2020,
            'isbn': '978-1234567890',
            'processed_at': '2023-01-01',
            'tricks': [
                {
                    'id': 'trick_1',
                    'name': 'Card Force',
                    'effect_type': 'Card',
                    'difficulty': 'Beginner',
                    'confidence': 0.9,
                    'page_start': 10,
                    'page_end': 12
                }
            ]
        }
        
        with patch('magic_trick_mcp_server.db', mock_db):
            mock_db.get_book_details.return_value = mock_book
            
            result = await handle_call_tool('get_book_details', {'book_id': 'book_1'})
            
            assert len(result) == 1
            content = result[0].text
            assert 'Magic Book' in content
            assert 'Card Force' in content
            assert 'Tricks in this book (1):' in content

    @pytest.mark.asyncio
    async def test_get_cross_references_tool_success(self, mock_db):
        """Test get_cross_references tool with successful result"""
        mock_trick = {
            'id': 'trick_1',
            'name': 'Source Trick',
            'cross_references': [
                {
                    'related_trick_name': 'Similar Trick',
                    'related_book_title': 'Another Book',
                    'similarity_score': 0.8,
                    'relationship_type': 'similar',
                    'related_trick_id': 'trick_2'
                }
            ]
        }
        
        with patch('magic_trick_mcp_server.db', mock_db):
            mock_db.get_trick_details.return_value = mock_trick
            
            result = await handle_call_tool('get_cross_references', 
                                          {'trick_id': 'trick_1', 'min_similarity': 0.7})
            
            assert len(result) == 1
            content = result[0].text
            assert 'Cross-references for' in content
            assert 'Similar Trick' in content
            assert 'Similarity: 0.800' in content

    @pytest.mark.asyncio
    async def test_get_cross_references_tool_no_results(self, mock_db):
        """Test get_cross_references tool with no high-similarity results"""
        mock_trick = {
            'id': 'trick_1',
            'name': 'Source Trick',
            'cross_references': [
                {
                    'similarity_score': 0.5,  # Below threshold
                    'relationship_type': 'similar'
                }
            ]
        }
        
        with patch('magic_trick_mcp_server.db', mock_db):
            mock_db.get_trick_details.return_value = mock_trick
            
            result = await handle_call_tool('get_cross_references',
                                          {'trick_id': 'trick_1', 'min_similarity': 0.7})
            
            assert len(result) == 1
            content = result[0].text
            assert 'No cross-references found' in content

    @pytest.mark.asyncio
    async def test_get_stats_tool_success(self):
        """Test get_stats tool with database statistics"""
        with patch('magic_trick_mcp_server.db') as mock_db_instance:
            # Mock database connection and cursor
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_db_instance.get_connection.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Mock query results
            mock_cursor.fetchone.side_effect = [
                (10,),      # book count
                (50,),      # trick count  
                (25,),      # cross-reference count
                (0.85,)     # average confidence
            ]
            
            mock_cursor.fetchall.side_effect = [
                [('Card', 20), ('Coin', 15), ('Mentalism', 10)],  # effect types
                [('Beginner', 15), ('Intermediate', 20), ('Advanced', 15)]  # difficulties
            ]
            
            result = await handle_call_tool('get_stats', {})
            
            assert len(result) == 1
            content = result[0].text
            assert 'Books: 10' in content
            assert 'Tricks: 50' in content
            assert 'Cross-references: 25' in content
            assert 'Card: 20' in content
            assert 'Beginner: 15' in content

    @pytest.mark.asyncio
    async def test_search_by_description_tool_success(self, mock_db):
        """Test search_by_description tool"""
        mock_results = [
            {
                'id': 'trick_1',
                'name': 'Card Vanish',
                'effect_type': 'Card',
                'description': 'Make a card disappear',
                'difficulty': 'Intermediate',
                'confidence': 0.8,
                'book_title': 'Magic Book',
                'book_author': 'Author'
            }
        ]
        
        with patch('magic_trick_mcp_server.db', mock_db):
            mock_db.search_tricks.return_value = mock_results
            
            result = await handle_call_tool('search_by_description', 
                                          {'description': 'make something vanish'})
            
            assert len(result) == 1
            content = result[0].text
            assert 'Card Vanish' in content

    @pytest.mark.asyncio
    async def test_unknown_tool_error(self):
        """Test handling of unknown tool name"""
        result = await handle_call_tool('unknown_tool', {})
        
        assert len(result) == 1
        content = result[0].text
        assert 'Unknown tool' in content

    @pytest.mark.asyncio
    async def test_tool_exception_handling(self, mock_db):
        """Test that tool exceptions are properly handled"""
        with patch('magic_trick_mcp_server.db', mock_db):
            mock_db.search_tricks.side_effect = Exception("Database error")
            
            result = await handle_call_tool('search_tricks', {'query': 'test'})
            
            assert len(result) == 1
            content = result[0].text
            assert 'Error executing search_tricks' in content
            assert 'Database error' in content


class TestMCPServerIntegration:
    """Integration tests for MCP server functionality"""

    @pytest.mark.asyncio
    async def test_full_search_workflow(self):
        """Test complete search workflow from tool to database"""
        # This would be a more comprehensive integration test
        # that tests the full pipeline from MCP tool call to database query
        pass

    @pytest.mark.asyncio  
    async def test_server_initialization(self):
        """Test that server initializes with correct capabilities"""
        # Test server capabilities and initialization
        pass


if __name__ == "__main__":
    pytest.main([__file__])