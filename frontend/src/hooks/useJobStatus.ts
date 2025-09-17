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
  // Multi-stage job information
  ocr_completed?: boolean;
  ai_queued?: boolean;
  ai_job_id?: string;
  ai_job_status?: {
    job_id: string;
    status: string;
    result?: any;
    error?: string;
  };
  ocr_result?: {
    character_count: number;
    confidence: number;
    database_saved: boolean;
  };
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
        
        // Check if job is complete (either single-stage or multi-stage)
        const isOCRComplete = status.status === 'finished';
        const isAIComplete = status.ai_job_status?.status === 'finished';
        const isMultiStageJob = Boolean(status.ai_job_id);
        
        // For multi-stage jobs, consider complete when both OCR and AI are done
        // For single-stage jobs, complete when OCR is done
        const isJobComplete = isOCRComplete && (!isMultiStageJob || isAIComplete);
        const isJobFailed = status.status === 'failed' || status.ai_job_status?.status === 'failed';
        
        if (isJobComplete) {
          setIsLoading(false);
          if (onComplete && (status.result || status.ai_job_status?.result)) {
            onComplete(status.ai_job_status?.result || status.result);
          }
          clearInterval(intervalId);
        } else if (isJobFailed) {
          setIsLoading(false);
          const errorMsg = status.error || status.ai_job_status?.error || 'Job failed';
          if (onError) {
            onError(errorMsg);
          }
          clearInterval(intervalId);
        } else if (status.status === 'started' || status.ai_job_status?.status === 'started') {
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