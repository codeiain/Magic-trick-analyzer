import { useQuery } from '@tanstack/react-query';
import { getDashboardStats, getActiveOCRJobs, jobManagementApi } from '../lib/api';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import StatsCard from '../components/ui/StatsCard';
import { Link } from 'react-router-dom';
import { useState } from 'react';
import type { ActiveOCRJob } from '../types';

interface DashboardStats {
  total_tricks: number;
  pending_review: number;
  books_processed: number;
  accuracy: number;
}

interface RecentBook {
  id: string;
  title: string;
  author?: string;
  processed_at: string;
  status: 'processed' | 'processing' | 'error';
  trick_count?: number;
}

export default function Dashboard() {
  const [cancellingJob, setCancellingJob] = useState<string | null>(null);
  const [clearingJobs, setClearingJobs] = useState(false);

  const { data: stats, isLoading, error } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
  });

  // Query for active OCR jobs
  const { data: activeOCRJobs, isLoading: ocrJobsLoading, refetch: refetchOCRJobs } = useQuery({
    queryKey: ['active-ocr-jobs'],
    queryFn: getActiveOCRJobs,
    refetchInterval: 3000, // Poll every 3 seconds
  });

  // Job management functions
  const handleCancelJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to cancel this job?')) {
      return;
    }
    
    try {
      setCancellingJob(jobId);
      await jobManagementApi.cancelJob(jobId);
      refetchOCRJobs(); // Refresh the job list
    } catch (error) {
      console.error('Failed to cancel job:', error);
      alert('Failed to cancel job. Please try again.');
    } finally {
      setCancellingJob(null);
    }
  };

  const handleRemoveJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to remove this job completely? This action cannot be undone.')) {
      return;
    }
    
    try {
      setCancellingJob(jobId);
      await jobManagementApi.removeJob(jobId);
      refetchOCRJobs(); // Refresh the job list
    } catch (error) {
      console.error('Failed to remove job:', error);
      alert('Failed to remove job. Please try again.');
    } finally {
      setCancellingJob(null);
    }
  };

  const handleClearCompletedJobs = async () => {
    if (!confirm('Clear all completed jobs from the system?')) {
      return;
    }
    
    try {
      setClearingJobs(true);
      await jobManagementApi.clearCompletedJobs(24); // Clear jobs older than 24 hours
      refetchOCRJobs(); // Refresh the job list
    } catch (error) {
      console.error('Failed to clear completed jobs:', error);
      alert('Failed to clear completed jobs. Please try again.');
    } finally {
      setClearingJobs(false);
    }
  };

  const handleClearAllJobs = async () => {
    if (!confirm('Clear ALL jobs (including queued ones) from the system? This action cannot be undone.')) {
      return;
    }
    
    try {
      setClearingJobs(true);
      // Clear multiple status types
      await Promise.all([
        jobManagementApi.clearJobsByStatus('completed'),
        jobManagementApi.clearJobsByStatus('failed'),
        jobManagementApi.clearJobsByStatus('cancelled'),
        jobManagementApi.clearJobsByStatus('finished')
      ]);
      refetchOCRJobs(); // Refresh the job list
    } catch (error) {
      console.error('Failed to clear all jobs:', error);
      alert('Failed to clear all jobs. Please try again.');
    } finally {
      setClearingJobs(false);
    }
  };

  // Query for recent books activity
  const { data: recentBooks, isLoading: booksLoading } = useQuery<RecentBook[]>({
    queryKey: ['recent-books'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/v1/books/recent?limit=10');
        if (!response.ok) {
          throw new Error('Failed to fetch recent books');
        }
        return response.json();
      } catch (error) {
        console.error('Failed to fetch recent books:', error);
        // Return empty array if API is not available instead of mock data
        return [];
      }
    },
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div>Error loading dashboard</div>;

  return (
    <div className="h-full bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      {/* Modern Header */}
      <div className="mb-8">
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20">
          <div className="flex items-center space-x-4 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
              <span className="text-2xl">🎭</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-blue-800 bg-clip-text text-transparent">
                Dashboard
              </h1>
              <p className="text-slate-600 font-medium">Welcome to your magic trick analysis hub</p>
            </div>
          </div>
        </div>
      </div>

      {/* Modern Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          title="Total Tricks"
          value={stats?.total_tricks || 0}
          icon="🎭"
        />
        <StatsCard
          title="Pending Review"
          value={stats?.pending_review || 0}
          icon="⏳"
        />
        <StatsCard
          title="Books Processed"
          value={stats?.books_processed || 0}
          icon="📚"
        />
        <StatsCard
          title="Accuracy"
          value={`${Math.round((stats?.accuracy || 0) * 100)}%`}
          icon="🎯"
        />
      </div>

      {/* Active OCR Jobs Section */}
      {activeOCRJobs && activeOCRJobs.count > 0 && (
        <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl flex items-center justify-center shadow-lg shadow-orange-500/25">
                <span className="text-lg">📄</span>
              </div>
              <div>
                <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-orange-800 bg-clip-text text-transparent">
                  Active OCR Processing
                </h2>
                <p className="text-slate-600 font-medium">
                  {activeOCRJobs.count} book{activeOCRJobs.count !== 1 ? 's' : ''} with detailed progress tracking
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button 
                onClick={handleClearCompletedJobs}
                disabled={clearingJobs}
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-700 bg-slate-50 hover:bg-slate-100 rounded-lg transition-colors disabled:opacity-50"
              >
                {clearingJobs ? '⏳ Clearing...' : '🗑️ Clear Completed'}
              </button>
              <button 
                onClick={handleClearAllJobs}
                disabled={clearingJobs}
                className="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-colors disabled:opacity-50"
              >
                {clearingJobs ? '⏳ Clearing...' : '🗑️ Clear All'}
              </button>
              <Link 
                to="/books" 
                className="px-4 py-2 text-sm font-medium text-orange-600 hover:text-orange-700 bg-orange-50 hover:bg-orange-100 rounded-lg transition-colors"
              >
                View All Books
              </Link>
            </div>
          </div>
          
          <div className="space-y-3">
            {ocrJobsLoading ? (
              <div className="text-center py-4">
                <LoadingSpinner />
                <p className="text-slate-500 mt-2">Loading OCR jobs...</p>
              </div>
            ) : (
              activeOCRJobs.active_ocr_jobs.map((job: ActiveOCRJob) => (
                <div
                  key={job.job_id}
                  className="bg-gradient-to-r from-orange-50 to-yellow-50/50 rounded-xl p-5 border border-orange-200/50 shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="font-semibold text-slate-800">
                          {job.book_title}
                        </h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          job.status === 'started' 
                            ? 'bg-yellow-100 text-yellow-700' 
                            : 'bg-blue-100 text-blue-700'
                        }`}>
                          {job.status === 'started' ? '⚡ Processing' : '⏳ Queued'}
                        </span>
                      </div>
                      
                      {/* Enhanced progress message */}
                      <p className="text-sm text-slate-600 mb-3 font-medium">{job.message}</p>
                      
                      {/* Detailed progress information */}
                      {job.progress !== undefined && job.progress !== null && (
                        <div className="space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-500">Progress</span>
                            <span className="font-medium text-slate-700">{job.progress}% complete</span>
                          </div>
                          <div className="w-full bg-gradient-to-r from-orange-200 to-yellow-200 rounded-full h-3 overflow-hidden">
                            <div 
                              className={`h-full rounded-full transition-all duration-500 ease-out ${
                                job.progress < 30 
                                  ? 'bg-gradient-to-r from-blue-500 to-blue-600' 
                                  : job.progress < 80
                                  ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                                  : 'bg-gradient-to-r from-orange-500 to-green-500'
                              }`}
                              style={{ width: `${Math.max(job.progress || 0, 2)}%` }}
                            >
                              <div className="h-full bg-white/20 rounded-full animate-pulse"></div>
                            </div>
                          </div>
                          
                          {/* Progress stage indicators */}
                          <div className="flex items-center justify-between text-xs text-slate-500 mt-2">
                            <div className="flex items-center space-x-4">
                              <div className={`flex items-center space-x-1 ${
                                (job.progress || 0) >= 10 ? 'text-green-600' : 'text-slate-400'
                              }`}>
                                <div className={`w-2 h-2 rounded-full ${
                                  (job.progress || 0) >= 10 ? 'bg-green-500' : 'bg-slate-300'
                                }`}></div>
                                <span>Init</span>
                              </div>
                              <div className={`flex items-center space-x-1 ${
                                (job.progress || 0) >= 30 ? 'text-green-600' : (job.progress || 0) >= 10 ? 'text-yellow-600' : 'text-slate-400'
                              }`}>
                                <div className={`w-2 h-2 rounded-full ${
                                  (job.progress || 0) >= 30 ? 'bg-green-500' : (job.progress || 0) >= 10 ? 'bg-yellow-500' : 'bg-slate-300'
                                }`}></div>
                                <span>Extract</span>
                              </div>
                              <div className={`flex items-center space-x-1 ${
                                (job.progress || 0) >= 80 ? 'text-green-600' : (job.progress || 0) >= 30 ? 'text-yellow-600' : 'text-slate-400'
                              }`}>
                                <div className={`w-2 h-2 rounded-full ${
                                  (job.progress || 0) >= 80 ? 'bg-green-500' : (job.progress || 0) >= 30 ? 'bg-yellow-500' : 'bg-slate-300'
                                }`}></div>
                                <span>OCR</span>
                              </div>
                              <div className={`flex items-center space-x-1 ${
                                (job.progress || 0) >= 95 ? 'text-green-600' : (job.progress || 0) >= 80 ? 'text-yellow-600' : 'text-slate-400'
                              }`}>
                                <div className={`w-2 h-2 rounded-full ${
                                  (job.progress || 0) >= 95 ? 'bg-green-500' : (job.progress || 0) >= 80 ? 'bg-yellow-500' : 'bg-slate-300'
                                }`}></div>
                                <span>Save</span>
                              </div>
                            </div>
                            <span className="font-medium">
                              {new Date(job.created_at).toLocaleTimeString()}
                            </span>
                          </div>
                        </div>
                      )}
                      
                      {/* Fallback for jobs without progress */}
                      {(job.progress === undefined || job.progress === null) && (
                        <div className="flex items-center space-x-2 mt-2">
                          <div className="text-right">
                            <p className="text-xs text-slate-500">
                              Started: {new Date(job.created_at).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {/* Action buttons and status indicator */}
                    <div className="flex items-start space-x-2 ml-4">
                      <div className="flex items-center justify-center w-8 h-8 bg-white/80 rounded-lg shadow-sm">
                        {job.status === 'started' ? (
                          <div className="w-4 h-4 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full animate-pulse shadow-sm"></div>
                        ) : (
                          <div className="w-4 h-4 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full"></div>
                        )}
                      </div>
                      <div className="flex flex-col space-y-1">
                        <button
                          onClick={() => handleCancelJob(job.job_id)}
                          disabled={cancellingJob === job.job_id}
                          className="px-2 py-1 text-xs font-medium text-orange-600 hover:text-orange-700 bg-orange-100 hover:bg-orange-200 rounded transition-colors disabled:opacity-50 shadow-sm"
                          title="Cancel Job"
                        >
                          {cancellingJob === job.job_id ? '⏳' : '⏸️'}
                        </button>
                        <button
                          onClick={() => handleRemoveJob(job.job_id)}
                          disabled={cancellingJob === job.job_id}
                          className="px-2 py-1 text-xs font-medium text-red-600 hover:text-red-700 bg-red-100 hover:bg-red-200 rounded transition-colors disabled:opacity-50 shadow-sm"
                          title="Remove Job"
                        >
                          {cancellingJob === job.job_id ? '⏳' : '🗑️'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Modern Activity Section */}
      <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-500/25">
              <span className="text-lg">�</span>
            </div>
            <div>
              <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-purple-800 bg-clip-text text-transparent">
                Recent Activity
              </h2>
              <p className="text-slate-600 font-medium">Last 10 processed books</p>
            </div>
          </div>
          <Link 
            to="/books" 
            className="px-4 py-2 text-sm font-medium text-purple-600 hover:text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors"
          >
            View All
          </Link>
        </div>
        
        <div className="space-y-3">
          {booksLoading ? (
            <div className="text-center py-8">
              <LoadingSpinner />
              <p className="text-slate-500 mt-2">Loading recent activity...</p>
            </div>
          ) : recentBooks && recentBooks.length > 0 ? (
            recentBooks.map((book) => (
              <Link
                key={book.id}
                to={`/books/${book.id}`}
                className="block bg-gradient-to-r from-slate-50 to-blue-50/50 hover:from-blue-50 hover:to-purple-50 rounded-xl p-4 border border-slate-200/50 hover:border-blue-200 transition-all duration-200 group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-slate-800 group-hover:text-blue-800 transition-colors">
                      {book.title}
                    </h3>
                    {book.author && (
                      <p className="text-sm text-slate-600 mt-1">by {book.author}</p>
                    )}
                    <div className="flex items-center space-x-4 mt-2">
                      <span className={`px-2 py-1 rounded-md text-xs font-medium ${
                        book.status === 'processed' 
                          ? 'bg-emerald-100 text-emerald-700' 
                          : book.status === 'processing'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {book.status === 'processed' ? '✓ Processed' : 
                         book.status === 'processing' ? '⏳ Processing' : '❌ Error'}
                      </span>
                      {book.trick_count && (
                        <span className="text-xs text-slate-500">
                          {book.trick_count} tricks found
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500">
                      {new Date(book.processed_at).toLocaleDateString()}
                    </p>
                    <div className="w-6 h-6 bg-white/80 rounded-lg flex items-center justify-center mt-2 group-hover:bg-blue-100 transition-colors">
                      <span className="text-sm">→</span>
                    </div>
                  </div>
                </div>
              </Link>
            ))
          ) : (
            <div className="text-center py-8 bg-gradient-to-br from-slate-50 to-blue-50/50 rounded-2xl border border-slate-200/50">
              <div className="w-16 h-16 bg-white/80 backdrop-blur-sm rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
                <span className="text-2xl">�</span>
              </div>
              <p className="font-medium text-slate-600">No books processed yet</p>
              <p className="text-sm text-slate-500 mt-1">Upload your first magic book to get started</p>
              <Link 
                to="/books"
                className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Upload Book
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}