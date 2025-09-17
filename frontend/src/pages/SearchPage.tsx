import { useState } from 'react';
import { MagnifyingGlassIcon, AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline';
import LoadingSpinner from '../components/ui/LoadingSpinner';

export default function SearchPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState([]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;

    setIsSearching(true);
    try {
      // TODO: Implement search API call
      setTimeout(() => {
        setResults([]);
        setIsSearching(false);
      }, 1000);
    } catch (error) {
      console.error('Search error:', error);
      setIsSearching(false);
    }
  };

  return (
    <div className="h-full bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      {/* Modern Header */}
      <div className="mb-8">
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20 text-center">
          <div className="flex items-center justify-center space-x-4 mb-4">
            <div className="w-14 h-14 bg-gradient-to-br from-purple-600 to-pink-700 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-500/25">
              <MagnifyingGlassIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-800 to-purple-800 bg-clip-text text-transparent">
                Search Magic Tricks
              </h1>
            </div>
          </div>
          <p className="text-slate-600 font-medium max-w-2xl mx-auto">
            Search through your magic trick database using advanced AI-powered semantic search
          </p>
        </div>
      </div>

      {/* Modern Search Form */}
      <div className="max-w-4xl mx-auto mb-8">
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20">
          <form onSubmit={handleSearch} className="space-y-6">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-6 top-1/2 transform -translate-y-1/2 h-6 w-6 text-slate-400" style={{ maxWidth: '1.5rem', maxHeight: '1.5rem' }} />
              <input
                type="text"
                placeholder="Search for tricks, effects, methods, or keywords..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-16 pr-6 py-4 text-lg bg-white/60 backdrop-blur-sm border border-white/40 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:bg-white/80 transition-all duration-300 placeholder-slate-400 font-medium shadow-lg"
              />
            </div>
            
            <div className="flex justify-center space-x-4">
              <button
                type="submit"
                disabled={isSearching || !searchTerm.trim()}
                className="px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-2xl hover:from-blue-700 hover:to-indigo-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center font-semibold shadow-lg shadow-blue-500/25 hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
              >
                {isSearching ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Searching...
                  </>
                ) : (
                  <>
                    <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                    Search
                  </>
                )}
              </button>
              
              <button
                type="button"
                className="px-6 py-4 bg-white/60 backdrop-blur-sm border border-white/40 text-slate-700 rounded-2xl hover:bg-white/80 hover:border-white/60 flex items-center font-semibold shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
              >
                <AdjustmentsHorizontalIcon className="h-5 w-5 mr-2" />
                Advanced
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Search Results */}
      <div className="max-w-4xl mx-auto">
        {isSearching ? (
          <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-12 shadow-xl border border-white/20 text-center">
            <LoadingSpinner size="lg" />
            <p className="text-slate-600 font-medium mt-6">Searching through magic tricks...</p>
          </div>
        ) : results.length > 0 ? (
          <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20">
            <h2 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-blue-800 bg-clip-text text-transparent mb-6">
              Search Results ({results.length})
            </h2>
            {/* Results will be displayed here */}
          </div>
        ) : searchTerm && !isSearching ? (
          <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-12 shadow-xl border border-white/20 text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-slate-100 to-slate-200 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <span className="text-2xl">🔍</span>
            </div>
            <p className="text-lg font-semibold text-slate-700 mb-2">No results found for "{searchTerm}"</p>
            <p className="text-slate-500 font-medium">Try different keywords or check your spelling</p>
          </div>
        ) : null}
      </div>

      {/* Search Tips */}
      {!searchTerm && (
        <div className="max-w-2xl mx-auto">
          <div className="bg-white/80 backdrop-blur-lg rounded-3xl p-8 shadow-xl border border-white/20">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl flex items-center justify-center shadow-lg shadow-amber-500/25">
                <span className="text-lg">💡</span>
              </div>
              <h3 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-amber-800 bg-clip-text text-transparent">
                Search Tips
              </h3>
            </div>
            
            <div className="space-y-3">
              {[
                'Use specific trick names: "Ambitious Card", "French Drop"',
                'Search by effect type: "card tricks", "coin magic", "mentalism"',
                'Look for methods: "double lift", "palm", "force"',
                'Search by difficulty: "beginner", "intermediate", "advanced"'
              ].map((tip, index) => (
                <div key={index} className="flex items-center space-x-3 p-3 bg-gradient-to-br from-slate-50 to-blue-50/50 rounded-xl border border-slate-200/50">
                  <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-white text-xs font-bold">•</span>
                  </div>
                  <p className="text-slate-600 font-medium">{tip}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
