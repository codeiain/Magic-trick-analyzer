"""
Unit tests for AI Processing functionality
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from ai_service.ai_processor import AIProcessor, process_text, train_model


class TestAIProcessor:
    """Test AIProcessor functionality"""
    
    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock SentenceTransformer model"""
        mock = Mock()
        # Return consistent embeddings for testing
        mock.encode.return_value = np.array([[0.1, 0.2, 0.3, 0.4, 0.5]])
        return mock
    
    @pytest.fixture
    def mock_database(self):
        """Mock database components"""
        mock_engine = Mock()
        mock_session = Mock()
        return mock_engine, mock_session
    
    @pytest.fixture
    def ai_processor(self, mock_sentence_transformer, mock_database):
        """AIProcessor instance with mocked dependencies"""
        with patch('ai_service.ai_processor.SentenceTransformer') as mock_st_class:
            with patch('ai_service.ai_processor.create_engine') as mock_create_engine:
                with patch('ai_service.ai_processor.sessionmaker') as mock_sessionmaker:
                    mock_st_class.return_value = mock_sentence_transformer
                    mock_engine, mock_session = mock_database
                    mock_create_engine.return_value = mock_engine
                    mock_sessionmaker.return_value = Mock(return_value=mock_session)
                    
                    processor = AIProcessor()
                    return processor
    
    def test_init_successful(self, ai_processor, mock_sentence_transformer, mock_database):
        """Test successful AI processor initialization"""
        mock_engine, mock_session = mock_database
        assert ai_processor.model == mock_sentence_transformer
        assert ai_processor.db_engine == mock_engine
        assert ai_processor.db_session == mock_session
    
    @patch.dict('os.environ', {"AI_MODEL": "custom-model"})
    def test_init_with_custom_model(self, mock_sentence_transformer, mock_database):
        """Test initialization with custom AI model"""
        with patch('ai_service.ai_processor.SentenceTransformer') as mock_st_class:
            with patch('ai_service.ai_processor.create_engine'):
                with patch('ai_service.ai_processor.sessionmaker'):
                    mock_st_class.return_value = mock_sentence_transformer
                    
                    AIProcessor()
                    mock_st_class.assert_called_with("custom-model")
    
    def test_detect_tricks_with_indicators(self, ai_processor, mock_sentence_transformer):
        """Test trick detection with clear indicators"""
        # Setup
        text_content = """
        The Vanishing Coin
        
        Effect: A coin disappears from the magician's hand.
        Method: Use a thumb tip to conceal the coin.
        
        The Four Ace Trick
        
        Effect: All four aces are produced from a shuffled deck.
        Preparation: Pre-arrange the aces on top of the deck.
        """
        
        mock_sentence_transformer.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        
        # Execute
        tricks = ai_processor.detect_tricks(text_content, "book-123")
        
        # Assert
        assert len(tricks) >= 2  # Should detect at least 2 tricks
        
        trick_names = [trick['name'] for trick in tricks]
        assert any('Vanishing Coin' in name for name in trick_names)
        assert any('Four Ace' in name for name in trick_names)
        
        # Check trick properties
        for trick in tricks:
            assert trick['book_id'] == 'book-123'
            assert 'embedding' in trick
            assert 'effect_type' in trick
            assert 'difficulty' in trick
            assert 'confidence' in trick
            assert 'created_at' in trick
    
    def test_detect_tricks_no_indicators(self, ai_processor):
        """Test trick detection with no clear indicators"""
        # Setup
        text_content = "This is just regular text without any magic trick indicators."
        
        # Execute
        tricks = ai_processor.detect_tricks(text_content, "book-123")
        
        # Assert
        assert len(tricks) == 0  # Should not detect any tricks
    
    def test_detect_tricks_short_paragraphs(self, ai_processor):
        """Test trick detection skips short paragraphs"""
        # Setup
        text_content = """
        Short.
        
        Also short.
        
        This is a longer paragraph that contains the word effect and method,
        but might not be a full trick description. However, it's long enough
        to be considered for analysis.
        """
        
        # Execute
        tricks = ai_processor.detect_tricks(text_content, "book-123")
        
        # Assert - should only process the long paragraph
        assert len(tricks) <= 1
    
    def test_classify_effect_type_card(self, ai_processor):
        """Test effect type classification for card tricks"""
        text = "This trick uses a deck of cards and the four aces"
        
        result = ai_processor._classify_effect_type(text)
        
        assert result == "Card"
    
    def test_classify_effect_type_coin(self, ai_processor):
        """Test effect type classification for coin tricks"""
        text = "The magician uses a quarter and some pennies for this trick"
        
        result = ai_processor._classify_effect_type(text)
        
        assert result == "Coin"
    
    def test_classify_effect_type_mentalism(self, ai_processor):
        """Test effect type classification for mentalism"""
        text = "This is a mind reading effect using telepathy and predictions"
        
        result = ai_processor._classify_effect_type(text)
        
        assert result == "Mentalism"
    
    def test_classify_effect_type_general(self, ai_processor):
        """Test effect type classification for general tricks"""
        text = "This is a general magic trick with no specific props"
        
        result = ai_processor._classify_effect_type(text)
        
        assert result == "General"
    
    def test_classify_difficulty_beginner(self, ai_processor):
        """Test difficulty classification for beginner tricks"""
        text = "This is an easy and simple basic trick for beginners"
        
        result = ai_processor._classify_difficulty(text)
        
        assert result == "Beginner"
    
    def test_classify_difficulty_advanced(self, ai_processor):
        """Test difficulty classification for advanced tricks"""
        text = "This advanced sleight requires difficult professional technique"
        
        result = ai_processor._classify_difficulty(text)
        
        assert result == "Advanced"
    
    def test_classify_difficulty_intermediate(self, ai_processor):
        """Test difficulty classification defaults to intermediate"""
        text = "This is a magic trick with no clear difficulty indicators"
        
        result = ai_processor._classify_difficulty(text)
        
        assert result == "Intermediate"
    
    def test_calculate_similarities_sufficient_tricks(self, ai_processor):
        """Test similarity calculation with sufficient tricks"""
        # Setup
        tricks = [
            {'embedding': [0.1, 0.2, 0.3], 'name': 'Trick 1'},
            {'embedding': [0.1, 0.2, 0.31], 'name': 'Trick 2'},  # Very similar
            {'embedding': [0.9, 0.8, 0.7], 'name': 'Trick 3'},   # Different
        ]
        
        # Execute
        similarities = ai_processor.calculate_similarities(tricks)
        
        # Assert
        assert len(similarities) >= 1  # Should find at least one similarity
        
        # Check similarity structure
        for sim in similarities:
            assert 'source_trick_idx' in sim
            assert 'target_trick_idx' in sim
            assert 'similarity_score' in sim
            assert 'relationship_type' in sim
            assert sim['similarity_score'] > 0.7
    
    def test_calculate_similarities_insufficient_tricks(self, ai_processor):
        """Test similarity calculation with insufficient tricks"""
        # Setup
        tricks = [{'embedding': [0.1, 0.2, 0.3], 'name': 'Only Trick'}]
        
        # Execute
        similarities = ai_processor.calculate_similarities(tricks)
        
        # Assert
        assert len(similarities) == 0
    
    def test_calculate_similarities_error_handling(self, ai_processor):
        """Test similarity calculation error handling"""
        # Setup - invalid embeddings
        tricks = [
            {'embedding': 'invalid', 'name': 'Trick 1'},
            {'embedding': 'also_invalid', 'name': 'Trick 2'}
        ]
        
        # Execute
        similarities = ai_processor.calculate_similarities(tricks)
        
        # Assert - should handle error gracefully
        assert len(similarities) == 0


