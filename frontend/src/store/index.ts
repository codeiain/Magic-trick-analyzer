import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Trick, Book, ReviewStats, SearchFilters } from '@/types';

interface AppState {
  // Data
  tricks: Trick[];
  books: Book[];
  reviewStats: ReviewStats | null;
  
  // UI State
  isLoading: boolean;
  error: string | null;
  selectedTrick: Trick | null;
  searchFilters: SearchFilters;
  
  // Pagination
  currentPage: number;
  totalPages: number;
  itemsPerPage: number;
  
  // Actions
  setTricks: (tricks: Trick[]) => void;
  setBooks: (books: Book[]) => void;
  setReviewStats: (stats: ReviewStats) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSelectedTrick: (trick: Trick | null) => void;
  setSearchFilters: (filters: SearchFilters) => void;
  clearFilters: () => void;
  setCurrentPage: (page: number) => void;
  setItemsPerPage: (items: number) => void;
  reset: () => void;
}

const initialState = {
  tricks: [],
  books: [],
  reviewStats: null,
  isLoading: false,
  error: null,
  selectedTrick: null,
  searchFilters: {},
  currentPage: 1,
  totalPages: 1,
  itemsPerPage: 20,
};

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      ...initialState,
      
      setTricks: (tricks) => set({ tricks }),
      setBooks: (books) => set({ books }),
      setReviewStats: (reviewStats) => set({ reviewStats }),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
      setSelectedTrick: (selectedTrick) => set({ selectedTrick }),
      
      setSearchFilters: (filters) => 
        set((state) => ({ 
          searchFilters: { ...state.searchFilters, ...filters },
          currentPage: 1, // Reset to first page when filters change
        })),
      
      clearFilters: () => 
        set({ 
          searchFilters: {},
          currentPage: 1,
        }),
      
      setCurrentPage: (currentPage) => set({ currentPage }),
      setItemsPerPage: (itemsPerPage) => set({ itemsPerPage, currentPage: 1 }),
      
      reset: () => set(initialState),
    }),
    {
      name: 'magic-trick-analyzer-store',
    }
  )
);

// Selectors for computed values
export const useFilteredTricks = () => {
  const { tricks, searchFilters } = useAppStore();
  
  return tricks.filter((trick) => {
    if (searchFilters.effect_type && trick.effect_type !== searchFilters.effect_type) {
      return false;
    }
    
    if (searchFilters.difficulty && trick.difficulty !== searchFilters.difficulty) {
      return false;
    }
    
    if (searchFilters.author && !trick.book_author?.toLowerCase().includes(searchFilters.author.toLowerCase())) {
      return false;
    }
    
    if (searchFilters.book_title && !trick.book_title?.toLowerCase().includes(searchFilters.book_title.toLowerCase())) {
      return false;
    }
    
    if (searchFilters.confidence_level && trick.confidence) {
      const confidence = trick.confidence;
      switch (searchFilters.confidence_level) {
        case 'high':
          if (confidence <= 0.8) return false;
          break;
        case 'medium':
          if (confidence <= 0.6 || confidence > 0.8) return false;
          break;
        case 'low':
          if (confidence > 0.6) return false;
          break;
      }
    }
    
    if (searchFilters.props && searchFilters.props.length > 0) {
      const hasAllProps = searchFilters.props.every(prop =>
        trick.props.some(trickProp => 
          trickProp.toLowerCase().includes(prop.toLowerCase())
        )
      );
      if (!hasAllProps) return false;
    }
    
    return true;
  });
};
