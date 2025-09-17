"""
Unit tests for AI Processor

Tests the AI processing functionality including trick detection,
classification, similarity calculations, and job processing.
"""

import pytest
import numpy as np
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from ai_processor import AIProcessor, process_text, train_model


class TestAIProcessor:
    """Test cases for AIProcessor class"""

    @pytest.fixture
    def mock_model(self):
        """Mock SentenceTransformer model"""
        mock_model = Mock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3, 0.4, 0.5]])
        return mock_model

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def mock_db_engine(self):
        """Mock database engine"""
        return Mock()

    @pytest.fixture
    def ai_processor(self, mock_model, mock_db_session, mock_db_engine):
        """Create AI processor with mocked dependencies"""
        with patch('ai_processor.SentenceTransformer', return_value=mock_model), \
             patch('ai_processor.create_engine', return_value=mock_db_engine), \
             patch('ai_processor.sessionmaker') as mock_session_maker:
            
            mock_session_maker.return_value.return_value = mock_db_session
            processor = AIProcessor()
            return processor

    def test_initialization_success(self, mock_model, mock_db_session, mock_db_engine):
        """Test successful AI processor initialization"""
        with patch('ai_processor.SentenceTransformer', return_value=mock_model), \
             patch('ai_processor.create_engine', return_value=mock_db_engine), \
             patch('ai_processor.sessionmaker') as mock_session_maker, \
             patch.dict('os.environ', {'DATABASE_URL': 'sqlite:///test.db', 'AI_MODEL': 'test-model'}):
            
            mock_session_maker.return_value.return_value = mock_db_session
            
            processor = AIProcessor()
            
            assert processor.model == mock_model
            assert processor.db_engine == mock_db_engine
            assert processor.db_session == mock_db_session

    def test_initialization_failure(self):
        """Test AI processor initialization failure"""
        with patch('ai_processor.SentenceTransformer', side_effect=Exception("Model load failed")):
            with pytest.raises(Exception, match="Model load failed"):
                AIProcessor()

    def test_classify_effect_type_card(self, ai_processor):
        """Test effect type classification for card tricks"""
        text = "take the deck of cards and ask the spectator to choose an ace"
        result = ai_processor._classify_effect_type(text)
        assert result == "Card"

    def test_classify_effect_type_coin(self, ai_processor):
        """Test effect type classification for coin tricks"""
        text = "take a quarter and show it to the audience, then make the coin vanish"
        result = ai_processor._classify_effect_type(text)
        assert result == "Coin"

    def test_classify_effect_type_mentalism(self, ai_processor):
        """Test effect type classification for mentalism"""
        text = "ask the spectator to think of a number and predict their thought"
        result = ai_processor._classify_effect_type(text)
        assert result == "Mentalism"

    def test_classify_effect_type_rope(self, ai_processor):
        """Test effect type classification for rope tricks"""
        text = "take a piece of rope and cut it into several pieces"
        result = ai_processor._classify_effect_type(text)
        assert result == "Rope"

    def test_classify_effect_type_silk(self, ai_processor):
        """Test effect type classification for silk tricks"""
        text = "take a silk handkerchief and make it disappear"
        result = ai_processor._classify_effect_type(text)
        assert result == "Silk"

    def test_classify_effect_type_general(self, ai_processor):
        """Test effect type classification for general tricks"""
        text = "perform this amazing illusion with these props"
        result = ai_processor._classify_effect_type(text)
        assert result == "General"

    def test_classify_difficulty_beginner(self, ai_processor):
        """Test difficulty classification for beginner tricks"""
        text = "this is an easy trick suitable for beginners"
        result = ai_processor._classify_difficulty(text)
        assert result == "Beginner"

    def test_classify_difficulty_advanced(self, ai_processor):
        """Test difficulty classification for advanced tricks"""
        text = "this requires advanced sleight of hand and professional skill"
        result = ai_processor._classify_difficulty(text)
        assert result == "Advanced"

    def test_classify_difficulty_intermediate(self, ai_processor):
        """Test difficulty classification for intermediate tricks"""
        text = "this trick requires some practice but is not too difficult"
        result = ai_processor._classify_difficulty(text)
        assert result == "Intermediate"

    def test_detect_tricks_empty_text(self, ai_processor):
        """Test trick detection with empty text"""
        result = ai_processor.detect_tricks("", "book_123")
        assert result == []

    def test_detect_tricks_no_indicators(self, ai_processor):
        """Test trick detection with text containing no trick indicators"""
        text = "This is just regular text without any magic content."
        result = ai_processor.detect_tricks(text, "book_123")
        assert result == []

    def test_detect_tricks_with_indicators(self, ai_processor):
        """Test trick detection with text containing trick indicators"""
        text = """
        The Amazing Card Vanish
        
        Effect: The magician takes a card and makes it vanish completely.
        
        Method: Use the classic palm technique to hide the card.
        
        Another Trick
        
        This trick involves making a coin appear from thin air.
        """
        
        with patch.object(ai_processor.model, 'encode', return_value=np.array([[0.1, 0.2, 0.3]])):
            result = ai_processor.detect_tricks(text, "book_123")
        
        assert len(result) >= 1
        assert any("Effect:" in trick['description'] for trick in result)
        assert all(trick['book_id'] == "book_123" for trick in result)
        assert all(trick['confidence'] == 0.7 for trick in result)

    def test_detect_tricks_short_paragraphs_ignored(self, ai_processor):
        """Test that short paragraphs are ignored during trick detection"""
        text = """
        Short.
        
        Effect: This is a longer paragraph that contains trick indicators and should be detected as a potential magic trick.
        """
        
        with patch.object(ai_processor.model, 'encode', return_value=np.array([[0.1, 0.2, 0.3]])):
            result = ai_processor.detect_tricks(text, "book_123")
        
        assert len(result) == 1
        assert "Effect:" in result[0]['description']

    def test_detect_tricks_name_truncation(self, ai_processor):
        """Test that long trick names are properly truncated"""
        text = f"""
        {'Very long trick name ' * 10}that exceeds the character limit.
        
        Effect: This trick has a very long name that should be truncated.
        """
        
        with patch.object(ai_processor.model, 'encode', return_value=np.array([[0.1, 0.2, 0.3]])):
            result = ai_processor.detect_tricks(text, "book_123")
        
        assert len(result) == 1
        assert len(result[0]['name']) <= 103  # 100 chars + "..."
        assert result[0]['name'].endswith("...")

    def test_detect_tricks_description_truncation(self, ai_processor):
        """Test that long descriptions are properly truncated"""
        long_description = "This is a very long description. " * 50
        text = f"Effect: {long_description}"
        
        with patch.object(ai_processor.model, 'encode', return_value=np.array([[0.1, 0.2, 0.3]])):
            result = ai_processor.detect_tricks(text, "book_123")
        
        assert len(result) == 1
        assert len(result[0]['description']) <= 500

    def test_detect_tricks_classification_integration(self, ai_processor):
        """Test that trick detection properly uses classification methods"""
        text = """
        Card Force Technique
        
        Effect: The spectator chooses a card, but it's actually a force using an easy method.
        """
        
        with patch.object(ai_processor.model, 'encode', return_value=np.array([[0.1, 0.2, 0.3]])):
            result = ai_processor.detect_tricks(text, "book_123")
        
        assert len(result) == 1
        assert result[0]['effect_type'] == "Card"  # Should detect card-related content
        assert result[0]['difficulty'] == "Beginner"  # Should detect "easy" keyword

    def test_calculate_similarities_insufficient_tricks(self, ai_processor):
        """Test similarity calculation with insufficient tricks"""
        tricks = [{'embedding': [0.1, 0.2, 0.3]}]
        result = ai_processor.calculate_similarities(tricks)
        assert result == []

    def test_calculate_similarities_no_high_similarity(self, ai_processor):
        """Test similarity calculation with no high similarity pairs"""
        tricks = [
            {'embedding': [1.0, 0.0, 0.0]},
            {'embedding': [0.0, 1.0, 0.0]}  # Very different embeddings
        ]
        
        with patch('ai_processor.cosine_similarity', return_value=np.array([[1.0, 0.1], [0.1, 1.0]])):
            result = ai_processor.calculate_similarities(tricks)
        
        assert result == []  # No similarities above threshold

    def test_calculate_similarities_high_similarity_found(self, ai_processor):
        """Test similarity calculation with high similarity pairs"""
        tricks = [
            {'embedding': [1.0, 0.0, 0.0]},
            {'embedding': [0.9, 0.1, 0.0]},  # Very similar
            {'embedding': [0.8, 0.2, 0.0]}   # Also similar
        ]
        
        # Mock similarity matrix with high similarities
        similarity_matrix = np.array([
            [1.0, 0.8, 0.75],
            [0.8, 1.0, 0.85],
            [0.75, 0.85, 1.0]
        ])
        
        with patch('ai_processor.cosine_similarity', return_value=similarity_matrix):
            result = ai_processor.calculate_similarities(tricks)
        
        # Should find similarities above threshold (0.7)
        assert len(result) >= 1
        assert all(sim['similarity_score'] > 0.7 for sim in result)
        assert all(sim['relationship_type'] == 'similar' for sim in result)

    def test_calculate_similarities_error_handling(self, ai_processor):
        """Test similarity calculation error handling"""
        tricks = [
            {'embedding': [1.0, 0.0]},
            {'embedding': [0.0, 1.0]}
        ]
        
        with patch('ai_processor.cosine_similarity', side_effect=Exception("Calculation error")):
            result = ai_processor.calculate_similarities(tricks)
        
        assert result == []


