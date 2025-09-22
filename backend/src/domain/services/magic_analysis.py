"""
Domain services for the Magic Trick Analyzer.
These contain business logic that doesn't naturally fit within entities.
Following Domain-Driven Design principles.
"""
from typing import List, Set
from abc import ABC, abstractmethod

from ..entities.magic import Book, Trick, CrossReference
from ..value_objects.common import TrickId, Confidence


class TrickAnalysisService:
    """
    Domain service for analyzing tricks and identifying relationships.
    Contains business logic for trick comparison and classification.
    """
    
    def __init__(self):
        self._similarity_threshold = 0.7
        self._high_confidence_threshold = 0.8
    
    def are_tricks_similar(self, trick1: Trick, trick2: Trick) -> bool:
        """
        Determine if two tricks are similar based on domain rules.
        This is pure business logic, independent of AI implementation.
        """
        if trick1.effect_type != trick2.effect_type:
            return False
        
        # Check if they share significant props
        shared_props = self._calculate_shared_props(trick1, trick2)
        if shared_props < 0.5:  # Less than 50% shared props
            return False
        
        # Additional domain-specific similarity rules can be added here
        return True
    
    def determine_relationship_type(self, source: Trick, target: Trick) -> str:
        """
        Determine the type of relationship between two tricks.
        Based on domain knowledge of magic relationships.
        """
        if source.effect_type == target.effect_type:
            if self._are_method_variations(source, target):
                return "variation"
            elif self._have_similar_props(source, target):
                return "similar"
            else:
                return "related"
        else:
            return "reference"
    
    def calculate_trick_complexity_score(self, trick: Trick) -> float:
        """
        Calculate a complexity score for a trick based on domain rules.
        """
        base_score = {
            "beginner": 1.0,
            "intermediate": 2.0, 
            "advanced": 3.0,
            "expert": 4.0
        }.get(trick.difficulty.value, 2.0)
        
        # Adjust based on number of props required
        prop_modifier = len(trick.props) * 0.1
        
        # Adjust based on effect type complexity
        effect_modifier = self._get_effect_complexity_modifier(trick.effect_type)
        
        return min(5.0, base_score + prop_modifier + effect_modifier)
    
    def _calculate_shared_props(self, trick1: Trick, trick2: Trick) -> float:
        """Calculate the percentage of shared props between two tricks."""
        if len(trick1.props) == 0 and len(trick2.props) == 0:
            return 1.0
        
        if len(trick1.props) == 0 or len(trick2.props) == 0:
            return 0.0
        
        props1 = set(trick1.props.items)
        props2 = set(trick2.props.items)
        
        intersection = props1.intersection(props2)
        union = props1.union(props2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _are_method_variations(self, trick1: Trick, trick2: Trick) -> bool:
        """Check if tricks are method variations of each other."""
        # This would involve more sophisticated analysis
        # For now, simplified logic
        return (trick1.method is not None and 
                trick2.method is not None and
                len(set(trick1.method.lower().split()).intersection(
                    set(trick2.method.lower().split()))) > 3)
    
    def _have_similar_props(self, trick1: Trick, trick2: Trick) -> bool:
        """Check if tricks have similar prop requirements."""
        return self._calculate_shared_props(trick1, trick2) > 0.6
    
    def _get_effect_complexity_modifier(self, effect_type: str) -> float:
        """Get complexity modifier based on effect type."""
        complexity_map = {
            "Card": 0.1,
            "Coin": 0.2,
            "Close-Up": 0.1,
            "Stage Magic": 0.5,
            "Mentalism": 0.3,
            "Vanish": 0.2,
            "Production": 0.3,
            "Transformation": 0.4,
            "Restoration": 0.4,
            "Prediction": 0.3,
            "Mind Reading": 0.4
        }
        return complexity_map.get(effect_type, 0.2)


class CrossReferenceService:
    """
    Domain service for managing cross-references between tricks.
    """
    
    def __init__(self, trick_analysis_service: TrickAnalysisService):
        self._analysis_service = trick_analysis_service
    
    def create_cross_reference(
        self, 
        source_trick: Trick, 
        target_trick: Trick,
        similarity_score: float,
        notes: str = None
    ) -> CrossReference:
        """
        Create a cross reference between two tricks.
        """
        relationship_type = self._analysis_service.determine_relationship_type(
            source_trick, target_trick
        )
        
        return CrossReference(
            source_trick_id=source_trick.id,
            target_trick_id=target_trick.id,
            relationship_type=relationship_type,
            similarity_score=Confidence(similarity_score),
            notes=notes
        )
    
    def should_create_cross_reference(
        self, 
        source_trick: Trick, 
        target_trick: Trick,
        similarity_score: float
    ) -> bool:
        """
        Determine if a cross reference should be created based on domain rules.
        """
        if source_trick.id == target_trick.id:
            return False
        
        if similarity_score < 0.6:  # Below minimum similarity threshold
            return False
        
        if not self._analysis_service.are_tricks_similar(source_trick, target_trick):
            return False
        
        return True
    
    def filter_meaningful_cross_references(
        self, 
        cross_references: List[CrossReference]
    ) -> List[CrossReference]:
        """
        Filter cross references to keep only meaningful ones.
        """
        # Remove low-confidence cross references
        filtered = [
            ref for ref in cross_references 
            if ref.similarity_score is None or ref.similarity_score.value >= 0.6
        ]
        
        # Group by relationship type and keep top N per type
        # Implementation would group and limit results
        
        return filtered


class BookAnalysisService:
    """
    Domain service for analyzing books and their content.
    """
    
    def calculate_book_complexity(self, book: Book) -> float:
        """
        Calculate overall complexity of a book based on its tricks.
        """
        if not book.tricks:
            return 0.0
        
        analysis_service = TrickAnalysisService()
        total_complexity = sum(
            analysis_service.calculate_trick_complexity_score(trick)
            for trick in book.tricks
        )
        
        return total_complexity / len(book.tricks)
    
    def get_book_effect_distribution(self, book: Book) -> dict[str, int]:
        """
        Get the distribution of effect types in a book.
        """
        distribution = {}
        for trick in book.tricks:
            effect_type = trick.effect_type
            distribution[effect_type] = distribution.get(effect_type, 0) + 1
        
        return distribution
    
    def find_book_signature_tricks(self, book: Book) -> List[Trick]:
        """
        Find tricks that are signature/unique to this book.
        These are high-confidence tricks with few cross-references.
        """
        signature_tricks = []
        
        for trick in book.tricks:
            if (trick.is_high_confidence() and 
                len(trick.cross_references) <= 2):  # Few similar tricks in other books
                signature_tricks.append(trick)
        
        return signature_tricks
    
    def is_book_beginner_friendly(self, book: Book) -> bool:
        """
        Determine if a book is beginner-friendly based on trick complexity.
        """
        if not book.tricks:
            return False
        
        beginner_tricks = [
            trick for trick in book.tricks 
            if trick.difficulty.value in ["beginner", "intermediate"]
        ]
        
        return len(beginner_tricks) / len(book.tricks) >= 0.7
