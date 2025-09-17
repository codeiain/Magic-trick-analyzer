import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import TricksPage from './pages/TricksPage';
import ReviewPage from './pages/ReviewPage';
import SearchPage from './pages/SearchPage';
import TrainingPage from './pages/TrainingPage';
import BooksPage from './pages/BooksPage';
import TrickDetailPage from './pages/TrickDetailPage';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/40">
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/tricks" element={<TricksPage />} />
              <Route path="/tricks/:id" element={<TrickDetailPage />} />
              <Route path="/books" element={<BooksPage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/review" element={<ReviewPage />} />
              <Route path="/training" element={<TrainingPage />} />
            </Routes>
          </Layout>
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'linear-gradient(135deg, #1e293b, #334155)',
                color: '#f1f5f9',
                border: '1px solid #475569',
                borderRadius: '12px',
                fontSize: '14px',
                fontWeight: '500',
              },
              success: {
                style: {
                  background: 'linear-gradient(135deg, #059669, #10b981)',
                  color: '#f0fdf4',
                },
              },
              error: {
                style: {
                  background: 'linear-gradient(135deg, #dc2626, #ef4444)',
                  color: '#fef2f2',
                },
              },
            }}
          />
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