class TestProcessTextJob:
    """Test cases for the process_text RQ job function"""

    @pytest.fixture
    def job_data(self):
        """Sample job data for testing"""
        return {
            'text_content': "Effect: Make a card vanish. Method: Use sleight of hand.",
            'book_id': 'book_123',
            'parent_job_id': 'job_456'
        }

    def test_process_text_success(self, job_data):
        """Test successful text processing job"""
        mock_processor = Mock()
        mock_tricks = [
            {'name': 'Card Vanish', 'effect_type': 'Card', 'confidence': 0.8},
            {'name': 'Another Trick', 'effect_type': 'General', 'confidence': 0.7}
        ]
        mock_similarities = [
            {'source_trick_idx': 0, 'target_trick_idx': 1, 'similarity_score': 0.75}
        ]
        
        mock_processor.detect_tricks.return_value = mock_tricks
        mock_processor.calculate_similarities.return_value = mock_similarities

        with patch('ai_processor.AIProcessor', return_value=mock_processor):
            result = process_text(job_data)

        assert result['status'] == 'completed'
        assert result['book_id'] == 'book_123'
        assert result['tricks_detected'] == 2
        assert result['similarities_found'] == 1
        assert result['tricks'] == mock_tricks
        assert result['similarities'] == mock_similarities
        assert 'processed_at' in result

    def test_process_text_processor_init_error(self, job_data):
        """Test text processing with processor initialization error"""
        with patch('ai_processor.AIProcessor', side_effect=Exception("Init failed")):
            result = process_text(job_data)

        assert result['status'] == 'failed'
        assert 'Init failed' in result['error']
        assert 'processed_at' in result

    def test_process_text_detection_error(self, job_data):
        """Test text processing with trick detection error"""
        mock_processor = Mock()
        mock_processor.detect_tricks.side_effect = Exception("Detection failed")

        with patch('ai_processor.AIProcessor', return_value=mock_processor):
            result = process_text(job_data)

        assert result['status'] == 'failed'
        assert 'Detection failed' in result['error']

    def test_process_text_similarity_error(self, job_data):
        """Test text processing with similarity calculation error"""
        mock_processor = Mock()
        mock_processor.detect_tricks.return_value = []
        mock_processor.calculate_similarities.side_effect = Exception("Similarity failed")

        with patch('ai_processor.AIProcessor', return_value=mock_processor):
            result = process_text(job_data)

        assert result['status'] == 'failed'
        assert 'Similarity failed' in result['error']

    @patch('ai_processor.datetime')
    def test_process_text_timestamp(self, mock_datetime, job_data):
        """Test that text processing includes correct timestamp"""
        fixed_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = fixed_time

        mock_processor = Mock()
        mock_processor.detect_tricks.return_value = []
        mock_processor.calculate_similarities.return_value = []

        with patch('ai_processor.AIProcessor', return_value=mock_processor):
            result = process_text(job_data)

        assert result['processed_at'] == fixed_time.isoformat()


