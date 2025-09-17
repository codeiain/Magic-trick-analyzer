import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { BookOpenIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { booksApi } from '../lib/api';
import { useJobStatus } from '../hooks/useJobStatus';
import type { Book } from '../types';

export default function BooksPage() {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string>('');
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Job status polling
  const { jobStatus, isLoading: isJobRunning, error: jobError, cancelJob, isComplete } = useJobStatus(
    currentJobId,
    {
      onComplete: (result) => {
        setUploadProgress('Processing completed successfully!');
        queryClient.invalidateQueries({ queryKey: ['books'] });
        setTimeout(() => {
          setCurrentJobId(null);
          setIsUploading(false);
          setUploadProgress('');
        }, 2000);
      },
      onError: (error) => {
        setUploadProgress(`Processing failed: ${error}`);
        setTimeout(() => {
          setCurrentJobId(null);
          setIsUploading(false);
          setUploadProgress('');
        }, 3000);
      }
    }
  );

  // Fetch books from API
  const { data: books = [], isLoading, error } = useQuery({
    queryKey: ['books'],
    queryFn: booksApi.getAll
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: booksApi.upload,
    onMutate: () => {
      setIsUploading(true);
      setUploadProgress('Uploading file...');
    },
    onSuccess: (response) => {
      // Check if response includes job_id (new async system)
      if (response.job_id) {
        setCurrentJobId(response.job_id);
        setUploadProgress('Upload successful! Processing started...');
      } else {
        // Fallback for old system
        setUploadProgress('Upload successful! Processing book...');
        queryClient.invalidateQueries({ queryKey: ['books'] });
        setTimeout(() => {
          setIsUploading(false);
          setUploadProgress('');
        }, 2000);
      }
      
      // Clear the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    },
    onError: (error) => {
      console.error('Upload failed:', error);
      setUploadProgress('Upload failed. Please try again.');
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress('');
      }, 3000);
    }
  });

  // Reprocess mutation
  const reprocessMutation = useMutation({
    mutationFn: booksApi.reprocess,
    onMutate: (bookId) => {
      console.log('Starting reprocess for book:', bookId);
    },
    onSuccess: (_data, bookId) => {
      console.log('Reprocess completed for book:', bookId);
      // Refresh the books list
      queryClient.invalidateQueries({ queryKey: ['books'] });
    },
    onError: (error, bookId) => {
      console.error('Reprocess failed for book:', bookId, error);
      alert('Reprocess failed. Please try again.');
    }
  });

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please select a PDF file.');
        return;
      }
      uploadMutation.mutate(file);
    }
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleViewDetails = (bookId: string) => {
    // Navigate to book details page (you can implement routing later)
    console.log('View details for book:', bookId);
    // For now, show an alert
    alert(`Book details feature coming soon! Book ID: ${bookId}`);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">Error loading books: {String(error)}</p>
      </div>
    );
  }

  return (
    <div className="h-full bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        accept=".pdf"
        style={{ display: 'none' }}
      />

      {/* Modern Header */}
      <div className="mb-8">
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-amber-600 to-orange-700 rounded-2xl flex items-center justify-center shadow-lg shadow-amber-500/25">
                <BookOpenIcon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-amber-800 bg-clip-text text-transparent">
                  Magic Books
                </h1>
                <p className="text-slate-600 font-medium">
                  Manage your magic book collection and track processing status
                </p>
              </div>
            </div>
            
            <button 
              onClick={triggerFileUpload}
              disabled={isUploading}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-2xl hover:from-blue-700 hover:to-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed font-semibold shadow-lg shadow-blue-500/25 hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
            >
              {isUploading ? 'Uploading...' : 'Upload Book'}
            </button>
          </div>
        </div>
      </div>

      {/* Upload Progress */}
      {uploadProgress && (
        <div className="mb-8">
          <div className="bg-blue-50/80 backdrop-blur-lg border border-blue-200/60 rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {isJobRunning && (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                )}
                <div>
                  <p className="text-blue-800 font-semibold">{uploadProgress}</p>
                  {jobStatus && (
                    <div className="mt-2">
                      <p className="text-sm text-blue-600">
                        Job ID: <code className="bg-blue-100 px-2 py-1 rounded text-xs">{jobStatus.job_id}</code>
                      </p>
                      <p className="text-sm text-blue-600 mt-1">
                        Status: <span className={`font-medium ${
                          jobStatus.status === 'finished' ? 'text-green-600' :
                          jobStatus.status === 'failed' ? 'text-red-600' :
                          jobStatus.status === 'started' ? 'text-yellow-600' :
                          'text-blue-600'
                        }`}>{jobStatus.status}</span>
                      </p>
                      {jobStatus.message && (
                        <p className="text-sm text-gray-600 mt-1">{jobStatus.message}</p>
                      )}
                      {jobStatus.progress && (
                        <div className="mt-2">
                          <div className="w-full bg-blue-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                              style={{ width: `${jobStatus.progress}%` }}
                            ></div>
                          </div>
                          <p className="text-xs text-blue-600 mt-1">{jobStatus.progress}% complete</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
              
              {/* Cancel button for active jobs */}
              {currentJobId && isJobRunning && (
                <button
                  onClick={() => {
                    cancelJob();
                    setCurrentJobId(null);
                    setIsUploading(false);
                    setUploadProgress('');
                  }}
                  className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg text-sm font-medium transition-colors"
                  title="Cancel job"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modern Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white/80 backdrop-blur-lg p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
              <BookOpenIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-semibold text-slate-600">Total Books</p>
              <p className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-blue-800 bg-clip-text text-transparent">{books.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white/80 backdrop-blur-lg p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/25">
              <DocumentIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-semibold text-slate-600">Processed</p>
              <p className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-emerald-800 bg-clip-text text-transparent">
                {books.filter(book => book.processed_at).length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white/80 backdrop-blur-lg p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-orange-600 rounded-2xl flex items-center justify-center shadow-lg shadow-yellow-500/25">
              <div className="w-6 h-6 bg-white/20 rounded-full flex items-center justify-center">
                <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-semibold text-slate-600">Processing</p>
              <p className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-yellow-800 bg-clip-text text-transparent">
                {books.filter(book => !book.processed_at).length}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white/80 backdrop-blur-lg p-6 rounded-2xl shadow-lg border border-white/20 hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-500/25">
              <span className="text-white font-bold text-lg">T</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-semibold text-slate-600">Total Tricks</p>
              <p className="text-2xl font-bold bg-gradient-to-r from-slate-800 to-purple-800 bg-clip-text text-transparent">
                {books.reduce((sum, book) => sum + book.trick_count, 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Modern Books List */}
      <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-xl border border-white/20 overflow-hidden">
        <div className="px-8 py-6 border-b border-white/20 bg-gradient-to-r from-white/60 to-white/40">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25">
              <span className="text-sm text-white">📚</span>
            </div>
            <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-blue-800 bg-clip-text text-transparent">
              Your Books
            </h2>
          </div>
        </div>
        
        <div className="divide-y divide-white/20">
          {books.map((book: Book) => (
            <div key={book.id} className="px-8 py-6 hover:bg-white/40 transition-all duration-300">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-6">
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl flex items-center justify-center shadow-lg shadow-amber-500/25">
                      <BookOpenIcon className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-bold text-slate-800">
                      {book.title}
                    </h3>
                    <p className="text-slate-600 font-medium">by {book.author}</p>
                    <div className="flex items-center space-x-4 mt-2 text-sm">
                      {book.publication_year && (
                        <span className="bg-white/60 backdrop-blur-sm px-3 py-1 rounded-lg border border-white/40 text-slate-600 font-medium">
                          {book.publication_year}
                        </span>
                      )}
                      <span className="bg-blue-50/80 backdrop-blur-sm px-3 py-1 rounded-lg border border-blue-200/60 text-blue-700 font-medium">
                        {book.trick_count} tricks detected
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <span className={`px-4 py-2 text-sm font-semibold rounded-xl border shadow-sm ${
                    book.processed_at 
                      ? 'bg-emerald-50/80 border-emerald-200/60 text-emerald-700'
                      : 'bg-yellow-50/80 border-yellow-200/60 text-yellow-700'
                  }`}>
                    {book.processed_at ? 'Processed' : 'Processing...'}
                  </span>
                  
                  <button 
                    onClick={() => {
                      console.log('Clicking reprocess for book:', book.id);
                      reprocessMutation.mutate(book.id);
                    }}
                    disabled={reprocessMutation.isPending}
                    className="px-4 py-2 text-sm font-semibold text-orange-700 bg-white/60 backdrop-blur-sm border border-orange-200/60 rounded-xl hover:bg-orange-50/80 hover:border-orange-300/60 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 hover:shadow-md hover:-translate-y-0.5"
                    title="Reprocess book with improved AI detection"
                  >
                    {reprocessMutation.isPending ? 'Reprocessing...' : 'Reprocess'}
                  </button>
                  
                  <button 
                    onClick={() => handleViewDetails(book.id)}
                    className="px-4 py-2 text-sm font-semibold text-blue-700 bg-white/60 backdrop-blur-sm border border-blue-200/60 rounded-xl hover:bg-blue-50/80 hover:border-blue-300/60 transition-all duration-300 hover:shadow-md hover:-translate-y-0.5"
                  >
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {books.length === 0 && (
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-12 shadow-xl border border-white/20 text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-slate-100 to-slate-200 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg">
            <BookOpenIcon className="w-8 h-8 text-slate-600" />
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2">No books yet</h3>
          <p className="text-slate-600 font-medium mb-8">
            Get started by uploading your first magic book.
          </p>
          <button 
            onClick={triggerFileUpload}
            disabled={isUploading}
            className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-2xl hover:from-blue-700 hover:to-indigo-800 disabled:opacity-50 font-semibold shadow-lg shadow-blue-500/25 hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
          >
            <BookOpenIcon className="h-5 w-5 mr-2" />
            Upload Book
          </button>
        </div>
      )}
    </div>
  );
}
