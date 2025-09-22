import { useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { BookOpenIcon, ArrowLeftIcon, StarIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import TrickCard from '../components/TrickCard';
import { booksApi, tricksApi } from '../lib/api';
import type { BookDetail, Trick } from '../types';

export default function BookDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [selectedTrick, setSelectedTrick] = useState<Trick | null>(null);
  const [userRating, setUserRating] = useState<number>(0);
  const [userReview, setUserReview] = useState<string>('');
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [scrollingToPage, setScrollingToPage] = useState<number | null>(null);
  const [showTrickDetails, setShowTrickDetails] = useState(false);
  
  // Refs for scroll functionality
  const bookContentRef = useRef<HTMLDivElement>(null);
  const contentTextRef = useRef<HTMLPreElement>(null);

  // Parse page markers from book content
  const parsePageMarkers = useCallback((content: string) => {
    const pageRegex = /--- Page (\d+) ---/g;
    const pages: { pageNumber: number; index: number }[] = [];
    let match;
    
    while ((match = pageRegex.exec(content)) !== null) {
      pages.push({
        pageNumber: parseInt(match[1]),
        index: match.index
      });
    }
    
    return pages.sort((a, b) => a.pageNumber - b.pageNumber);
  }, []);

  // Fetch book details
  const { data: book, isLoading: bookLoading, error: bookError } = useQuery<BookDetail>({
    queryKey: ['book', id],
    queryFn: async () => {
      if (!id) throw new Error('Book ID is required');
      return await booksApi.getById(id);
    },
    enabled: !!id
  });

  // Scroll to specific trick location
  const scrollToTrick = useCallback((trick: Trick) => {
    console.log('scrollToTrick called with:', trick.name, 'page_start:', trick.page_start);
    
    if (!book?.text_content || !contentTextRef.current) {
      console.log('Missing requirements:', { 
        hasBookContent: !!book?.text_content, 
        hasContentRef: !!contentTextRef.current 
      });
      return;
    }
    
    const pages = parsePageMarkers(book.text_content);
    console.log('Found pages:', pages.length, 'first few:', pages.slice(0, 5));
    
    if (pages.length === 0) return;
    
    // Find the page marker closest to the trick's page_start
    const targetPage = trick.page_start || 1;
    const targetPageData = pages.find(p => p.pageNumber >= targetPage) || pages[pages.length - 1];
    
    console.log('Target page:', targetPage, 'found page data:', targetPageData);
    
    if (targetPageData) {
      // Show which page we're scrolling to
      setScrollingToPage(targetPageData.pageNumber);
      
      // Calculate the relative position in the text content
      const textLength = book.text_content.length;
      const relativePosition = targetPageData.index / textLength;
      
      console.log('Scroll calculation:', {
        textLength,
        targetIndex: targetPageData.index,
        relativePosition
      });
      
      // Get the scrollable container
      const scrollContainer = bookContentRef.current;
      if (scrollContainer) {
        // Calculate scroll position based on the relative position in content
        const maxScroll = scrollContainer.scrollHeight - scrollContainer.clientHeight;
        const targetScroll = maxScroll * relativePosition;
        
        console.log('Container scroll info:', {
          scrollHeight: scrollContainer.scrollHeight,
          clientHeight: scrollContainer.clientHeight,
          maxScroll,
          targetScroll
        });
        
        // Smooth scroll to target position
        scrollContainer.scrollTo({
          top: targetScroll,
          behavior: 'smooth'
        });
        
        // Add a visual highlight effect and hide the page indicator
        setTimeout(() => {
          if (contentTextRef.current) {
            contentTextRef.current.style.background = 'linear-gradient(to right, rgba(59, 130, 246, 0.1), transparent)';
            setTimeout(() => {
              if (contentTextRef.current) {
                contentTextRef.current.style.background = '';
              }
              setScrollingToPage(null);
            }, 2000);
          }
        }, 500);
      } else {
        console.log('No scroll container found');
      }
    }
  }, [book?.text_content, parsePageMarkers]);

  // Fetch tricks for this book
  const { data: tricks = [], isLoading: tricksLoading } = useQuery<Trick[]>({
    queryKey: ['book-tricks', id],
    queryFn: async () => {
      if (!id || !book) return [];
      // Use the existing API with book_title filter as workaround
      const allTricks = await tricksApi.getAll({ 
        book_title: book?.title,
        limit: 100,
        include_book_info: true 
      });
      return allTricks.filter(trick => 
        trick.book_title === book?.title
      );
    },
    enabled: !!id && !!book
  });

  const handleTrickClick = (trick: Trick) => {
    // Set the selected trick for highlighting but don't show details by default
    setSelectedTrick(trick);
    // Always scroll to the trick's location in the book content
    scrollToTrick(trick);
  };

  const handleSubmitReview = () => {
    // Mock review submission - replace with actual API call
    console.log('Submitting review:', { rating: userRating, review: userReview });
    alert(`Review submitted! Rating: ${userRating}/5 stars`);
    setShowReviewForm(false);
  };

  if (bookLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (bookError || !book) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-lg font-semibold">Error loading book details</p>
          <button 
            onClick={() => navigate('/books')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Books
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-lg border-b border-slate-200/60 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/books')}
              className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <ArrowLeftIcon className="h-5 w-5 text-slate-600" />
            </button>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-amber-600 to-orange-700 rounded-xl flex items-center justify-center shadow-lg">
                <BookOpenIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">{book.title}</h1>
                <p className="text-slate-600">by {book.author}</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{tricks.length}</div>
              <div className="text-sm text-slate-500">Tricks</div>
            </div>
            <button
              onClick={() => setShowReviewForm(!showReviewForm)}
              className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 font-medium shadow-lg transition-all"
            >
              Rate & Review
            </button>
          </div>
        </div>
      </div>

      {/* Review Form */}
      {showReviewForm && (
        <div className="bg-purple-50/80 border-b border-purple-200/60 px-6 py-4">
          <div className="max-w-2xl">
            <h3 className="text-lg font-semibold text-purple-900 mb-4">Rate this book</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-purple-800 mb-2">Your Rating</label>
                <div className="flex items-center space-x-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setUserRating(star)}
                      className="p-1 hover:scale-110 transition-transform"
                    >
                      {star <= userRating ? (
                        <StarIconSolid className="h-6 w-6 text-yellow-500" />
                      ) : (
                        <StarIcon className="h-6 w-6 text-gray-300 hover:text-yellow-400" />
                      )}
                    </button>
                  ))}
                  <span className="ml-2 text-sm text-purple-700">
                    {userRating > 0 ? `${userRating}/5 stars` : 'Select a rating'}
                  </span>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-purple-800 mb-2">Your Review (optional)</label>
                <textarea
                  value={userReview}
                  onChange={(e) => setUserReview(e.target.value)}
                  placeholder="Share your thoughts about this book..."
                  className="w-full px-3 py-2 border border-purple-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                  rows={3}
                />
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleSubmitReview}
                  disabled={userRating === 0}
                  className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
                >
                  Submit Review
                </button>
                <button
                  onClick={() => setShowReviewForm(false)}
                  className="px-4 py-2 text-purple-600 hover:bg-purple-100 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Split View Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Book Content Reader */}
        <div className="w-1/2 flex flex-col border-r border-slate-200/60 bg-white/60">
          <div className="px-6 py-4 border-b border-slate-200/40 bg-white/80">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-800">
                Book Content
                {selectedTrick && (
                  <span className="ml-2 text-sm font-normal text-blue-600">
                    - Viewing: {selectedTrick.name}
                  </span>
                )}
              </h2>
              {scrollingToPage && (
                <div className="flex items-center space-x-2 animate-pulse">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                  <span className="text-sm text-blue-600 font-medium">
                    Scrolling to page {scrollingToPage}...
                  </span>
                </div>
              )}
              {selectedTrick && (
                <button
                  onClick={() => setShowTrickDetails(!showTrickDetails)}
                  className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                >
                  {showTrickDetails ? 'Show Book' : 'Show Details'}
                </button>
              )}
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6">
            {selectedTrick && showTrickDetails ? (
              // Show selected trick details only when toggle is on
              <div className="space-y-6">
                <div>
                  <h3 className="text-2xl font-bold text-slate-900 mb-3">
                    {selectedTrick.name}
                  </h3>
                  <div className="flex flex-wrap items-center gap-3 mb-4">
                    {selectedTrick.confidence !== undefined && (
                      <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
                        {Math.round(selectedTrick.confidence * 100)}% confidence
                      </div>
                    )}
                    {selectedTrick.effect_type && (
                      <div className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-semibold">
                        {selectedTrick.effect_type.replace('_', ' ')}
                      </div>
                    )}
                    {selectedTrick.difficulty && (
                      <div className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-sm font-semibold">
                        {selectedTrick.difficulty}
                      </div>
                    )}
                  </div>
                </div>

                {selectedTrick.description && (
                  <div>
                    <h4 className="font-semibold text-slate-900 text-lg mb-2">Description</h4>
                    <p className="text-slate-700 leading-relaxed">
                      {selectedTrick.description}
                    </p>
                  </div>
                )}

                {selectedTrick.method && (
                  <div>
                    <h4 className="font-semibold text-slate-900 text-lg mb-2">Method</h4>
                    <p className="text-slate-700 leading-relaxed">
                      {selectedTrick.method}
                    </p>
                  </div>
                )}

                {selectedTrick.props && selectedTrick.props.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-slate-900 text-lg mb-2">Required Props</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedTrick.props.map((prop, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-2 bg-amber-100 text-amber-800 text-sm rounded-lg font-medium"
                        >
                          {prop}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {(selectedTrick.page_start || selectedTrick.page_number) && (
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-slate-900 mb-2">Page Reference</h4>
                    <p className="text-slate-600">
                      Page {selectedTrick.page_start || selectedTrick.page_number}
                      {selectedTrick.page_end && selectedTrick.page_start !== selectedTrick.page_end && ` - ${selectedTrick.page_end}`}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              // Always show book content/reader by default
              <div className="space-y-6">
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 p-6 rounded-2xl border border-amber-200/60">
                  <div className="flex items-start space-x-4">
                    <div className="p-3 bg-amber-100 rounded-xl">
                      <BookOpenIcon className="h-8 w-8 text-amber-600" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-amber-900 mb-2">Book Information</h3>
                      <div className="space-y-2 text-amber-800">
                        <p><span className="font-semibold">Title:</span> {book.title}</p>
                        <p><span className="font-semibold">Author:</span> {book.author}</p>
                        {book.publication_year && (
                          <p><span className="font-semibold">Published:</span> {book.publication_year}</p>
                        )}
                        <p><span className="font-semibold">Tricks Detected:</span> {book.trick_count}</p>
                        {book.processed_at && (
                          <p><span className="font-semibold">Processed:</span> {new Date(book.processed_at).toLocaleDateString()}</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* User Rating/Review Display */}
                {(book.user_rating || book.user_review) && (
                  <div className="bg-purple-50 p-6 rounded-2xl border border-purple-200/60">
                    <h3 className="text-lg font-semibold text-purple-900 mb-3">Your Review</h3>
                    {book.user_rating && (
                      <div className="flex items-center space-x-2 mb-2">
                        <div className="flex">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <StarIconSolid 
                              key={star}
                              className={`h-5 w-5 ${star <= book.user_rating! ? 'text-yellow-500' : 'text-gray-300'}`}
                            />
                          ))}
                        </div>
                        <span className="text-sm text-purple-700">{book.user_rating}/5 stars</span>
                      </div>
                    )}
                    {book.user_review && (
                      <p className="text-purple-800 leading-relaxed">{book.user_review}</p>
                    )}
                  </div>
                )}

                {/* Book Content Reader */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200/60">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-slate-900">Book Content</h3>
                    {book.character_count && (
                      <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded-full">
                        {book.character_count.toLocaleString()} characters
                      </span>
                    )}
                  </div>
                  
                  <div className="max-h-96 overflow-y-auto bg-slate-50 p-4 rounded-lg border" ref={bookContentRef}>
                    {book.text_content ? (
                      <>
                        {book.ocr_confidence && (
                          <div className="mb-3 pb-3 border-b border-slate-200">
                            <div className="flex items-center justify-between text-xs text-slate-500">
                              <span>OCR Quality: {Math.round(book.ocr_confidence * 100)}%</span>
                              <span>Last processed: {book.processed_at ? new Date(book.processed_at).toLocaleDateString() : 'Unknown'}</span>
                            </div>
                          </div>
                        )}
                        <div className="prose prose-sm prose-slate max-w-none">
                          <pre 
                            ref={contentTextRef}
                            className="font-sans text-sm text-slate-700 leading-relaxed whitespace-pre-wrap overflow-wrap break-word transition-colors duration-1000"
                          >
                            {book.text_content}
                          </pre>
                        </div>
                      </>
                    ) : (
                      <div className="text-center py-12 text-slate-500">
                        <BookOpenIcon className="h-16 w-16 mx-auto mb-4 text-slate-300" />
                        <p className="font-medium">No text content available</p>
                        <p className="text-sm mt-1">
                          {book.processed_at ? 
                            'OCR processing may not have extracted readable text from this book' :
                            'This book has not been processed yet'
                          }
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="text-center text-slate-500">
                  <p className="text-sm">� Select a trick from the right panel to see detailed information</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Tricks List */}
        <div className="w-1/2 flex flex-col bg-white/30">
          <div className="px-6 py-4 border-b border-slate-200/40 bg-white/60">
            <h2 className="text-lg font-semibold text-slate-800">
              Tricks in this Book ({tricks.length})
            </h2>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {tricksLoading ? (
              <div className="flex items-center justify-center p-8">
                <LoadingSpinner />
              </div>
            ) : tricks.length > 0 ? (
              <div className="p-4 space-y-3">
                {tricks.map((trick) => (
                  <div 
                    key={trick.id} 
                    className={selectedTrick?.id === trick.id ? 'ring-2 ring-blue-500 rounded-lg' : ''}
                  >
                    <TrickCard
                      trick={trick}
                      showBookInfo={false}
                      onClick={handleTrickClick}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center p-8">
                <div className="text-center text-slate-500">
                  <BookOpenIcon className="h-12 w-12 mx-auto mb-2 text-slate-300" />
                  <p>No tricks found in this book</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}