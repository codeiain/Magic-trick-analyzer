import { CheckIcon, XMarkIcon, BookOpenIcon } from '@heroicons/react/24/outline';
import type { Trick } from '../types';

interface TrickCardProps {
  trick: Trick;
  onReview?: (approved: boolean) => void;
  showBookInfo?: boolean;
  onClick?: (trick: Trick) => void;
}

export default function TrickCard({ trick, onReview, showBookInfo = true, onClick }: TrickCardProps) {
  const handleCardClick = () => {
    if (onClick) {
      onClick(trick);
    }
  };

  const handleReviewClick = (e: React.MouseEvent, approved: boolean) => {
    e.stopPropagation(); // Prevent card click when clicking review buttons
    if (onReview) {
      onReview(approved);
    }
  };

  return (
    <div 
      className={`group bg-white/90 backdrop-blur-sm border border-slate-200/80 rounded-2xl p-5 transition-all duration-300 ${
        onClick ? 'cursor-pointer hover:border-blue-300/80 hover:shadow-lg hover:shadow-blue-100/50 hover:-translate-y-1' : 'hover:border-slate-300/80 hover:shadow-md'
      }`}
      onClick={handleCardClick}
    >
      <div className="space-y-4">
        <div>
          <h3 className="font-semibold text-slate-900 text-lg leading-tight group-hover:text-blue-900 transition-colors">
            {trick.name}
          </h3>
          {trick.description && (
            <p className="text-slate-600 mt-2 text-sm leading-relaxed line-clamp-2">
              {trick.description}
            </p>
          )}
        </div>

        {/* Book Information */}
        {showBookInfo && (trick.book_title || trick.book_author) && (
          <div className="flex items-center space-x-3 text-sm bg-gradient-to-r from-slate-50 to-blue-50 px-4 py-3 rounded-xl border border-slate-100">
            <BookOpenIcon className="h-4 w-4 text-blue-500 flex-shrink-0" />
            <div className="min-w-0 flex-1">
              {trick.book_title && (
                <p className="font-medium text-slate-800 truncate text-sm">{trick.book_title}</p>
              )}
              {trick.book_author && (
                <p className="text-xs text-slate-500 mt-0.5">by {trick.book_author}</p>
              )}
            </div>
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="bg-gradient-to-r from-purple-100 to-blue-100 text-purple-800 px-3 py-1 rounded-full text-xs font-semibold">
              {trick.effect_type?.replace('_', ' ') || 'Unknown'}
            </span>
            
            {trick.difficulty && (
              <span className="bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full text-xs font-semibold">
                {trick.difficulty}
              </span>
            )}
          </div>
          
          {trick.confidence !== undefined && (
            <div className="text-right">
              <div className="text-sm font-semibold text-slate-700">
                {Math.round(trick.confidence * 100)}%
              </div>
              <div className="text-xs text-slate-500">confidence</div>
            </div>
          )}
        </div>

        {(trick.page_start || trick.page_end) && (
          <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
            <span>
              Page{trick.page_start && trick.page_end && trick.page_start !== trick.page_end ? 's' : ''}: {' '}
              {trick.page_start}{trick.page_end && trick.page_start !== trick.page_end ? `-${trick.page_end}` : ''}
            </span>
            <span className="text-slate-400">
              {new Date(trick.created_at).toLocaleDateString()}
            </span>
          </div>
        )}

        {onReview && trick.status === 'pending' && (
          <div className="flex space-x-2 pt-2 border-t border-gray-100">
            <button
              onClick={(e) => handleReviewClick(e, true)}
              className="flex-1 flex items-center justify-center px-3 py-1.5 text-green-700 bg-green-50 hover:bg-green-100 rounded text-sm font-medium"
            >
              <CheckIcon className="h-4 w-4 mr-1" style={{ maxWidth: '1rem', maxHeight: '1rem' }} />
              Approve
            </button>
            <button
              onClick={(e) => handleReviewClick(e, false)}
              className="flex-1 flex items-center justify-center px-3 py-1.5 text-red-700 bg-red-50 hover:bg-red-100 rounded text-sm font-medium"
            >
              <XMarkIcon className="h-4 w-4 mr-1" style={{ maxWidth: '1rem', maxHeight: '1rem' }} />
              Reject
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