class TestTrainModelJob:
    """Test cases for the train_model RQ job function"""

    @pytest.fixture
    def training_job_data(self):
        """Sample training job data"""
        return {
            'training_data': {
                'feedback': [
                    {'trick_id': '1', 'correct': True},
                    {'trick_id': '2', 'correct': False}
                ]
            }
        }

    @patch('ai_processor.time.sleep')  # Speed up test
    def test_train_model_success(self, mock_sleep, training_job_data):
        """Test successful model training job"""
        result = train_model(training_job_data)

        assert result['status'] == 'completed'
        assert result['feedback_processed'] == 2
        assert result['model_version'] == '1.1'
        assert result['training_accuracy'] == 0.85
        assert 'trained_at' in result
        mock_sleep.assert_called_once_with(30)

    @patch('ai_processor.time.sleep')
    def test_train_model_no_feedback(self, mock_sleep):
        """Test model training with no feedback data"""
        job_data = {'training_data': {}}
        
        result = train_model(job_data)

        assert result['status'] == 'completed'
        assert result['feedback_processed'] == 0

    @patch('ai_processor.time.sleep', side_effect=Exception("Training failed"))
    def test_train_model_error(self, mock_sleep, training_job_data):
        """Test model training error handling"""
        result = train_model(training_job_data)

        assert result['status'] == 'failed'
        assert 'Training failed' in result['error']
        assert 'trained_at' in result

    @patch('ai_processor.datetime')
    @patch('ai_processor.time.sleep')
    def test_train_model_timestamp(self, mock_sleep, mock_datetime, training_job_data):
        """Test that model training includes correct timestamp"""
        fixed_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = fixed_time

        result = train_model(training_job_data)

        assert result['trained_at'] == fixed_time.isoformat()