class TestProcessTextJobFunction:
    """Test the RQ job function process_text"""
    
    @patch('ai_service.ai_processor.AIProcessor')
    def test_process_text_success(self, mock_processor_class):
        """Test successful text processing job"""
        # Setup
        mock_processor = Mock()
        mock_tricks = [
            {'name': 'Test Trick', 'embedding': [0.1, 0.2]},
            {'name': 'Another Trick', 'embedding': [0.3, 0.4]}
        ]
        mock_similarities = [
            {'source_trick_idx': 0, 'target_trick_idx': 1, 'similarity_score': 0.8}
        ]
        
        mock_processor.detect_tricks.return_value = mock_tricks
        mock_processor.calculate_similarities.return_value = mock_similarities
        mock_processor_class.return_value = mock_processor
        
        job_data = {
            'text_content': 'Test magic trick content',
            'book_id': 'book-123'
        }
        
        # Execute
        result = process_text(job_data)
        
        # Assert
        assert result['status'] == 'completed'
        assert result['book_id'] == 'book-123'
        assert result['tricks_detected'] == 2
        assert result['similarities_found'] == 1
        assert result['tricks'] == mock_tricks
        assert result['similarities'] == mock_similarities
        assert 'processed_at' in result
    
    @patch('ai_service.ai_processor.AIProcessor')
    def test_process_text_failure(self, mock_processor_class):
        """Test text processing job failure"""
        # Setup
        mock_processor_class.side_effect = Exception("AI processing failed")
        
        job_data = {
            'text_content': 'Test content',
            'book_id': 'book-123'
        }
        
        # Execute
        result = process_text(job_data)
        
        # Assert
        assert result['status'] == 'failed'
        assert 'AI processing failed' in result['error']
        assert 'processed_at' in result


