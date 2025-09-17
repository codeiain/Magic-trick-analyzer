import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { CheckIcon, XMarkIcon, BookOpenIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import TrickDetailModal from '../components/TrickDetailModal';
import Pagination from '../components/ui/Pagination';
import { reviewApi } from '../lib/api';
import type { Trick } from '../types';

export default function ReviewPage() {
  const [selectedTrick, setSelectedTrick] = useState<Trick | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  const { data: pendingTricks = [], isLoading, refetch } = useQuery({
    queryKey: ['pending-reviews', currentPage],
    queryFn: () => reviewApi.getPendingReviews()
  });

  const handleReview = async (trickId: string, approved: boolean) => {
    try {
      await reviewApi.updateTrickReview(trickId, { approved, reviewed: true });
      await refetch();
      if (selectedTrick?.id === trickId) {
        setSelectedTrick(null);
        setIsModalOpen(false);
      }
    } catch (error) {
      console.error('Failed to update review:', error);
    }
  };

  const handleTrickClick = (trick: Trick) => {
    setSelectedTrick(trick);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedTrick(null);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Paginate the results client-side for now
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedTricks = pendingTricks.slice(startIndex, endIndex);

  return (
    <div className="h-full bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      {/* Modern Header */}
      <div className="mb-8">
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/25">
              <span className="text-2xl">✨</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-emerald-800 bg-clip-text text-transparent">
                Review AI Detections
              </h1>
              <p className="text-slate-600 font-medium">Review and approve magic tricks detected by the AI</p>
            </div>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-xl border border-white/20 p-8">
          {/* Tricks List */}
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                  <span className="text-sm">📋</span>
                </div>
                <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-blue-800 bg-clip-text text-transparent">
                  Pending Reviews ({pendingTricks.length})
                </h2>
              </div>
              {pendingTricks.length > itemsPerPage && (
                <p className="text-sm text-slate-500 font-medium bg-white/60 backdrop-blur-sm px-3 py-1 rounded-lg border border-white/30">
                  Showing {startIndex + 1}-{Math.min(endIndex, pendingTricks.length)} of {pendingTricks.length}
                </p>
              )}
            </div>
            
            {pendingTricks.length === 0 ? (
              <div className="text-center py-12 bg-gradient-to-br from-slate-50 to-blue-50/50 rounded-2xl border border-slate-200/50">
                <div className="w-16 h-16 bg-white/80 backdrop-blur-sm rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                  <CheckIcon className="w-8 h-8 text-emerald-500" />
                </div>
                <p className="text-lg font-semibold text-slate-700 mb-2">No pending reviews</p>
                <p className="text-slate-500 font-medium">All detected tricks have been reviewed!</p>
              </div>
            ) : (
              <>
                <div className="space-y-4">
                  {paginatedTricks.map((trick: Trick) => (
                    <div
                      key={trick.id}
                      className={`p-6 rounded-2xl cursor-pointer transition-all duration-300 hover:-translate-y-1 hover:shadow-lg border ${
                        selectedTrick?.id === trick.id
                          ? 'bg-gradient-to-br from-blue-50 to-indigo-50/50 border-blue-200/60 shadow-lg shadow-blue-500/20'
                          : 'bg-white/60 backdrop-blur-sm border-white/40 hover:bg-white/80 hover:border-white/60'
                      }`}
                      onClick={() => handleTrickClick(trick)}
                    >
                      <div className="space-y-4">
                        <div className="flex justify-between items-start">
                          <div className="flex-1 min-w-0">
                            <h3 className="text-lg font-bold text-slate-800 truncate">{trick.name}</h3>
                            <div className="flex items-center space-x-2 mt-1">
                              <span className="text-sm font-semibold text-slate-600">Confidence:</span>
                              <div className="px-3 py-1 bg-gradient-to-r from-blue-500 to-indigo-600 text-white text-sm font-semibold rounded-full">
                                {Math.round((trick.confidence || 0) * 100)}%
                              </div>
                            </div>
                          </div>
                          <div className="flex space-x-3 ml-4">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleReview(trick.id, true);
                              }}
                              className="p-2 text-emerald-600 hover:bg-emerald-50 rounded-xl border border-emerald-200/60 hover:border-emerald-300 transition-all duration-200 hover:shadow-md"
                              title="Approve"
                            >
                              <CheckIcon className="h-5 w-5" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleReview(trick.id, false);
                              }}
                              className="p-2 text-red-600 hover:bg-red-50 rounded-xl border border-red-200/60 hover:border-red-300 transition-all duration-200 hover:shadow-md"
                              title="Reject"
                            >
                              <XMarkIcon className="h-5 w-5" />
                            </button>
                          </div>
                        </div>
                        
                        {/* Book Information */}
                        {(trick.book_title || trick.book_author) && (
                          <div className="bg-white/60 backdrop-blur-sm rounded-xl p-3 border border-white/40">
                            <div className="flex items-center space-x-3">
                              <BookOpenIcon className="h-5 w-5 text-blue-600 flex-shrink-0" />
                              <div className="min-w-0 flex-1">
                                {trick.book_title && (
                                  <p className="font-semibold text-slate-700 truncate">{trick.book_title}</p>
                                )}
                                {trick.book_author && (
                                  <p className="text-sm text-slate-500 font-medium">by {trick.book_author}</p>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                        
                        {/* Source and Page Info */}
                        <div className="text-sm text-slate-500 flex justify-between items-center bg-slate-50/60 rounded-lg px-3 py-2">
                          {trick.source_document && (
                            <span className="truncate font-medium">{trick.source_document}</span>
                          )}
                          {(trick.page_start || trick.page_number) && (
                            <span className="flex-shrink-0 ml-2 bg-white/80 px-2 py-1 rounded-md font-semibold">
                              Page {trick.page_start || trick.page_number}
                              {trick.page_end && trick.page_start !== trick.page_end && `-${trick.page_end}`}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination for Review List */}
                {pendingTricks.length > itemsPerPage && (
                  <Pagination
                    currentPage={currentPage}
                    totalItems={pendingTricks.length}
                    itemsPerPage={itemsPerPage}
                    onPageChange={handlePageChange}
                  />
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* Trick Detail Modal */}
      <TrickDetailModal
        trick={selectedTrick}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        showReviewActions={true}
        onReview={(approved: boolean) => selectedTrick && handleReview(selectedTrick.id, approved)}
      />
    </div>
  );
}