class TestAIProcessorIntegration:
    """Integration tests for AI processor with real-like scenarios"""

    @pytest.fixture
    def ai_processor(self):
        """Create AI processor with mocked external dependencies"""
        mock_model = Mock()
        with patch('ai_processor.SentenceTransformer', return_value=mock_model), \
             patch('ai_processor.create_engine'), \
             patch('ai_processor.sessionmaker'):
            processor = AIProcessor()
            processor.model = mock_model
            return processor

    def test_full_detection_pipeline(self, ai_processor):
        """Test complete trick detection pipeline"""
        text = """
        The Ambitious Card
        
        Effect: A selected card continually rises to the top of the deck.
        
        Method: Use a double lift and careful misdirection.
        
        The Vanishing Coin
        
        Effect: A coin placed under a handkerchief completely disappears.
        
        Method: Use a simple finger palm technique.
        """
        
        # Mock model to return different embeddings for different tricks
        embeddings = np.array([
            [0.8, 0.1, 0.2, 0.3, 0.4],  # Card trick embedding
            [0.1, 0.8, 0.3, 0.2, 0.1]   # Coin trick embedding
        ])
        ai_processor.model.encode.return_value = embeddings

        tricks = ai_processor.detect_tricks(text, "book_123")
        
        assert len(tricks) == 2
        
        # Check card trick
        card_trick = next(t for t in tricks if 'card' in t['name'].lower())
        assert card_trick['effect_type'] == "Card"
        assert 'Effect:' in card_trick['description']
        
        # Check coin trick
        coin_trick = next(t for t in tricks if 'coin' in t['name'].lower())
        assert coin_trick['effect_type'] == "Coin"

    def test_detection_and_similarity_pipeline(self, ai_processor):
        """Test detection followed by similarity calculation"""
        text = """
        Card Trick One
        
        Effect: Make a card vanish using sleight of hand.
        
        Card Trick Two
        
        Effect: Make a different card vanish using similar sleight of hand.
        """
        
        # Mock similar embeddings
        embeddings = np.array([
            [0.9, 0.1, 0.1, 0.1, 0.1],
            [0.8, 0.2, 0.1, 0.1, 0.1]   # Very similar to first
        ])
        ai_processor.model.encode.return_value = embeddings
        
        with patch('ai_processor.cosine_similarity', return_value=np.array([[1.0, 0.85], [0.85, 1.0]])):
            tricks = ai_processor.detect_tricks(text, "book_123")
            similarities = ai_processor.calculate_similarities(tricks)
        
        assert len(tricks) == 2
        assert len(similarities) >= 1
        assert similarities[0]['similarity_score'] > 0.7

    def test_error_recovery_in_detection(self, ai_processor):
        """Test error recovery during trick detection"""
        text = "Effect: A trick that should be detected."
        
        # Mock model to fail on encode but processor should handle gracefully
        ai_processor.model.encode.side_effect = Exception("Encoding failed")
        
        # Should not crash, but return empty list
        with pytest.raises(Exception):
            ai_processor.detect_tricks(text, "book_123")


# Test utilities and fixtures
@pytest.fixture
def sample_magic_text():
    """Sample magic trick text for testing"""
    return """
    The Four Ace Production
    
    Effect: The magician produces the four aces from a shuffled deck in a surprising manner.
    
    Method: Pre-arrange the aces on top of the deck and use a false shuffle to maintain their position.
    
    Preparation: Place the four aces on top of the deck before beginning the routine.
    
    Performance: Shuffle the deck while maintaining the top stock, then deal the aces dramatically.
    """

@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing similarity calculations"""
    return np.array([
        [0.8, 0.1, 0.2, 0.3, 0.4],  # Trick 1
        [0.7, 0.2, 0.3, 0.2, 0.1],  # Trick 2 - somewhat similar
        [0.1, 0.1, 0.1, 0.8, 0.9]   # Trick 3 - very different
    ])


if __name__ == "__main__":
    pytest.main([__file__])