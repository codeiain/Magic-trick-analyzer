/**
 * Custom hook for polling job status
 */
import { useEffect, useState } from 'react';
import { jobsApi } from '../lib/api';

interface JobStatus {
  job_id: string;
  status: 'queued' | 'started' | 'finished' | 'failed';
  progress?: number;
  message?: string;
  result?: any;
  error?: string;
  created_at: string;
  started_at?: string;
  finished_at?: string;
}

interface UseJobStatusOptions {
  pollInterval?: number; // milliseconds
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
}

export function useJobStatus(jobId: string | null, options: UseJobStatusOptions = {}) {
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { pollInterval = 2000, onComplete, onError } = options;

  useEffect(() => {
    if (!jobId) {
      setJobStatus(null);
      setIsLoading(false);
      return;
    }

    let intervalId: number;
    let isMounted = true;

    const pollJobStatus = async () => {
      try {
        setError(null);
        const status = await jobsApi.getStatus(jobId);
        
        if (!isMounted) return;
        
        setJobStatus(status);
        
        // Check if job is complete
        if (status.status === 'finished') {
          setIsLoading(false);
          if (onComplete && status.result) {
            onComplete(status.result);
          }
          clearInterval(intervalId);
        } else if (status.status === 'failed') {
          setIsLoading(false);
          const errorMsg = status.error || 'Job failed';
          if (onError) {
            onError(errorMsg);
          }
          clearInterval(intervalId);
        } else if (status.status === 'started') {
          setIsLoading(true);
        }
      } catch (err) {
        if (!isMounted) return;
        
        const errorMsg = err instanceof Error ? err.message : 'Failed to fetch job status';
        setError(errorMsg);
        setIsLoading(false);
        clearInterval(intervalId);
      }
    };

    // Initial poll
    setIsLoading(true);
    pollJobStatus();

    // Set up polling interval
    intervalId = setInterval(pollJobStatus, pollInterval);

    // Cleanup
    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, [jobId, pollInterval, onComplete, onError]);

  const cancelJob = async () => {
    if (!jobId) return;
    
    try {
      await jobsApi.cancel(jobId);
      setJobStatus(prev => prev ? { ...prev, status: 'failed', error: 'Cancelled by user' } : null);
      setIsLoading(false);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to cancel job';
      setError(errorMsg);
    }
  };

  return {
    jobStatus,
    isLoading,
    error,
    cancelJob,
    isComplete: jobStatus?.status === 'finished',
    isFailed: jobStatus?.status === 'failed',
    isQueued: jobStatus?.status === 'queued',
    isStarted: jobStatus?.status === 'started'
  };
}