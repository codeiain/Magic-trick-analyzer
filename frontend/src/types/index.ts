export interface BookSource {
  book_id: string;
  book_title: string;
  book_author: string;
  page_start?: number;
  page_end?: number;
  method?: string;
  confidence?: number;
}

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
  book_sources: BookSource[];
  similar_tricks: Trick[];
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
  content?: string;
  user_rating?: number;
  user_review?: string;
}

export interface BookDetail extends Book {
  file_path: string;
  updated_at: string;
  tricks: Trick[];
  text_content?: string;
  ocr_confidence?: number;
  character_count?: number;
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
  total_reviews: number;
  average_rating: number;
  pending_reviews: number;
  approved_reviews: number;
  rejected_reviews: number;
}

export interface ActiveOCRJob {
  job_id: string;
  book_title: string;
  status: 'queued' | 'started';
  created_at: string;
  file_path: string;
  progress?: number;
  message: string;
}

export interface ActiveOCRJobsResponse {
  active_ocr_jobs: ActiveOCRJob[];
  count: number;
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
