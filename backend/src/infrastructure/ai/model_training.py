"""
Model fine-tuning infrastructure for improving trick detection.
Uses user feedback to create training data and fine-tune the base model.
"""
import logging
import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from datetime import datetime
import torch
from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
from torch.utils.data import DataLoader
import numpy as np

from ...domain.entities.magic import Trick
from ...domain.value_objects.common import TrickId, Confidence
from ...infrastructure.repositories.sql_repositories import SQLTrickRepository, SQLBookRepository


class FeedbackData:
    """Container for user feedback on trick detections."""
    
    def __init__(
        self,
        trick_id: str,
        is_correct: bool,
        user_notes: Optional[str] = None,
        suggested_name: Optional[str] = None,
        suggested_description: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.trick_id = trick_id
        self.is_correct = is_correct
        self.user_notes = user_notes
        self.suggested_name = suggested_name
        self.suggested_description = suggested_description
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict:
        return {
            'trick_id': self.trick_id,
            'is_correct': self.is_correct,
            'user_notes': self.user_notes,
            'suggested_name': self.suggested_name,
            'suggested_description': self.suggested_description,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FeedbackData':
        return cls(
            trick_id=data['trick_id'],
            is_correct=data['is_correct'],
            user_notes=data.get('user_notes'),
            suggested_name=data.get('suggested_name'),
            suggested_description=data.get('suggested_description'),
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


class TrainingDataGenerator:
    """
    Generates training data for fine-tuning from user feedback.
    Creates positive and negative pairs for contrastive learning.
    """
    
    def __init__(
        self, 
        trick_repository: SQLTrickRepository,
        feedback_file: str = "data/user_feedback.json"
    ):
        self._trick_repository = trick_repository
        self._feedback_file = Path(feedback_file)
        self._logger = logging.getLogger(__name__)
        
        # Ensure feedback file exists
        self._feedback_file.parent.mkdir(parents=True, exist_ok=True)
        if not self._feedback_file.exists():
            with open(self._feedback_file, 'w') as f:
                json.dump([], f)
    
    async def add_feedback(self, feedback: FeedbackData) -> None:
        """Add user feedback to the training dataset."""
        try:
            # Load existing feedback
            feedbacks = self._load_feedback()
            
            # Add new feedback
            feedbacks.append(feedback.to_dict())
            
            # Save updated feedback
            with open(self._feedback_file, 'w') as f:
                json.dump(feedbacks, f, indent=2)
            
            self._logger.info(f"Added feedback for trick {feedback.trick_id}")
            
        except Exception as e:
            self._logger.error(f"Error adding feedback: {str(e)}")
            raise
    
    async def generate_training_examples(self) -> List[InputExample]:
        """
        Generate training examples from user feedback.
        Creates positive/negative pairs for similarity learning.
        """
        feedbacks = self._load_feedback()
        training_examples = []
        
        # Get all validated tricks (marked as correct)
        correct_feedbacks = [f for f in feedbacks if f['is_correct']]
        incorrect_feedbacks = [f for f in feedbacks if not f['is_correct']]
        
        self._logger.info(f"Generating training data from {len(correct_feedbacks)} positive and {len(incorrect_feedbacks)} negative examples")
        
        # Create positive pairs (similar tricks)
        positive_pairs = await self._create_positive_pairs(correct_feedbacks)
        training_examples.extend(positive_pairs)
        
        # Create negative pairs (dissimilar tricks)
        negative_pairs = await self._create_negative_pairs(correct_feedbacks, incorrect_feedbacks)
        training_examples.extend(negative_pairs)
        
        # Create correction pairs (incorrect vs corrected)
        correction_pairs = await self._create_correction_pairs(incorrect_feedbacks)
        training_examples.extend(correction_pairs)
        
        self._logger.info(f"Generated {len(training_examples)} training examples")
        return training_examples
    
    async def _create_positive_pairs(self, correct_feedbacks: List[Dict]) -> List[InputExample]:
        """Create positive training pairs from correctly identified tricks."""
        examples = []
        
        for i, feedback1 in enumerate(correct_feedbacks):
            for feedback2 in correct_feedbacks[i+1:]:
                try:
                    trick1 = await self._trick_repository.find_by_id(TrickId(feedback1['trick_id']))
                    trick2 = await self._trick_repository.find_by_id(TrickId(feedback2['trick_id']))
                    
                    if trick1 and trick2 and self._are_similar_effects(trick1, trick2):
                        # High similarity for same effect type
                        examples.append(InputExample(
                            texts=[str(trick1.name), str(trick2.name)],
                            label=0.9  # High similarity
                        ))
                        
                        examples.append(InputExample(
                            texts=[trick1.description, trick2.description],
                            label=0.8  # Description similarity
                        ))
                        
                except Exception as e:
                    self._logger.warning(f"Error creating positive pair: {str(e)}")
                    continue
        
        return examples
    
    async def _create_negative_pairs(self, correct_feedbacks: List[Dict], incorrect_feedbacks: List[Dict]) -> List[InputExample]:
        """Create negative training pairs from different effect types."""
        examples = []
        
        # Pairs between different effect types (should be dissimilar)
        for feedback1 in correct_feedbacks[:20]:  # Limit to prevent explosion
            for feedback2 in correct_feedbacks[:20]:
                try:
                    if feedback1['trick_id'] == feedback2['trick_id']:
                        continue
                        
                    trick1 = await self._trick_repository.find_by_id(TrickId(feedback1['trick_id']))
                    trick2 = await self._trick_repository.find_by_id(TrickId(feedback2['trick_id']))
                    
                    if trick1 and trick2 and not self._are_similar_effects(trick1, trick2):
                        examples.append(InputExample(
                            texts=[str(trick1.name), str(trick2.name)],
                            label=0.2  # Low similarity
                        ))
                        
                except Exception as e:
                    self._logger.warning(f"Error creating negative pair: {str(e)}")
                    continue
        
        return examples
    
    async def _create_correction_pairs(self, incorrect_feedbacks: List[Dict]) -> List[InputExample]:
        """Create training pairs from user corrections."""
        examples = []
        
        for feedback in incorrect_feedbacks:
            if not feedback.get('suggested_name') and not feedback.get('suggested_description'):
                continue
                
            try:
                trick = await self._trick_repository.find_by_id(TrickId(feedback['trick_id']))
                if not trick:
                    continue
                
                # Original detection vs user correction (should be different)
                if feedback.get('suggested_name'):
                    examples.append(InputExample(
                        texts=[str(trick.name), feedback['suggested_name']],
                        label=0.3  # Low similarity - correction indicates difference
                    ))
                
                if feedback.get('suggested_description'):
                    examples.append(InputExample(
                        texts=[trick.description, feedback['suggested_description']],
                        label=0.4  # Slightly higher - descriptions might be more similar
                    ))
                    
            except Exception as e:
                self._logger.warning(f"Error creating correction pair: {str(e)}")
                continue
        
        return examples
    
    def _are_similar_effects(self, trick1: Trick, trick2: Trick) -> bool:
        """Check if two tricks have similar effects."""
        return trick1.effect_type == trick2.effect_type
    
    def _load_feedback(self) -> List[Dict]:
        """Load feedback from file."""
        try:
            with open(self._feedback_file, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    
    async def get_feedback_stats(self) -> Dict:
        """Get statistics about the feedback data."""
        feedbacks = self._load_feedback()
        
        correct_count = sum(1 for f in feedbacks if f['is_correct'])
        incorrect_count = len(feedbacks) - correct_count
        
        return {
            'total_feedback': len(feedbacks),
            'correct_detections': correct_count,
            'incorrect_detections': incorrect_count,
            'accuracy': correct_count / len(feedbacks) if feedbacks else 0.0
        }


class ModelFineTuner:
    """
    Fine-tunes the sentence transformer model using user feedback.
    """
    
    def __init__(
        self,
        base_model_name: str = "all-MiniLM-L6-v2",
        model_save_path: str = "models/magic-tuned-model"
    ):
        self.base_model_name = base_model_name
        self.model_save_path = Path(model_save_path)
        self._logger = logging.getLogger(__name__)
        
        # Ensure model directory exists
        self.model_save_path.mkdir(parents=True, exist_ok=True)
    
    async def fine_tune_model(
        self, 
        training_examples: List[InputExample],
        epochs: int = 3,
        batch_size: int = 16,
        learning_rate: float = 2e-5
    ) -> str:
        """
        Fine-tune the base model on magic-specific data.
        """
        if len(training_examples) < 10:
            raise ValueError(f"Need at least 10 training examples, got {len(training_examples)}")
        
        self._logger.info(f"Starting fine-tuning with {len(training_examples)} examples")
        
        try:
            # Load base model
            model = SentenceTransformer(self.base_model_name)
            
            # Split into train/validation
            train_examples = training_examples[:int(0.8 * len(training_examples))]
            val_examples = training_examples[int(0.8 * len(training_examples)):]
            
            # Create data loader
            train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
            
            # Define loss function (cosine similarity loss)
            train_loss = losses.CosineSimilarityLoss(model)
            
            # Create evaluator
            evaluator = None
            if val_examples:
                val_sentences1 = [ex.texts[0] for ex in val_examples]
                val_sentences2 = [ex.texts[1] for ex in val_examples]
                val_scores = [ex.label for ex in val_examples]
                
                evaluator = EmbeddingSimilarityEvaluator(
                    val_sentences1, val_sentences2, val_scores
                )
            
            # Training configuration
            warmup_steps = int(len(train_dataloader) * epochs * 0.1)
            
            # Fine-tune the model
            model.fit(
                train_objectives=[(train_dataloader, train_loss)],
                epochs=epochs,
                warmup_steps=warmup_steps,
                evaluator=evaluator,
                evaluation_steps=len(train_dataloader) // 2,
                output_path=str(self.model_save_path),
                save_best_model=True,
                show_progress_bar=True
            )
            
            self._logger.info(f"Fine-tuning completed. Model saved to {self.model_save_path}")
            return str(self.model_save_path)
            
        except Exception as e:
            self._logger.error(f"Error during fine-tuning: {str(e)}")
            raise
    
    def model_exists(self) -> bool:
        """Check if a fine-tuned model exists."""
        return (self.model_save_path / "pytorch_model.bin").exists()
    
    def get_model_info(self) -> Dict:
        """Get information about the fine-tuned model."""
        if not self.model_exists():
            return {"exists": False}
        
        try:
            # Try to load model info
            config_file = self.model_save_path / "config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            return {
                "exists": True,
                "path": str(self.model_save_path),
                "base_model": self.base_model_name,
                "config": config
            }
            
        except Exception as e:
            self._logger.error(f"Error getting model info: {str(e)}")
            return {"exists": True, "error": str(e)}


class AdaptiveTrickDetector:
    """
    Enhanced trick detector that can switch between base and fine-tuned models.
    """
    
    def __init__(
        self, 
        base_model_name: str = "all-MiniLM-L6-v2",
        fine_tuned_model_path: Optional[str] = None
    ):
        self.base_model_name = base_model_name
        self.fine_tuned_model_path = fine_tuned_model_path
        self._current_model = None
        self._logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize with the best available model."""
        try:
            # Try to load fine-tuned model first
            if (self.fine_tuned_model_path and 
                Path(self.fine_tuned_model_path).exists()):
                self._logger.info(f"Loading fine-tuned model: {self.fine_tuned_model_path}")
                self._current_model = SentenceTransformer(self.fine_tuned_model_path)
            else:
                # Fall back to base model
                self._logger.info(f"Loading base model: {self.base_model_name}")
                self._current_model = SentenceTransformer(self.base_model_name)
                
        except Exception as e:
            self._logger.error(f"Error loading model: {str(e)}")
            # Final fallback
            self._current_model = SentenceTransformer(self.base_model_name)
    
    async def switch_to_fine_tuned_model(self, model_path: str) -> bool:
        """Switch to a newly fine-tuned model."""
        try:
            if Path(model_path).exists():
                self._current_model = SentenceTransformer(model_path)
                self.fine_tuned_model_path = model_path
                self._logger.info(f"Switched to fine-tuned model: {model_path}")
                return True
            else:
                self._logger.warning(f"Fine-tuned model not found: {model_path}")
                return False
                
        except Exception as e:
            self._logger.error(f"Error switching to fine-tuned model: {str(e)}")
            return False
    
    def encode(self, sentences):
        """Encode sentences using current model."""
        if self._current_model is None:
            raise RuntimeError("Model not initialized")
        return self._current_model.encode(sentences)
    
    def get_current_model_info(self) -> Dict:
        """Get information about the currently loaded model."""
        return {
            "base_model": self.base_model_name,
            "fine_tuned_model": self.fine_tuned_model_path,
            "is_fine_tuned": self.fine_tuned_model_path is not None,
            "model_loaded": self._current_model is not None
        }
