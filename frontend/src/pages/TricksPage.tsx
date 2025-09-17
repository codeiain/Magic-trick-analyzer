import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MagnifyingGlassIcon, FunnelIcon, SparklesIcon, BookOpenIcon } from '@heroicons/react/24/outline';
import TrickCard from '../components/TrickCard';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Pagination from '../components/ui/Pagination';
import { tricksApi } from '../lib/api';
import type { Trick, EffectType, DifficultyLevel } from '../types';

export default function TricksPage() {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [effectType, setEffectType] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [selectedTrick, setSelectedTrick] = useState<Trick | null>(null);
  const itemsPerPage = 20; // Reduced for better two-column layout

  const { data: tricks = [], isLoading, error } = useQuery({
    queryKey: ['tricks', currentPage, searchTerm, effectType, difficulty],
    queryFn: () => tricksApi.getAll({
      page: currentPage,
      limit: itemsPerPage,
      book_title: searchTerm || undefined,
      effect_type: effectType as EffectType || undefined,
      difficulty: difficulty as DifficultyLevel || undefined,
      include_book_info: true
    })
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1); // Reset to first page when searching
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleTrickClick = (trick: Trick) => {
    setSelectedTrick(trick);
  };

  // For now, we'll estimate total count since the API doesn't return it
  // In a real implementation, you'd want to modify the backend to return total count
  const estimatedTotal = tricks.length === itemsPerPage ? currentPage * itemsPerPage + 1 : (currentPage - 1) * itemsPerPage + tricks.length;

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Modern Header */}
      <div className="bg-white/80 backdrop-blur-lg border-b border-slate-200/60 px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent">
                Magic Tricks Collection
              </h1>
              <p className="text-slate-600 mt-1 font-medium">Discover and explore magical effects from your library</p>
            </div>
            
            {/* Stats */}
            <div className="flex items-center gap-6 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{tricks.length}</div>
                <div className="text-slate-500 font-medium">Tricks</div>
              </div>
              {selectedTrick && (
                <div className="text-center">
                  <div className="text-2xl font-bold text-emerald-600">{Math.round((selectedTrick.confidence || 0) * 100)}%</div>
                  <div className="text-slate-500 font-medium">Confidence</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modern Filters */}
      <div className="bg-white/60 backdrop-blur-sm border-b border-slate-200/40 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div className="md:col-span-2">
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
                  <input
                    id="search"
                    type="text"
                    placeholder="Search tricks or book titles..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 bg-white/80 border border-slate-200/80 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder-slate-500 font-medium shadow-sm transition-all"
                  />
                </div>
              </div>

              {/* Effect Type */}
              <div>
                <select
                  value={effectType}
                  onChange={(e) => setEffectType(e.target.value)}
                  className="w-full px-4 py-3 bg-white/80 border border-slate-200/80 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 font-medium shadow-sm transition-all"
                >
                  <option value="">All Effect Types</option>
                  <option value="card_trick">Card Tricks</option>
                  <option value="coin_magic">Coin Magic</option>
                  <option value="mentalism">Mentalism</option>
                  <option value="stage_magic">Stage Magic</option>
                  <option value="close_up">Close-up</option>
                  <option value="card_force">Card Force</option>
                  <option value="vanish">Vanish</option>
                  <option value="production">Production</option>
                  <option value="transformation">Transformation</option>
                </select>
              </div>

              {/* Difficulty */}
              <div>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  className="w-full px-4 py-3 bg-white/80 border border-slate-200/80 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 font-medium shadow-sm transition-all"
                >
                  <option value="">All Difficulties</option>
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                  <option value="expert">Expert</option>
                </select>
              </div>
            </div>
          </form>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="flex-1 flex overflow-hidden">
        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <LoadingSpinner size="lg" />
              <p className="mt-4 text-slate-600 font-medium">Loading magical discoveries...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center text-red-600">
              <p className="text-lg font-semibold">Error loading tricks</p>
              <p className="mt-2">{String(error)}</p>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex">
            {/* Left Column - Tricks List */}
            <div className="w-1/2 flex flex-col border-r border-slate-200/60 bg-white/30">
              <div className="px-6 py-4 border-b border-slate-200/40 bg-white/60">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-semibold text-slate-800">
                    Tricks ({tricks.length})
                  </h2>
                  {currentPage > 1 && (
                    <span className="text-sm text-slate-500 font-medium">Page {currentPage}</span>
                  )}
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto">
                {tricks.length > 0 ? (
                  <div className="p-4 space-y-3">
                    {tricks.map((trick: Trick) => (
                      <div key={trick.id} className={selectedTrick?.id === trick.id ? 'ring-2 ring-blue-500 rounded-lg' : ''}>
                        <TrickCard 
                          trick={trick} 
                          showBookInfo={true}
                          onClick={handleTrickClick}
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center p-8">
                    <div className="text-center">
                      <FunnelIcon className="mx-auto h-16 w-16 text-slate-300 mb-4" />
                      <h3 className="text-lg font-semibold text-slate-600 mb-2">No tricks found</h3>
                      <p className="text-slate-500">Try adjusting your search or filters.</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Pagination */}
              {tricks.length > 0 && (
                <div className="px-4 py-4 border-t border-slate-200/40 bg-white/60">
                  <Pagination
                    currentPage={currentPage}
                    totalItems={estimatedTotal}
                    itemsPerPage={itemsPerPage}
                    onPageChange={handlePageChange}
                  />
                </div>
              )}
            </div>

            {/* Right Column - Trick Details */}
            <div className="w-1/2 flex flex-col bg-white/60">
              {selectedTrick ? (
                <>
                  <div className="px-6 py-4 border-b border-slate-200/40 bg-white/80">
                    <h2 className="text-lg font-semibold text-slate-800">Trick Details</h2>
                  </div>
                  <div className="flex-1 overflow-y-auto p-6">
                    <div className="space-y-6">
                      {/* Title and Basic Info */}
                      <div>
                        <h3 className="text-2xl font-bold text-slate-900 mb-3">
                          {selectedTrick.name}
                        </h3>
                        <div className="flex flex-wrap items-center gap-3">
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

                      {/* Book Information */}
                      {(selectedTrick.book_title || selectedTrick.book_author) && (
                        <div className="bg-gradient-to-r from-slate-50 to-blue-50 p-6 rounded-2xl border border-slate-200/60">
                          <div className="flex items-start space-x-4">
                            <div className="p-2 bg-blue-100 rounded-lg">
                              <BookOpenIcon className="h-6 w-6 text-blue-600" />
                            </div>
                            <div className="flex-1">
                              <h4 className="font-semibold text-slate-900 mb-2">Source Book</h4>
                              {selectedTrick.book_title && (
                                <p className="text-slate-800 font-medium text-lg">{selectedTrick.book_title}</p>
                              )}
                              {selectedTrick.book_author && (
                                <p className="text-slate-600 mt-1">by {selectedTrick.book_author}</p>
                              )}
                              {(selectedTrick.page_start || selectedTrick.page_number) && (
                                <p className="text-slate-500 text-sm mt-2">
                                  Page {selectedTrick.page_start || selectedTrick.page_number}
                                  {selectedTrick.page_end && selectedTrick.page_start !== selectedTrick.page_end && ` - ${selectedTrick.page_end}`}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Description */}
                      {selectedTrick.description && (
                        <div className="space-y-3">
                          <h4 className="font-semibold text-slate-900 text-lg">Description</h4>
                          <p className="text-slate-700 leading-relaxed text-base">
                            {selectedTrick.description}
                          </p>
                        </div>
                      )}

                      {/* Method */}
                      {selectedTrick.method && (
                        <div className="space-y-3">
                          <h4 className="font-semibold text-slate-900 text-lg">Method</h4>
                          <p className="text-slate-700 leading-relaxed text-base">
                            {selectedTrick.method}
                          </p>
                        </div>
                      )}

                      {/* Props */}
                      {selectedTrick.props && selectedTrick.props.length > 0 && (
                        <div className="space-y-3">
                          <h4 className="font-semibold text-slate-900 text-lg">Required Props</h4>
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

                      {/* Keywords */}
                      {selectedTrick.keywords && selectedTrick.keywords.length > 0 && (
                        <div className="space-y-3">
                          <h4 className="font-semibold text-slate-900 text-lg">Keywords</h4>
                          <div className="flex flex-wrap gap-2">
                            {selectedTrick.keywords.map((keyword, idx) => (
                              <span
                                key={idx}
                                className="px-3 py-2 bg-slate-100 text-slate-700 text-sm rounded-lg font-medium"
                              >
                                {keyword}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Source Document */}
                      {selectedTrick.source_document && (
                        <div className="space-y-3">
                          <h4 className="font-semibold text-slate-900 text-lg">Source Document</h4>
                          <p className="text-slate-600 text-sm font-mono bg-slate-100 p-3 rounded-lg border">
                            {selectedTrick.source_document}
                          </p>
                        </div>
                      )}

                      {/* Timestamps */}
                      <div className="pt-6 border-t border-slate-200 text-xs text-slate-500 space-y-1">
                        <p><span className="font-medium">Created:</span> {new Date(selectedTrick.created_at).toLocaleString()}</p>
                        {selectedTrick.updated_at && (
                          <p><span className="font-medium">Updated:</span> {new Date(selectedTrick.updated_at).toLocaleString()}</p>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center p-8">
                  <div className="text-center">
                    <SparklesIcon className="mx-auto h-16 w-16 text-slate-300 mb-4" />
                    <h3 className="text-lg font-semibold text-slate-600 mb-2">Select a trick to explore</h3>
                    <p className="text-slate-500">Click on any trick to see its detailed information.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
