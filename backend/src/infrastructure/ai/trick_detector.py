"""
AI-powered trick detection using local models (no paid APIs).
Infrastructure layer implementation for detecting magic tricks in text.
Falls back to text-based detection when ML models unavailable.
"""
import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Optional ML imports with fallbacks
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    SentenceTransformer = None
    cosine_similarity = None

from ...domain.entities.magic import Trick
from ...domain.value_objects.common import (
    BookId, TrickId, Title, Props, PageRange, 
    DifficultyLevel, EffectType, Confidence
)


class TrickDetector:
    """
    AI-powered trick detector using local models.
    Uses sentence transformers and NLP to identify magic tricks in text.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._logger = logging.getLogger(__name__)
        self._model = None
        self._nlp = None
        self._model_name = model_name
        
        # Magic-specific patterns and keywords
        self._trick_patterns = self._initialize_trick_patterns()
        self._effect_keywords = self._initialize_effect_keywords()
        self._prop_keywords = self._initialize_prop_keywords()
        
    async def initialize(self):
        """Initialize AI models (lazy loading with fallback)."""
        self._logger.info("Initializing trick detection models...")
        
        if self._model is None:
            if ML_AVAILABLE:
                self._logger.info("Attempting to load sentence transformer model...")
                try:
                    # Try local model first
                    local_model_path = "/app/models/sentence-transformers/sentence-transformers_all-MiniLM-L6-v2"
                    if os.path.exists(local_model_path):
                        self._logger.info(f"Loading local model from {local_model_path}")
                        self._model = SentenceTransformer(local_model_path)
                        self._logger.info("Local sentence transformer model loaded successfully")
                    else:
                        # Fallback to trying to download (will likely fail if HuggingFace is blocked)
                        self._logger.info("Local model not found, attempting to download...")
                        self._model = SentenceTransformer(self._model_name)
                        self._logger.info("Downloaded sentence transformer model loaded successfully")
                except Exception as e:
                    self._logger.warning(f"Failed to load sentence transformer model: {e}")
                    self._logger.info("Using text-based detection fallback")
                    self._model = "fallback"
            else:
                self._logger.info("ML libraries not available, using text-based detection")
                self._model = "fallback"
            
        if self._nlp is None and SPACY_AVAILABLE:
            self._logger.info("Attempting to load spaCy model...")
            try:
                self._nlp = spacy.load("en_core_web_sm")
                self._logger.info("spaCy model loaded successfully")
            except OSError:
                self._logger.warning("spaCy model not found, using basic processing")
                self._nlp = None
        elif not SPACY_AVAILABLE:
            self._logger.info("spaCy not available, using basic text processing")
            self._nlp = None
    
    async def detect_tricks(self, text: str, book_id: BookId) -> List[Trick]:
        """
        Detect magic tricks in the given text.
        Returns a list of Trick entities with confidence scores.
        """
        await self.initialize()
        
        # Split text into sections (chapters, tricks, etc.)
        sections = self._split_into_sections(text)
        
        detected_tricks = []
        
        self._logger.info(f"Processing {len(sections)} sections for trick detection")
        
        for i, section in enumerate(sections):
            if i % 100 == 0:  # Log progress every 100 sections
                self._logger.info(f"Processing section {i}/{len(sections)}")
                
            tricks = await self._analyze_section(section, book_id, i)
            detected_tricks.extend(tricks)
            
            # Log first few candidates for debugging
            if i < 5 and tricks:
                self._logger.info(f"Section {i} found {len(tricks)} candidates")
        
        # Remove duplicates and low-confidence detections
        filtered_tricks = self._filter_and_deduplicate(detected_tricks)
        
        self._logger.info(f"Detected {len(filtered_tricks)} tricks from {len(sections)} sections")
        return filtered_tricks
    
    async def _analyze_section(self, section: str, book_id: BookId, section_index: int) -> List[Trick]:
        """Analyze a text section for magic tricks."""
        tricks = []
        
        # Extract potential trick names
        trick_candidates = self._extract_trick_candidates(section)
        
        # Log for debugging (only for first few sections)
        if section_index < 5 and trick_candidates:
            self._logger.info(f"Section {section_index}: Found {len(trick_candidates)} candidates")
        
        for candidate in trick_candidates:
            # Analyze the candidate
            analysis = await self._analyze_trick_candidate(candidate, section)
            
            if analysis['confidence'] > 0.3:  # Lower minimum confidence threshold
                trick = self._create_trick_from_analysis(
                    analysis, book_id, section_index
                )
                tricks.append(trick)
        
        return tricks
    
    def _split_into_sections(self, text: str) -> List[str]:
        """
        Split text into logical sections (chapters, tricks, etc.).
        Uses heuristics to identify section boundaries.
        """
        sections = []
        
        # Look for common section separators
        patterns = [
            r'\n\s*Chapter\s+\d+',
            r'\n\s*CHAPTER\s+[IVX]+',
            r'\n\s*\d+\.\s*[A-Z][^.\n]{10,}',  # Numbered sections
            r'\n\s*[A-Z][A-Z\s]{5,}[A-Z]\n',   # ALL CAPS headings
            r'\n\s*Effect:',                    # Magic book convention
            r'\n\s*Method:',                    # Magic book convention
            r'\n\s*THE\s+[A-Z][^.\n]{5,}',     # "THE TRICK NAME" format
            r'\n\s*[A-Z][^.\n]{10,}\n\s*\n',   # Title followed by blank line
        ]
        
        # Find all potential split points
        split_points = [0]
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            split_points.extend([m.start() for m in matches])
        
        split_points = sorted(set(split_points))
        split_points.append(len(text))
        
        # Create sections
        for i in range(len(split_points) - 1):
            start = split_points[i]
            end = split_points[i + 1]
            section = text[start:end].strip()
            
            if len(section) > 100:  # Minimum section length
                sections.append(section)
        
        return sections if sections else [text]  # Fallback to whole text
    
    def _extract_trick_candidates(self, section: str) -> List[Dict[str, Any]]:
        """Extract potential trick names and descriptions from a section."""
        candidates = []
        
        # Pattern 1: Effect/Method structure
        effect_match = re.search(r'Effect:\s*(.+?)(?=Method:|$)', section, re.DOTALL | re.IGNORECASE)
        method_match = re.search(r'Method:\s*(.+?)(?=Effect:|$)', section, re.DOTALL | re.IGNORECASE)
        
        if effect_match:
            candidates.append({
                'name': self._extract_trick_name_from_effect(effect_match.group(1)),
                'description': effect_match.group(1).strip(),
                'method': method_match.group(1).strip() if method_match else None,
                'full_text': section,
                'pattern_type': 'effect_method'
            })
        
        # Pattern 2: Titled sections (improved for Vernon's style)
        title_patterns = [
            r'^([A-Z][^.\n]{5,}?)\n\s*(.+?)(?=\n[A-Z][^.\n]{5,}|\Z)',
            r'^\d+\.\s*([^.\n]{5,}?)\n\s*(.+?)(?=^\d+\.|\Z)',
            r'^THE\s+([^.\n]{5,}?)\n\s*(.+?)(?=^THE\s+|\Z)',  # "THE TRICK NAME"
            r'^([A-Z\s]{10,})\n\s*(.+?)(?=^[A-Z\s]{10,}|\Z)',  # ALL CAPS titles
        ]
        
        for pattern in title_patterns:
            matches = re.finditer(pattern, section, re.MULTILINE | re.DOTALL)
            for match in matches:
                title = match.group(1).strip()
                content = match.group(2).strip()
                
                if self._looks_like_trick_title(title) and len(content) > 50:
                    candidates.append({
                        'name': title,
                        'description': content[:500],  # First 500 chars
                        'method': self._extract_method_from_content(content),
                        'full_text': match.group(0),
                        'pattern_type': 'titled_section'
                    })
        
        return candidates
    
    async def _analyze_trick_candidate(self, candidate: Dict[str, Any], full_section: str) -> Dict[str, Any]:
        """Analyze a trick candidate using AI and heuristics."""
        analysis = {
            'name': candidate['name'],
            'description': candidate['description'],
            'method': candidate.get('method'),
            'confidence': 0.0,
            'effect_type': EffectType.CLOSE_UP,  # Default
            'difficulty': DifficultyLevel.INTERMEDIATE,  # Default
            'props': [],
            'page_range': None
        }
        
        # Calculate confidence score
        confidence_factors = []
        
        # Factor 1: Pattern recognition confidence
        pattern_confidence = {
            'effect_method': 0.9,
            'titled_section': 0.7,
            'paragraph': 0.5
        }.get(candidate['pattern_type'], 0.5)
        confidence_factors.append(pattern_confidence)
        
        # Factor 2: Magic-specific vocabulary
        vocab_score = self._calculate_magic_vocabulary_score(candidate['description'])
        confidence_factors.append(vocab_score)
        
        # Factor 3: Structural indicators
        structure_score = self._calculate_structure_score(candidate['full_text'])
        confidence_factors.append(structure_score)
        
        # Factor 4: AI semantic similarity to known magic tricks (if available)
        if self._model and self._model != "fallback":
            semantic_score = await self._calculate_semantic_magic_score(candidate['description'])
            confidence_factors.append(semantic_score)
        else:
            # Fallback: use enhanced vocabulary scoring
            enhanced_vocab_score = self._calculate_enhanced_vocabulary_score(candidate['description'])
            confidence_factors.append(enhanced_vocab_score)
        
        # Combine confidence factors
        analysis['confidence'] = np.mean(confidence_factors)
        
        # Determine effect type
        analysis['effect_type'] = self._classify_effect_type(candidate['description'])
        
        # Determine difficulty
        analysis['difficulty'] = self._classify_difficulty(candidate['description'])
        
        # Extract props
        analysis['props'] = self._extract_props(candidate['description'])
        
        return analysis
    
    def _extract_trick_name_from_effect(self, effect_text: str) -> str:
        """Extract a trick name from effect description."""
        # Take first sentence or first 50 characters
        sentences = effect_text.split('.')
        if sentences:
            name = sentences[0].strip()
            if len(name) > 50:
                name = name[:47] + "..."
            return name
        return effect_text[:50].strip()
    
    def _looks_like_trick_title(self, title: str) -> bool:
        """Heuristic to check if text looks like a trick title."""
        if len(title) < 5 or len(title) > 100:
            return False
        
        # Should not be all caps (likely section header)
        if title.isupper():
            return False
        
        # Should not start with common non-trick words
        skip_words = ['chapter', 'introduction', 'conclusion', 'preface', 'about', 'contents']
        first_word = title.split()[0].lower()
        if first_word in skip_words:
            return False
        
        return True
    
    def _extract_method_from_content(self, content: str) -> Optional[str]:
        """Extract method description from content."""
        # Look for method indicators
        method_patterns = [
            r'Method:\s*(.+?)(?=\n\n|\Z)',
            r'How it\'s done:\s*(.+?)(?=\n\n|\Z)',
            r'Secret:\s*(.+?)(?=\n\n|\Z)',
            r'Working:\s*(.+?)(?=\n\n|\Z)'
        ]
        
        for pattern in method_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _calculate_magic_vocabulary_score(self, text: str) -> float:
        """Calculate score based on magic-specific vocabulary."""
        magic_terms = [
            'effect', 'method', 'secret', 'reveal', 'vanish', 'appear', 'transform',
            'palm', 'force', 'double lift', 'break', 'control', 'shuffle', 'cut',
            'spectator', 'audience', 'volunteer', 'deck', 'card', 'coin', 'ring',
            'silk', 'rope', 'magic', 'trick', 'illusion', 'mentalism', 'psychic',
            'prediction', 'mind reading', 'divination', 'esp', 'telepathy',
            'switch', 'steal', 'load', 'ditch', 'classic pass', 'elmsley count',
            'sleight', 'hand', 'finger', 'thumb', 'move', 'position', 'grip',
            'deal', 'dealing', 'pack', 'packet', 'selection', 'chosen', 'pick'
        ]
        
        text_lower = text.lower()
        found_terms = sum(1 for term in magic_terms if term in text_lower)
        
        return min(1.0, found_terms / 5.0)  # Normalize to 0-1, more sensitive
    
    def _calculate_structure_score(self, text: str) -> float:
        """Calculate score based on magic book structure."""
        score = 0.0
        
        # Look for common magic book structures
        if re.search(r'effect:\s*', text, re.IGNORECASE):
            score += 0.3
        if re.search(r'method:\s*', text, re.IGNORECASE):
            score += 0.3
        if re.search(r'props?\s*(needed|required):', text, re.IGNORECASE):
            score += 0.2
        if re.search(r'difficulty:\s*', text, re.IGNORECASE):
            score += 0.1
        if re.search(r'presentation:\s*', text, re.IGNORECASE):
            score += 0.1
        
        return min(1.0, score)
    
    async def _calculate_semantic_magic_score(self, text: str) -> float:
        """Calculate semantic similarity to magic concepts using AI."""
        if not ML_AVAILABLE or not cosine_similarity:
            return self._calculate_enhanced_vocabulary_score(text)
            
        magic_examples = [
            "A card trick where the spectator's chosen card appears at the top of the deck",
            "A coin vanishes from the magician's hand and reappears behind the spectator's ear",
            "The magician predicts which card the spectator will choose",
            "A rope is cut into pieces and then magically restored to one piece",
            "The magician reads the spectator's mind and reveals their thought"
        ]
        
        try:
            # Get embeddings
            text_embedding = self._model.encode([text])
            example_embeddings = self._model.encode(magic_examples)
            
            # Calculate similarities
            similarities = cosine_similarity(text_embedding, example_embeddings)[0]
            
            # Return highest similarity score
            return float(np.max(similarities))
            
        except Exception as e:
            self._logger.warning(f"Error calculating semantic score: {e}")
            return self._calculate_enhanced_vocabulary_score(text)

    def _calculate_enhanced_vocabulary_score(self, text: str) -> float:
        """Enhanced vocabulary scoring for fallback mode."""
        text_lower = text.lower()
        
        # Extended magic vocabulary with weights
        weighted_terms = {
            # High-value magic-specific terms
            'effect': 0.15, 'method': 0.15, 'secret': 0.10, 'reveal': 0.08,
            'vanish': 0.12, 'appear': 0.10, 'transform': 0.10, 'illusion': 0.12,
            
            # Techniques and moves
            'palm': 0.08, 'force': 0.08, 'double lift': 0.12, 'break': 0.06,
            'control': 0.08, 'shuffle': 0.06, 'cut': 0.04, 'switch': 0.08,
            'classic pass': 0.15, 'elmsley count': 0.15,
            
            # Performance terms
            'spectator': 0.08, 'audience': 0.06, 'volunteer': 0.08, 'presentation': 0.08,
            
            # Props
            'deck': 0.08, 'card': 0.06, 'coin': 0.08, 'ring': 0.06, 'silk': 0.08,
            'rope': 0.08, 'wand': 0.08, 'hat': 0.06,
            
            # Types of magic
            'mentalism': 0.12, 'psychic': 0.10, 'prediction': 0.10, 'mind reading': 0.12,
            'divination': 0.10, 'esp': 0.10, 'telepathy': 0.10,
            
            # Common magic words
            'magic': 0.08, 'trick': 0.08, 'magical': 0.08, 'mysterious': 0.06,
            'impossible': 0.08, 'miracle': 0.08
        }
        
        total_score = 0.0
        for term, weight in weighted_terms.items():
            if term in text_lower:
                # Bonus for multiple occurrences but with diminishing returns
                occurrences = text_lower.count(term)
                score = weight * (1 + 0.2 * min(occurrences - 1, 3))
                total_score += score
        
        # Normalize to 0-1 range
        return min(1.0, total_score)
    
    
    def _classify_effect_type(self, text: str) -> EffectType:
        """Classify the effect type based on text content."""
        text_lower = text.lower()
        
        # Effect type keywords mapping
        type_keywords = {
            EffectType.CARD_TRICK: ['card', 'deck', 'shuffle', 'deal', 'ace', 'king', 'queen'],
            EffectType.COIN_MAGIC: ['coin', 'penny', 'quarter', 'dollar', 'change', 'palm'],
            EffectType.MENTALISM: ['mind', 'thought', 'predict', 'esp', 'telepathy', 'psychic'],
            EffectType.STAGE_MAGIC: ['stage', 'platform', 'large', 'theater', 'audience'],
            EffectType.CLOSE_UP: ['close', 'intimate', 'small group', 'table', 'parlor'],
            EffectType.VANISH: ['vanish', 'disappear', 'gone', 'invisible'],
            EffectType.PRODUCTION: ['appear', 'produce', 'materialize', 'manifest'],
            EffectType.TRANSFORMATION: ['change', 'transform', 'morph', 'convert'],
            EffectType.RESTORATION: ['restore', 'repair', 'fix', 'mend', 'whole again'],
            EffectType.PREDICTION: ['predict', 'prophecy', 'foretell', 'future'],
            EffectType.MIND_READING: ['mind reading', 'thoughts', 'telepathy']
        }
        
        # Score each effect type
        scores = {}
        for effect_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[effect_type] = score
        
        # Return highest scoring type or default
        if scores:
            return max(scores.keys(), key=lambda k: scores[k])
        
        return EffectType.CLOSE_UP  # Default
    
    def _classify_difficulty(self, text: str) -> DifficultyLevel:
        """Classify difficulty based on text indicators."""
        text_lower = text.lower()
        
        difficulty_keywords = {
            DifficultyLevel.BEGINNER: ['easy', 'simple', 'basic', 'beginner', 'learn', 'first'],
            DifficultyLevel.INTERMEDIATE: ['intermediate', 'moderate', 'some practice'],
            DifficultyLevel.ADVANCED: ['advanced', 'difficult', 'challenging', 'skill required'],
            DifficultyLevel.EXPERT: ['expert', 'master', 'professional', 'years of practice']
        }
        
        for difficulty, keywords in difficulty_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return difficulty
        
        return DifficultyLevel.INTERMEDIATE  # Default
    
    def _extract_props(self, text: str) -> List[str]:
        """Extract required props from text."""
        props = []
        text_lower = text.lower()
        
        # Common magic props
        prop_patterns = [
            r'deck of cards?', r'cards?', r'coins?', r'rings?', r'ropes?',
            r'silk', r'handkerchief', r'rubber bands?', r'cups?', r'balls?',
            r'wand', r'top hat', r'table', r'chair', r'box', r'envelope'
        ]
        
        for pattern in prop_patterns:
            if re.search(pattern, text_lower):
                # Extract the actual prop name
                match = re.search(pattern, text_lower)
                if match:
                    prop = match.group().title()
                    if prop not in props:
                        props.append(prop)
        
        return props
    
    def _create_trick_from_analysis(
        self, 
        analysis: Dict[str, Any], 
        book_id: BookId, 
        section_index: int
    ) -> Trick:
        """Create a Trick entity from analysis results."""
        return Trick(
            name=Title(analysis['name']),
            book_id=book_id,
            effect_type=analysis['effect_type'],
            description=analysis['description'],
            method=analysis.get('method'),
            props=Props(analysis['props']),
            difficulty=analysis['difficulty'],
            page_range=PageRange(section_index + 1),  # Approximate page
            confidence=Confidence(analysis['confidence'])
        )
    
    def _filter_and_deduplicate(self, tricks: List[Trick]) -> List[Trick]:
        """Filter low confidence tricks and remove duplicates."""
        # Filter by confidence
        filtered = [trick for trick in tricks if trick.confidence.value > 0.3]
        
        # Simple deduplication by name similarity
        unique_tricks = []
        for trick in filtered:
            is_duplicate = False
            for existing in unique_tricks:
                if self._are_trick_names_similar(str(trick.name), str(existing.name)):
                    # Keep the one with higher confidence
                    if trick.confidence.value > existing.confidence.value:
                        unique_tricks.remove(existing)
                        unique_tricks.append(trick)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_tricks.append(trick)
        
        return unique_tricks
    
    def _are_trick_names_similar(self, name1: str, name2: str) -> bool:
        """Check if two trick names are similar (potential duplicates)."""
        # Simple similarity check - more sophisticated could use edit distance
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity > 0.8
    
    def _initialize_trick_patterns(self) -> List[str]:
        """Initialize regex patterns for trick detection."""
        return [
            r'Effect:\s*(.+?)Method:',
            r'Trick:\s*(.+?)(?=Trick:|$)',
            r'EFFECT\s*(.+?)METHOD',
            r'\d+\.\s*([A-Z][^.\n]+)\n'
        ]
    
    def _initialize_effect_keywords(self) -> Dict[str, List[str]]:
        """Initialize keywords for effect classification."""
        return {
            'card': ['card', 'deck', 'ace', 'king', 'queen', 'jack', 'suit'],
            'coin': ['coin', 'penny', 'quarter', 'dollar', 'change'],
            'mentalism': ['mind', 'thought', 'predict', 'telepathy', 'psychic'],
            'stage': ['stage', 'platform', 'theater', 'large audience'],
            'close_up': ['close', 'intimate', 'table', 'small group']
        }
    
    def _initialize_prop_keywords(self) -> List[str]:
        """Initialize prop detection keywords."""
        return [
            'cards', 'deck', 'coins', 'rope', 'silk', 'handkerchief',
            'rings', 'balls', 'cups', 'wand', 'hat', 'box', 'envelope'
        ]
