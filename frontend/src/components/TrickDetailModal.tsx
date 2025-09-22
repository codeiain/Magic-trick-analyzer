import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, BookOpenIcon } from '@heroicons/react/24/outline';
import type { Trick, TrickDetail } from '../types';

interface TrickDetailModalProps {
  trick: Trick | TrickDetail | null;
  isOpen: boolean;
  onClose: () => void;
  showReviewActions?: boolean;
  onReview?: (approved: boolean) => void;
}

export default function TrickDetailModal({ 
  trick, 
  isOpen, 
  onClose, 
  showReviewActions = false, 
  onReview 
}: TrickDetailModalProps) {
  if (!trick) return null;

  // Helper function to check if trick is detailed
  const isDetailedTrick = (trick: Trick | TrickDetail): trick is TrickDetail => {
    return 'book_sources' in trick && Array.isArray(trick.book_sources);
  };

  const bookSources = isDetailedTrick(trick) ? trick.book_sources : 
    (trick.book_title || trick.book_author) ? [{
      book_id: '',
      book_title: trick.book_title || '',
      book_author: trick.book_author || '',
      page_start: trick.page_start,
      page_end: trick.page_end,
      method: trick.method,
      confidence: trick.confidence
    }] : [];

  const handleReview = (approved: boolean) => {
    if (onReview) {
      onReview(approved);
      onClose();
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                {/* Header */}
                <div className="flex justify-between items-start mb-6">
                  <div className="flex-1">
                    <Dialog.Title
                      as="h3"
                      className="text-xl font-semibold leading-6 text-gray-900 pr-4"
                    >
                      {trick.name}
                    </Dialog.Title>
                    <div className="flex items-center space-x-4 mt-2">
                      {trick.confidence !== undefined && (
                        <span className="text-sm text-gray-600">
                          Confidence: {Math.round(trick.confidence * 100)}%
                        </span>
                      )}
                      {trick.effect_type && (
                        <span className="bg-magic-100 text-magic-800 px-3 py-1 rounded-full text-sm font-medium">
                          {trick.effect_type.replace('_', ' ')}
                        </span>
                      )}
                      {trick.difficulty && (
                        <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                          {trick.difficulty}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    type="button"
                    className="rounded-md p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-magic-500"
                    onClick={onClose}
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>

                {/* Content */}
                <div className="space-y-6">
                  {/* Book Sources */}
                  {bookSources.length > 0 && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex items-start space-x-3">
                        <BookOpenIcon className="h-6 w-6 text-gray-400 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900 mb-1">
                            {bookSources.length === 1 ? 'Source Book' : `Found in ${bookSources.length} Books`}
                          </h4>
                          <div className="space-y-3">
                            {bookSources.map((source, idx) => (
                              <div key={idx} className={idx > 0 ? "pt-3 border-t border-gray-200" : ""}>
                                {source.book_title && (
                                  <p className="text-gray-800 font-medium">{source.book_title}</p>
                                )}
                                {source.book_author && (
                                  <p className="text-gray-600 text-sm">by {source.book_author}</p>
                                )}
                                {(source.page_start || source.page_end) && (
                                  <p className="text-gray-500 text-sm">
                                    Page {source.page_start}
                                    {source.page_end && source.page_start !== source.page_end && ` - ${source.page_end}`}
                                  </p>
                                )}
                                {source.confidence !== undefined && (
                                  <p className="text-gray-500 text-sm">
                                    Detection Confidence: {Math.round(source.confidence * 100)}%
                                  </p>
                                )}
                                {source.method && (
                                  <div className="mt-2">
                                    <h5 className="font-medium text-gray-800 text-sm">Performance Method:</h5>
                                    <p className="text-gray-700 text-sm leading-relaxed mt-1">
                                      {source.method}
                                    </p>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Description */}
                  {trick.description && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Description</h4>
                      <p className="text-gray-700 leading-relaxed">
                        {trick.description}
                      </p>
                    </div>
                  )}

                  {/* Props */}
                  {trick.props && trick.props.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Required Props</h4>
                      <div className="flex flex-wrap gap-2">
                        {trick.props.map((prop, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full font-medium"
                          >
                            {prop}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Keywords */}
                  {trick.keywords && trick.keywords.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Keywords</h4>
                      <div className="flex flex-wrap gap-2">
                        {trick.keywords.map((keyword, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Source Document */}
                  {trick.source_document && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Source Document</h4>
                      <p className="text-gray-600 text-sm font-mono bg-gray-50 p-2 rounded">
                        {trick.source_document}
                      </p>
                    </div>
                  )}

                  {/* Similar Tricks */}
                  {isDetailedTrick(trick) && trick.similar_tricks && trick.similar_tricks.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Similar Tricks</h4>
                      <div className="space-y-2">
                        {trick.similar_tricks.slice(0, 3).map((similarTrick, idx) => (
                          <div key={idx} className="bg-blue-50 p-3 rounded border-l-4 border-blue-200">
                            <p className="font-medium text-blue-900">{similarTrick.name}</p>
                            {similarTrick.book_title && (
                              <p className="text-blue-700 text-sm">from {similarTrick.book_title}</p>
                            )}
                            {similarTrick.effect_type && (
                              <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs mt-1">
                                {similarTrick.effect_type.replace('_', ' ')}
                              </span>
                            )}
                          </div>
                        ))}
                        {trick.similar_tricks.length > 3 && (
                          <p className="text-gray-500 text-sm">
                            ... and {trick.similar_tricks.length - 3} more similar tricks
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Timestamps */}
                  <div className="text-xs text-gray-500 space-y-1 pt-4 border-t border-gray-200">
                    <p>Created: {new Date(trick.created_at).toLocaleString()}</p>
                    {trick.updated_at && (
                      <p>Updated: {new Date(trick.updated_at).toLocaleString()}</p>
                    )}
                  </div>
                </div>

                {/* Review Actions */}
                {showReviewActions && onReview && trick.status === 'pending' && (
                  <div className="flex space-x-3 pt-6 border-t border-gray-200">
                    <button
                      onClick={() => handleReview(true)}
                      className="flex items-center justify-center px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:ring-2 focus:ring-green-500 font-medium"
                    >
                      <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Approve
                    </button>
                    <button
                      onClick={() => handleReview(false)}
                      className="flex items-center justify-center px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:ring-2 focus:ring-red-500 font-medium"
                    >
                      <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      Reject
                    </button>
                  </div>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}