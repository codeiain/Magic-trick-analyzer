"""
AI Processing Functions

Core AI functionality extracted from the main application for microservice architecture.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# AI/ML imports
import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Database imports  
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

class AIProcessor:
    """AI processing functionality"""
    
    def __init__(self):
        self.model = None
        self.db_engine = None
        self.db_session = None
        self._initialize()
    
    def _initialize(self):
        """Initialize AI models and database connection"""
        try:
            # Initialize database
            db_url = os.getenv("DATABASE_URL", "sqlite:///data/magic_tricks.db")
            self.db_engine = create_engine(db_url)
            Session = sessionmaker(bind=self.db_engine)
            self.db_session = Session()
            
            # Load AI model
            model_name = os.getenv("AI_MODEL", "all-MiniLM-L6-v2")
            logger.info(f"Loading AI model: {model_name}")
            
            self.model = SentenceTransformer(model_name)
            logger.info("AI processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI processor: {e}")
            raise
    
    def detect_tricks(self, text_content: str, book_id: str) -> List[Dict[str, Any]]:
        """Detect magic tricks in text content"""
        try:
            logger.info(f"Processing text for book {book_id}, length: {len(text_content)} characters")
            
            # Simple trick detection logic (this would be more sophisticated in practice)
            tricks = []
            
            # Split text into paragraphs
            paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
            
            for i, paragraph in enumerate(paragraphs):
                if len(paragraph) < 50:  # Skip short paragraphs
                    continue
                
                # Simple heuristics for trick detection
                trick_indicators = [
                    'effect:', 'method:', 'preparation:', 'performance:',
                    'the trick', 'the effect', 'the method', 'the secret',
                    'vanish', 'appear', 'transform', 'prediction'
                ]
                
                paragraph_lower = paragraph.lower()
                if any(indicator in paragraph_lower for indicator in trick_indicators):
                    
                    # Extract a potential trick name (first sentence/line)
                    lines = paragraph.split('\n')
                    potential_name = lines[0].strip() if lines else f"Trick {i+1}"
                    
                    # Clean the name
                    if len(potential_name) > 100:
                        potential_name = potential_name[:100] + "..."
                    
                    # Determine effect type based on content
                    effect_type = self._classify_effect_type(paragraph_lower)
                    
                    # Determine difficulty
                    difficulty = self._classify_difficulty(paragraph_lower)
                    
                    # Generate embedding for similarity
                    embedding = self.model.encode([paragraph])[0]
                    
                    trick = {
                        'name': potential_name,
                        'description': paragraph[:500],  # Truncate description
                        'effect_type': effect_type,
                        'difficulty': difficulty,
                        'confidence': 0.7,  # Basic confidence score
                        'page_start': i + 1,  # Approximate page
                        'book_id': book_id,
                        'embedding': embedding.tolist(),  # For similarity calculations
                        'created_at': datetime.utcnow().isoformat()
                    }
                    
                    tricks.append(trick)
            
            logger.info(f"Detected {len(tricks)} potential tricks in book {book_id}")
            return tricks
            
        except Exception as e:
            logger.error(f"Error detecting tricks: {e}")
            return []
    
    def _classify_effect_type(self, text: str) -> str:
        """Classify the effect type based on text content"""
        
        card_indicators = ['card', 'deck', 'ace', 'king', 'queen', 'jack', 'spade', 'heart', 'diamond', 'club']
        coin_indicators = ['coin', 'penny', 'quarter', 'dollar', 'change', 'money']
        mentalism_indicators = ['mind', 'thought', 'prediction', 'esp', 'psychic', 'telepathy', 'mental']
        rope_indicators = ['rope', 'string', 'cord', 'thread']
        silk_indicators = ['silk', 'handkerchief', 'scarf']
        
        if any(indicator in text for indicator in card_indicators):
            return "Card"
        elif any(indicator in text for indicator in coin_indicators):
            return "Coin"
        elif any(indicator in text for indicator in mentalism_indicators):
            return "Mentalism"
        elif any(indicator in text for indicator in rope_indicators):
            return "Rope"
        elif any(indicator in text for indicator in silk_indicators):
            return "Silk"
        else:
            return "General"
    
    def _classify_difficulty(self, text: str) -> str:
        """Classify difficulty level based on text content"""
        
        beginner_indicators = ['easy', 'simple', 'basic', 'beginner', 'elementary']
        advanced_indicators = ['advanced', 'difficult', 'complex', 'expert', 'professional', 'sleight']
        
        if any(indicator in text for indicator in advanced_indicators):
            return "Advanced"
        elif any(indicator in text for indicator in beginner_indicators):
            return "Beginner"
        else:
            return "Intermediate"
    
    def calculate_similarities(self, tricks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate similarity between tricks"""
        
        if len(tricks) < 2:
            return []
        
        similarities = []
        
        try:
            # Extract embeddings
            embeddings = np.array([trick['embedding'] for trick in tricks])
            
            # Calculate cosine similarities
            similarity_matrix = cosine_similarity(embeddings)
            
            # Find significant similarities (threshold > 0.7)
            threshold = 0.7
            for i in range(len(tricks)):
                for j in range(i + 1, len(tricks)):
                    similarity_score = similarity_matrix[i][j]
                    
                    if similarity_score > threshold:
                        similarities.append({
                            'source_trick_idx': i,
                            'target_trick_idx': j,
                            'similarity_score': float(similarity_score),
                            'relationship_type': 'similar'
                        })
            
            logger.info(f"Found {len(similarities)} similar trick pairs")
            
        except Exception as e:
            logger.error(f"Error calculating similarities: {e}")
        
        return similarities

# RQ job functions (called by the worker)

def process_text(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process text content to detect magic tricks (RQ job function)"""
    
    logger.info(f"Starting AI text processing job: {job_data.get('parent_job_id')}")
    
    try:
        processor = AIProcessor()
        
        text_content = job_data['text_content']
        book_id = job_data['book_id']
        
        # Detect tricks
        tricks = processor.detect_tricks(text_content, book_id)
        
        # Calculate similarities within the book
        similarities = processor.calculate_similarities(tricks)
        
        result = {
            'status': 'completed',
            'book_id': book_id,
            'tricks_detected': len(tricks),
            'similarities_found': len(similarities),
            'tricks': tricks,
            'similarities': similarities,
            'processed_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"AI processing completed: {len(tricks)} tricks detected")
        return result
        
    except Exception as e:
        logger.error(f"AI processing failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'processed_at': datetime.utcnow().isoformat()
        }

def train_model(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Train/fine-tune the AI model (RQ job function)"""
    
    logger.info("Starting model training job")
    
    try:
        # This would implement actual model training
        # For now, just simulate training
        
        training_data = job_data.get('training_data', {})
        feedback_count = len(training_data.get('feedback', []))
        
        logger.info(f"Training with {feedback_count} feedback examples")
        
        # Simulate training time
        import time
        time.sleep(30)  # Simulate 30 seconds of training
        
        result = {
            'status': 'completed',
            'feedback_processed': feedback_count,
            'model_version': '1.1',
            'training_accuracy': 0.85,  # Mock accuracy
            'trained_at': datetime.utcnow().isoformat()
        }
        
        logger.info("Model training completed")
        return result
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'trained_at': datetime.utcnow().isoformat()
        }