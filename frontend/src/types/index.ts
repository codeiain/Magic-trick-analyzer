export interface Trick {
  id: string;
  name: string;
  effect_type: string;
  description: string;
  difficulty: string;
  props: string[];
  confidence?: number;
  page_start?: number;
  page_end?: number;
  created_at: string;
  book_title?: string;
  book_author?: string;
  method?: string;
  status?: 'pending' | 'approved' | 'rejected';
  reviewed?: boolean;
  source_document?: string;
  page_number?: number;
  keywords?: string[];
  updated_at?: string;
}

export interface TrickDetail extends Trick {
  book_id: string;
  updated_at: string;
}

export interface Book {
  id: string;
  title: string;
  author: string;
  publication_year?: number;
  isbn?: string;
  processed_at?: string;
  trick_count: number;
  created_at: string;
}

export interface BookDetail extends Book {
  file_path: string;
  updated_at: string;
  tricks: Trick[];
}

export interface CrossReference {
  id: string;
  source_trick_id: string;
  target_trick_id: string;
  relationship_type: string;
  similarity_score?: number;
  notes?: string;
  created_at: string;
}

export interface SearchResult {
  tricks: Trick[];
  total_count: number;
  returned_count: number;
  skip: number;
  limit: number;
}

export interface Statistics {
  total_books: number;
  total_tricks: number;
  processed_books: number;
  effect_distribution: Record<string, number>;
  difficulty_distribution: Record<string, number>;
  top_authors: [string, number][];
}

export interface ReviewStats {
  total_tricks: number;
  pending_review: number;
  accuracy: number;
  training_examples: number;
  correct_detections: number;
  incorrect_detections: number;
}

export interface Feedback {
  trick_id: string;
  is_correct: boolean;
  user_notes?: string;
  suggested_name?: string;
  suggested_description?: string;
}

export interface TrainingStatus {
  status: 'ready' | 'training' | 'completed' | 'error';
  progress: number;
  message: string;
  model_info?: Record<string, any>;
}

export interface ModelInfo {
  base_model: string;
  is_fine_tuned: boolean;
  fine_tuned_path?: string;
  model_exists: boolean;
  training_available: boolean;
}

export type ConfidenceLevel = 'high' | 'medium' | 'low';
export type EffectType = 'card_trick' | 'coin_magic' | 'mentalism' | 'stage_magic' | 'close_up' | 'other';
export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';

export interface SearchFilters {
  effect_type?: EffectType;
  difficulty?: DifficultyLevel;
  author?: string;
  book_title?: string;
  props?: string[];
  confidence_level?: ConfidenceLevel;
  page?: number;
  limit?: number;
  status?: 'all' | 'pending' | 'approved' | 'rejected';
  confidence_min?: number;
  include_book_info?: boolean;
}
