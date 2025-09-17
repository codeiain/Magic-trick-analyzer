import { useQuery, useMutation } from '@tanstack/react-query';
import { PlayIcon, InformationCircleIcon } from '@heroicons/react/24/outline';
import { reviewApi } from '../lib/api';
import LoadingSpinner from '../components/ui/LoadingSpinner';

export default function TrainingPage() {
  // Get training stats
  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['training-stats'],
    queryFn: reviewApi.getStats,
    refetchInterval: 5000 // Refresh every 5 seconds
  });

  // Get training status
  const { data: trainingStatus, refetch: refetchStatus } = useQuery({
    queryKey: ['training-status'],
    queryFn: reviewApi.getTrainingStatus,
    refetchInterval: 2000 // Check status more frequently during training
  });

  // Get model info
  const { data: modelInfo, refetch: refetchModel } = useQuery({
    queryKey: ['model-info'],
    queryFn: reviewApi.getModelInfo,
    refetchInterval: 10000
  });

  // Training mutation
  const trainingMutation = useMutation({
    mutationFn: reviewApi.startTraining,
    onSuccess: () => {
      // Refetch all related data
      refetchStats();
      refetchStatus();
      refetchModel();
    },
    onError: (error) => {
      console.error('Training failed:', error);
    }
  });

  const handleStartTraining = async () => {
    try {
      await trainingMutation.mutateAsync();
    } catch (error) {
      console.error('Failed to start training:', error);
    }
  };

  const isTraining = trainingStatus?.status === 'training';
  const trainingProgress = trainingStatus?.progress || 0;

  return (
    <div className="h-full bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      {/* Modern Header */}
      <div className="mb-8">
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gradient-to-br from-violet-600 to-purple-700 rounded-2xl flex items-center justify-center shadow-lg shadow-violet-500/25">
              <span className="text-2xl">🤖</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-violet-800 bg-clip-text text-transparent">
                AI Model Training
              </h1>
              <p className="text-slate-600 font-medium">
                Fine-tune the magic trick detection model with your feedback
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Training Status */}
      <div className="mb-8">
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-3 mb-2">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                  <span className="text-sm text-white">⚙️</span>
                </div>
                <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-blue-800 bg-clip-text text-transparent">
                  Training Status
                </h2>
              </div>
              <p className="text-slate-600 font-medium">
                {isTraining 
                  ? `${trainingStatus?.message || 'Training in progress...'} ${trainingProgress}%`
                  : trainingStatus?.message || 'Model is ready for training'
                }
              </p>
              {trainingStatus?.status === 'error' && (
                <div className="mt-2 flex items-center space-x-2 text-red-600">
                  <InformationCircleIcon className="h-4 w-4" />
                  <span className="text-sm font-medium">Training failed - check logs for details</span>
                </div>
              )}
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={handleStartTraining}
                disabled={isTraining || trainingMutation.isPending || (stats?.training_examples || 0) < 10}
                className="flex items-center px-6 py-3 bg-gradient-to-r from-emerald-600 to-green-700 text-white rounded-2xl hover:from-emerald-700 hover:to-green-800 font-semibold shadow-lg shadow-emerald-500/25 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
              >
                {trainingMutation.isPending ? (
                  <LoadingSpinner size="sm" className="mr-2" />
                ) : (
                  <PlayIcon className="h-5 w-5 mr-2" />
                )}
                {isTraining ? 'Training...' : 'Start Training'}
              </button>
            </div>
          </div>

          {(stats?.training_examples || 0) < 10 && (
            <div className="mt-4 p-4 bg-yellow-50/60 backdrop-blur-sm rounded-xl border border-yellow-200/60">
              <div className="flex items-center space-x-2 text-yellow-800">
                <InformationCircleIcon className="h-5 w-5" />
                <span className="font-medium text-sm">
                  Need at least 10 training examples to start training. Current: {stats?.training_examples || 0}
                </span>
              </div>
            </div>
          )}

          {isTraining && (
            <div className="mt-6">
              <div className="bg-slate-200/60 rounded-full h-3 backdrop-blur-sm border border-white/40 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-indigo-600 h-3 rounded-full transition-all duration-500 shadow-sm"
                  style={{ width: `${trainingProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Training Data Stats */}
      <div className="mb-8">
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/25">
              <span className="text-sm text-white">📊</span>
            </div>
            <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-emerald-800 bg-clip-text text-transparent">
              Training Data
            </h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-gradient-to-br from-emerald-50 to-green-50/50 backdrop-blur-sm p-6 rounded-2xl border border-emerald-200/60 text-center hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-green-600 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-lg shadow-emerald-500/25">
                <span className="text-white font-bold text-lg">✓</span>
              </div>
              <div className="text-2xl font-bold text-emerald-700 mb-1">{stats?.correct_detections || 0}</div>
              <div className="text-sm font-semibold text-emerald-800">Correct Detections</div>
            </div>
            
            <div className="bg-gradient-to-br from-red-50 to-rose-50/50 backdrop-blur-sm p-6 rounded-2xl border border-red-200/60 text-center hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
              <div className="w-12 h-12 bg-gradient-to-br from-red-500 to-rose-600 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-lg shadow-red-500/25">
                <span className="text-white font-bold text-lg">✗</span>
              </div>
              <div className="text-2xl font-bold text-red-700 mb-1">{stats?.incorrect_detections || 0}</div>
              <div className="text-sm font-semibold text-red-800">Incorrect Detections</div>
            </div>
            
            <div className="bg-gradient-to-br from-yellow-50 to-amber-50/50 backdrop-blur-sm p-6 rounded-2xl border border-yellow-200/60 text-center hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-amber-600 rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-lg shadow-yellow-500/25">
                <span className="text-white font-bold text-lg">⏳</span>
              </div>
              <div className="text-2xl font-bold text-yellow-700 mb-1">{stats?.pending_review || 0}</div>
              <div className="text-sm font-semibold text-yellow-800">Pending Reviews</div>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-slate-50 to-blue-50/50 rounded-2xl p-4 border border-slate-200/50">
            <p className="text-slate-600 font-medium text-center">
              Training examples available: <span className="font-bold text-slate-800">{stats?.training_examples || 0}</span>
              {(stats?.training_examples || 0) < 10 ? ' (Need at least 10 to start training)' : ' (Ready for training!)'}
            </p>
            {stats?.accuracy !== undefined && (
              <p className="text-slate-600 font-medium text-center mt-2">
                Current accuracy: <span className="font-bold text-emerald-600">{Math.round((stats.accuracy || 0) * 100)}%</span>
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Model Performance */}
      <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20">
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/25">
            <span className="text-sm text-white">📈</span>
          </div>
          <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-indigo-800 bg-clip-text text-transparent">
            Model Performance
          </h2>
        </div>
        
        <div className="space-y-4">
          {[
            { label: 'Accuracy', value: stats?.accuracy ? `${Math.round(stats.accuracy * 100)}%` : 'N/A', color: 'from-emerald-500 to-green-600' },
            { label: 'Total Tricks', value: stats?.total_tricks?.toString() || '0', color: 'from-blue-500 to-indigo-600' },
            { label: 'Training Examples', value: stats?.training_examples?.toString() || '0', color: 'from-purple-500 to-pink-600' },
            { label: 'Pending Review', value: stats?.pending_review?.toString() || '0', color: 'from-amber-500 to-orange-600' }
          ].map((metric, index) => (
            <div key={index} className="flex justify-between items-center p-4 bg-gradient-to-br from-slate-50 to-blue-50/50 rounded-2xl border border-slate-200/50">
              <div className="flex items-center space-x-3">
                <div className={`w-8 h-8 bg-gradient-to-br ${metric.color} rounded-xl flex items-center justify-center shadow-lg`}>
                  <span className="text-white text-xs font-bold">•</span>
                </div>
                <span className="font-semibold text-slate-700">{metric.label}</span>
              </div>
              <span className="font-bold text-lg bg-gradient-to-r from-slate-800 to-blue-800 bg-clip-text text-transparent">
                {metric.value}
              </span>
            </div>
          ))}
        </div>
        
        {modelInfo && (
          <div className="mt-6 p-4 bg-gradient-to-br from-indigo-50 to-purple-50/50 rounded-2xl border border-indigo-200/50">
            <h3 className="font-semibold text-indigo-800 mb-2">Model Information</h3>
            <div className="space-y-1 text-sm text-indigo-700">
              <p>Base Model: {modelInfo.base_model}</p>
              <p>Fine-tuned: {modelInfo.is_fine_tuned ? 'Yes' : 'No'}</p>
              {modelInfo.fine_tuned_path && (
                <p>Fine-tuned Path: {modelInfo.fine_tuned_path}</p>
              )}
              <p>Model Exists: {modelInfo.model_exists ? 'Yes' : 'No'}</p>
              <p>Training Available: {modelInfo.training_available ? 'Yes' : 'No'}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}