class TestTrainModelJobFunction:
    """Test the RQ job function train_model"""
    
    @patch('time.sleep')  # Speed up test
    def test_train_model_success(self, mock_sleep):
        """Test successful model training job"""
        # Setup
        job_data = {
            'training_data': {
                'feedback': [
                    {'trick_id': '123', 'rating': 5},
                    {'trick_id': '456', 'rating': 3}
                ]
            }
        }
        
        # Execute
        result = train_model(job_data)
        
        # Assert
        assert result['status'] == 'completed'
        assert result['feedback_processed'] == 2
        assert result['model_version'] == '1.1'
        assert 'training_accuracy' in result
        assert 'trained_at' in result
    
    def test_train_model_no_feedback(self):
        """Test model training with no feedback data"""
        # Setup
        job_data = {'training_data': {}}
        
        # Execute
        result = train_model(job_data)
        
        # Assert
        assert result['status'] == 'completed'
        assert result['feedback_processed'] == 0
    
    @patch('time.sleep')
    def test_train_model_failure(self, mock_sleep):
        """Test model training failure"""
        # Setup - simulate failure during training
        mock_sleep.side_effect = Exception("Training failed")
        
        job_data = {'training_data': {'feedback': []}}
        
        # Execute
        result = train_model(job_data)
        
        # Assert
        assert result['status'] == 'failed'
        assert 'Training failed' in result['error']
        assert 'trained_at' in result


class TestAIProcessorIntegration:
    """Integration tests for AI processor"""
    
    @pytest.mark.integration
    def test_end_to_end_trick_detection(self):
        """Test complete trick detection pipeline"""
        with patch('ai_service.ai_processor.create_engine'):
            with patch('ai_service.ai_processor.sessionmaker'):
                processor = AIProcessor()
                
                # Real magic trick text
                text = """
                The Four Aces
                
                Effect: The four aces are magically produced from a shuffled deck.
                Method: Pre-arrange the aces on top before the performance starts.
                This is a classic card trick suitable for beginners.
                
                Coin Vanish
                
                Effect: A coin disappears from the performer's hand.
                Method: Use a thumb tip or classic palm to conceal the coin.
                This requires practice but is very effective for audiences.
                """
                
                # Execute
                tricks = processor.detect_tricks(text, "integration-test")
                
                # Assert
                assert len(tricks) >= 2
                
                # Check that we detected card and coin tricks
                effect_types = [trick['effect_type'] for trick in tricks]
                assert 'Card' in effect_types or 'General' in effect_types
                assert 'Coin' in effect_types or 'General' in effect_types
                
                # Test similarities
                similarities = processor.calculate_similarities(tricks)
                assert isinstance(similarities, list)