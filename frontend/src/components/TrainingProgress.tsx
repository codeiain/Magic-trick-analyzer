/**
 * Training Progress Component
 * Shows real-time training progress, metrics, and model comparison
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { trainingApi } from '../lib/api';

interface TrainingProgressProps {
  datasetId: string;
  jobId?: string;
}

interface TrainingMetrics {
  epoch: number;
  training_accuracy: number;
  validation_accuracy: number;
  training_loss: number;
  validation_loss: number;
  epoch_time: number;
  learning_rate: number;
}

interface TrainingStatus {
  status: 'training' | 'completed' | 'failed' | 'pending';
  progress: number;
  message: string;
  current_epoch?: number;
  total_epochs?: number;
  training_history?: TrainingMetrics[];
  model_version?: string;
  validation_accuracy?: number;
  training_duration?: number;
}

export default function TrainingProgress({ datasetId, jobId }: TrainingProgressProps) {
  const [showDetails, setShowDetails] = useState(false);

  // Poll training status
  const { data: status, isLoading } = useQuery({
    queryKey: ['training-status', datasetId, jobId],
    queryFn: () => jobId ? trainingApi.getTrainingJobStatus(jobId) : Promise.resolve(null),
    refetchInterval: 2000, // Poll every 2 seconds during training
    enabled: !!jobId
  });

  const trainingStatus = status as TrainingStatus | null;

  if (isLoading || !trainingStatus) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="text-gray-600">Loading training status...</span>
        </div>
      </div>
    );
  }

  const isTraining = trainingStatus.status === 'training';
  const isCompleted = trainingStatus.status === 'completed';
  const isFailed = trainingStatus.status === 'failed';

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Header */}
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              isTraining ? 'bg-yellow-400 animate-pulse' :
              isCompleted ? 'bg-green-400' :
              isFailed ? 'bg-red-400' : 'bg-gray-400'
            }`}></div>
            <h3 className="text-lg font-semibold">
              Training Progress
            </h3>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              isTraining ? 'bg-yellow-100 text-yellow-800' :
              isCompleted ? 'bg-green-100 text-green-800' :
              isFailed ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'
            }`}>
              {trainingStatus.status.toUpperCase()}
            </span>
          </div>
          
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </button>
        </div>

        <p className="text-gray-600 mt-2">
          {trainingStatus.message}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="p-6 border-b">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-sm text-gray-500">{trainingStatus.progress}%</span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-500 ${
              isCompleted ? 'bg-green-600' :
              isFailed ? 'bg-red-600' : 'bg-blue-600'
            }`}
            style={{ width: `${trainingStatus.progress}%` }}
          />
        </div>

        {trainingStatus.current_epoch && trainingStatus.total_epochs && (
          <div className="flex items-center justify-between mt-3 text-sm text-gray-600">
            <span>Epoch {trainingStatus.current_epoch} of {trainingStatus.total_epochs}</span>
            {trainingStatus.training_duration && (
              <span>Duration: {Math.round(trainingStatus.training_duration)}s</span>
            )}
          </div>
        )}
      </div>

      {/* Key Metrics */}
      {(isCompleted || trainingStatus.validation_accuracy) && (
        <div className="p-6 border-b bg-gray-50">
          <h4 className="font-medium text-gray-900 mb-3">Key Metrics</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {trainingStatus.validation_accuracy && (
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {Math.round(trainingStatus.validation_accuracy * 100)}%
                </div>
                <div className="text-xs text-gray-600">Validation Accuracy</div>
              </div>
            )}
            
            {trainingStatus.model_version && (
              <div className="text-center">
                <div className="text-sm font-mono text-gray-800">
                  {trainingStatus.model_version}
                </div>
                <div className="text-xs text-gray-600">Model Version</div>
              </div>
            )}
            
            {trainingStatus.training_duration && (
              <div className="text-center">
                <div className="text-lg font-bold text-gray-800">
                  {Math.round(trainingStatus.training_duration / 60)}m
                </div>
                <div className="text-xs text-gray-600">Training Time</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Detailed Training History */}
      {showDetails && trainingStatus.training_history && trainingStatus.training_history.length > 0 && (
        <div className="p-6">
          <h4 className="font-medium text-gray-900 mb-4">Training History</h4>
          
          {/* Training Chart Placeholder */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center h-32 text-gray-500">
              <div className="text-center">
                <div className="text-sm font-medium">Training Metrics Visualization</div>
                <div className="text-xs mt-1">Chart would show accuracy and loss over epochs</div>
              </div>
            </div>
          </div>

          {/* Epoch Details Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Epoch</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Train Acc</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Val Acc</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Train Loss</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Val Loss</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-700">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {trainingStatus.training_history.slice(-10).map((metrics, index) => ( // Show last 10 epochs
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-medium">{metrics.epoch}</td>
                    <td className="px-3 py-2 text-green-600">
                      {(metrics.training_accuracy * 100).toFixed(2)}%
                    </td>
                    <td className="px-3 py-2 text-blue-600">
                      {(metrics.validation_accuracy * 100).toFixed(2)}%
                    </td>
                    <td className="px-3 py-2">{metrics.training_loss.toFixed(4)}</td>
                    <td className="px-3 py-2">{metrics.validation_loss.toFixed(4)}</td>
                    <td className="px-3 py-2">{metrics.epoch_time.toFixed(1)}s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Error Details */}
      {isFailed && (
        <div className="p-6 bg-red-50 border-t">
          <h4 className="font-medium text-red-900 mb-2">Training Failed</h4>
          <p className="text-red-700 text-sm">
            {trainingStatus.message || 'An error occurred during training. Please check the logs for more details.'}
          </p>
        </div>
      )}

      {/* Success Details */}
      {isCompleted && (
        <div className="p-6 bg-green-50 border-t">
          <h4 className="font-medium text-green-900 mb-2">Training Completed Successfully!</h4>
          <p className="text-green-700 text-sm">
            Model has been trained and is ready for deployment. You can now use the improved model for trick detection.
          </p>
          {trainingStatus.model_version && (
            <p className="text-green-700 text-sm mt-2">
              New model version: <span className="font-mono font-medium">{trainingStatus.model_version}</span>
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// Mini progress component for dataset cards
export function MiniTrainingProgress({ 
  status, 
  progress = 0, 
  validation_accuracy 
}: { 
  status: string; 
  progress?: number; 
  validation_accuracy?: number; 
}) {
  const isTraining = status === 'training';
  const isCompleted = status === 'trained';

  if (!isTraining && !isCompleted) return null;

  return (
    <div className="mt-2">
      {isTraining && (
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-600">Training...</span>
            <span className="text-xs text-gray-500">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1">
            <div 
              className="bg-blue-600 h-1 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
      
      {isCompleted && validation_accuracy && (
        <div className="text-center">
          <div className="text-lg font-bold text-green-600">
            {Math.round(validation_accuracy * 100)}%
          </div>
          <div className="text-xs text-gray-600">Final Accuracy</div>
        </div>
      )}
    </div>
  );
}