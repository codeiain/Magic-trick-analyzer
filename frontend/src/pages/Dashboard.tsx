import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '../lib/api';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import StatsCard from '../components/ui/StatsCard';

interface DashboardStats {
  total_tricks: number;
  pending_review: number;
  books_processed: number;
  accuracy: number;
}

export default function Dashboard() {
  const { data: stats, isLoading, error } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
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

      {/* Modern Activity Section */}
      <div className="bg-white/80 backdrop-blur-lg p-8 rounded-3xl shadow-xl border border-white/20">
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-500/25">
            <span className="text-lg">📊</span>
          </div>
          <div>
            <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-purple-800 bg-clip-text text-transparent">
              Recent Activity
            </h2>
            <p className="text-slate-600 font-medium">Latest trick detections and reviews</p>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-slate-50 to-blue-50/50 rounded-2xl p-6 border border-slate-200/50">
          <div className="text-center text-slate-500">
            <div className="w-16 h-16 bg-white/80 backdrop-blur-sm rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <span className="text-2xl">🔄</span>
            </div>
            <p className="font-medium">Recent activity coming soon</p>
            <p className="text-sm mt-1">Trick detections and reviews will appear here</p>
          </div>
        </div>
      </div>
    </div>
  );
}