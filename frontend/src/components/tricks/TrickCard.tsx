import React from 'react';
import { Link } from 'react-router-dom';
import { 
  CheckCircleIcon, 
  XCircleIcon,
  EyeIcon,
  BookOpenIcon,
  TagIcon,
  AdjustmentsVerticalIcon
} from '@heroicons/react/24/outline';
import type { Trick } from '@/types';
import { format } from 'date-fns';

interface TrickCardProps {
  trick: Trick;
  showReviewActions?: boolean;
  onMarkCorrect?: (id: string) => void;
  onMarkIncorrect?: (id: string) => void;
  onViewDetails?: (id: string) => void;
}

function getConfidenceColor(confidence?: number): string {
  if (!confidence) return 'gray';
  if (confidence > 0.8) return 'green';
  if (confidence > 0.6) return 'yellow';
  return 'red';
}

function getConfidenceLabel(confidence?: number): string {
  if (!confidence) return 'Unknown';
  if (confidence > 0.8) return 'High';
  if (confidence > 0.6) return 'Medium';
  return 'Low';
}

export default function TrickCard({ 
  trick, 
  showReviewActions = false,
  onMarkCorrect,
  onMarkIncorrect,
  onViewDetails,
}: TrickCardProps) {
  const confidenceColor = getConfidenceColor(trick.confidence);
  const confidenceLabel = getConfidenceLabel(trick.confidence);

  const handleMarkCorrect = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onMarkCorrect?.(trick.id);
  };

  const handleMarkIncorrect = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onMarkIncorrect?.(trick.id);
  };

  const handleViewDetails = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onViewDetails?.(trick.id);
  };

  return (
    <div className="card hover:shadow-lg transition-all duration-200 group">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <Link 
            to={`/tricks/${trick.id}`}
            className="text-lg font-semibold text-gray-900 hover:text-magic-600 transition-colors line-clamp-2"
          >
            {trick.name}
          </Link>
          {trick.confidence && (
            <div className="mt-2">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium confidence-${confidenceColor}`}>
                {confidenceLabel} ({(trick.confidence * 100).toFixed(0)}%)
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="space-y-3 mb-4">
        {/* Description */}
        <p className="text-gray-600 text-sm line-clamp-3">
          {trick.description}
        </p>

        {/* Metadata */}
        <div className="flex flex-wrap gap-2 text-xs">
          <div className="flex items-center text-gray-500">
            <TagIcon className="w-3 h-3 mr-1" />
            <span className="capitalize">{trick.effect_type.replace('_', ' ')}</span>
          </div>
          <div className="flex items-center text-gray-500">
            <AdjustmentsVerticalIcon className="w-3 h-3 mr-1" />
            <span className="capitalize">{trick.difficulty}</span>
          </div>
          {trick.page_start && (
            <div className="flex items-center text-gray-500">
              <BookOpenIcon className="w-3 h-3 mr-1" />
              <span>
                {trick.page_start}
                {trick.page_end && trick.page_end !== trick.page_start && `-${trick.page_end}`}
              </span>
            </div>
          )}
        </div>

        {/* Book Info */}
        {(trick.book_title || trick.book_author) && (
          <div className="pt-2 border-t border-gray-100">
            <p className="text-xs text-gray-500">
              {trick.book_title && <span className="font-medium">{trick.book_title}</span>}
              {trick.book_author && (
                <span>
                  {trick.book_title && ' by '}
                  {trick.book_author}
                </span>
              )}
            </p>
          </div>
        )}

        {/* Props */}
        {trick.props && trick.props.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {trick.props.slice(0, 3).map((prop, index) => (
              <span 
                key={index}
                className="inline-block bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs"
              >
                {prop}
              </span>
            ))}
            {trick.props.length > 3 && (
              <span className="inline-block bg-gray-100 text-gray-500 px-2 py-1 rounded text-xs">
                +{trick.props.length - 3} more
              </span>
            )}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <span className="text-xs text-gray-500">
          {format(new Date(trick.created_at), 'MMM dd, yyyy')}
        </span>

        <div className="flex items-center space-x-2">
          {showReviewActions && (
            <>
              <button
                onClick={handleMarkCorrect}
                className="p-1.5 text-green-600 hover:bg-green-50 rounded-md transition-colors"
                title="Mark as correct"
              >
                <CheckCircleIcon className="w-4 h-4" />
              </button>
              <button
                onClick={handleMarkIncorrect}
                className="p-1.5 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                title="Mark as incorrect"
              >
                <XCircleIcon className="w-4 h-4" />
              </button>
            </>
          )}
          <button
            onClick={handleViewDetails}
            className="p-1.5 text-gray-600 hover:bg-gray-50 rounded-md transition-colors group-hover:text-magic-600"
            title="View details"
          >
            <EyeIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
