
/**
 * Simplified Training Page
 * Focus on easy retraining with minimal configuration
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PlayIcon, Cog6ToothIcon, CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { trainingApi } from '../lib/api';
import TrainingProgress from '../components/TrainingProgress';
import LoadingSpinner from '../components/ui/LoadingSpinner';

interface TrainingStats {
  total_tricks: number;
  reviewed_tricks: number;
  accuracy_rate?: number;
  last_training?: string;
  model_version?: string;
}

interface TrainingJob {
  id: string;
  status: 'running' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  created_at: string;
  completed_at?: string;
}

export default function TrainingPage() {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [epochs, setEpochs] = useState(10);
  const [learningRate, setLearningRate] = useState(0.001);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  
  const queryClient = useQueryClient();

  // Fetch training stats
  const { data: stats, isLoading: statsLoading } = useQuery<TrainingStats>({
    queryKey: ['training-stats'],
    queryFn: async () => {
      return await trainingApi.getTrainingStats();
    }
  });

  // Fetch current training jobs
  const { data: currentJob } = useQuery<TrainingJob | null>({
    queryKey: ['current-training-job', currentJobId],
    queryFn: async () => {
      if (currentJobId) {
        return await trainingApi.getTrainingJobStatus(currentJobId);
      }
      return null;
    },
    refetchInterval: currentJobId ? 2000 : false, // Poll every 2 seconds if we have a job
  });

  // Simple retraining mutation
  const retrainMutation = useMutation({
    mutationFn: async (params: { epochs?: number; learning_rate?: number }) => {
      console.log('Starting retraining with params:', params);
      return await trainingApi.startSimpleRetraining(params);
    },
    onSuccess: (data) => {
      setCurrentJobId(data.job_id);
      queryClient.invalidateQueries({ queryKey: ['current-training-job'] });
      queryClient.invalidateQueries({ queryKey: ['training-stats'] });
    }
  });

  const handleSimpleRetrain = () => {
    const params = showAdvanced ? { epochs, learning_rate: learningRate } : {};
    retrainMutation.mutate(params);
  };

  const isTraining = currentJob?.status === 'running' || retrainMutation.isPending;

  return (
    <div className="h-full bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-pink-700 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-500/25">
              <PlayIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-purple-800 bg-clip-text text-transparent">
                AI Model Training
              </h1>
              <p className="text-slate-600 font-medium">
                Retrain your magic trick detection model with latest data
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Training Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Training Stats */}
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 shadow-lg border border-white/20">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">Training Overview</h2>
            
            {statsLoading ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{stats?.total_tricks}</div>
                  <div className="text-sm text-slate-600 font-medium">Total Tricks</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-emerald-600">{stats?.reviewed_tricks}</div>
                  <div className="text-sm text-slate-600 font-medium">Quality Data</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {stats?.accuracy_rate ? Math.round(stats.accuracy_rate * 100) : 0}%
                  </div>
                  <div className="text-sm text-slate-600 font-medium">Accuracy</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-amber-600">{stats?.model_version || 'v1.0'}</div>
                  <div className="text-sm text-slate-600 font-medium">Model Version</div>
                </div>
              </div>
            )}

            {stats?.last_training && (
              <div className="mt-6 p-4 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center space-x-2">
                  <CheckCircleIcon className="h-5 w-5 text-emerald-600" />
                  <span className="text-sm font-medium text-slate-700">
                    Last trained: {new Date(stats.last_training).toLocaleString()}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Simple Retraining Interface */}
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 shadow-lg border border-white/20">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-slate-800">Model Retraining</h2>
                <p className="text-slate-600 mt-1">Improve detection accuracy with latest trick data</p>
              </div>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center space-x-2 px-3 py-2 text-sm text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <Cog6ToothIcon className="h-4 w-4" />
                <span>{showAdvanced ? 'Hide' : 'Show'} Advanced</span>
              </button>
            </div>

            {/* Advanced Options */}
            {showAdvanced && (
              <div className="mb-6 p-4 bg-slate-50/80 rounded-xl border border-slate-200/60">
                <h3 className="text-lg font-medium text-slate-800 mb-4">Advanced Settings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Training Epochs
                    </label>
                    <input
                      type="number"
                      value={epochs}
                      onChange={(e) => setEpochs(parseInt(e.target.value))}
                      min={1}
                      max={100}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                    <p className="text-xs text-slate-500 mt-1">Recommended: 10-20 epochs</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Learning Rate
                    </label>
                    <input
                      type="number"
                      value={learningRate}
                      onChange={(e) => setLearningRate(parseFloat(e.target.value))}
                      min={0.0001}
                      max={0.1}
                      step={0.0001}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                    <p className="text-xs text-slate-500 mt-1">Recommended: 0.001</p>
                  </div>
                </div>
              </div>
            )}

            {/* Training Button */}
            <div className="text-center">
              <button
                onClick={handleSimpleRetrain}
                disabled={isTraining}
                className={`
                  inline-flex items-center px-8 py-4 rounded-2xl font-semibold text-lg transition-all duration-300 shadow-lg
                  ${isTraining 
                    ? 'bg-slate-300 text-slate-500 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 hover:shadow-xl hover:-translate-y-1 shadow-purple-500/25'
                  }
                `}
              >
                {isTraining ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                    Training in Progress...
                  </>
                ) : (
                  <>
                    <PlayIcon className="h-6 w-6 mr-3" />
                    Start Retraining
                  </>
                )}
              </button>
              
              {!isTraining && (
                <p className="text-sm text-slate-600 mt-3">
                  Typical training time: 5-15 minutes depending on data size
                </p>
              )}
            </div>

            {/* Warning for insufficient data */}
            {stats && stats.reviewed_tricks < 50 && (
              <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-yellow-800">Limited Training Data</h4>
                    <p className="text-sm text-yellow-700 mt-1">
                      You have only {stats.reviewed_tricks} quality data points. Consider reviewing more tricks for better model accuracy.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Training Progress Sidebar */}
        <div className="space-y-6">
          {/* Current Training Status */}
          {(currentJob && currentJobId) && (
            <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 shadow-lg border border-white/20">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Training Progress</h3>
              <TrainingProgress 
                datasetId="default"
                jobId={currentJobId}
              />
            </div>
          )}

          {/* Quick Tips */}
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 shadow-lg border border-white/20">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Training Tips</h3>
            <div className="space-y-3 text-sm text-slate-600">
              <div className="flex items-start space-x-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                <p>More quality data leads to better accuracy</p>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                <p>Training typically takes 5-15 minutes</p>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                <p>You can continue using the app during training</p>
              </div>
              <div className="flex items-start space-x-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                <p>Model updates automatically after training</p>
              </div>
            </div>
          </div>

          {/* Recent Training History */}
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl p-6 shadow-lg border border-white/20">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Recent Sessions</h3>
            <div className="space-y-3">
              {stats?.last_training ? (
                <div className="flex items-center space-x-3 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                  <CheckCircleIcon className="h-5 w-5 text-emerald-600" />
                  <div>
                    <p className="text-sm font-medium text-emerald-800">Training Completed</p>
                    <p className="text-xs text-emerald-600">
                      {new Date(stats.last_training).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-4 text-slate-500">
                  <p className="text-sm">No training history yet</p>
                  <p className="text-xs mt-1">Start your first training session above</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}