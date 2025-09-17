import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  SparklesIcon, 
  BookOpenIcon, 
  MagnifyingGlassIcon,
  AcademicCapIcon,
  CogIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

interface LayoutProps {
  children: ReactNode;
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'All Tricks', href: '/tricks', icon: SparklesIcon },
  { name: 'Books', href: '/books', icon: BookOpenIcon },
  { name: 'Search', href: '/search', icon: MagnifyingGlassIcon },
  { name: 'Review', href: '/review', icon: AcademicCapIcon },
  { name: 'Training', href: '/training', icon: CogIcon },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Modern Sidebar */}
      <div className="flex-shrink-0">
        <div className="flex h-full w-72 flex-col">
          <div className="flex min-h-0 flex-1 flex-col bg-white/80 backdrop-blur-xl shadow-xl border-r border-slate-200/60">
            <div className="flex flex-1 flex-col overflow-y-auto pt-6 pb-4">
              {/* Modern Logo */}
              <div className="flex flex-shrink-0 items-center px-6 mb-8">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25">
                    <SparklesIcon 
                      className="w-5 h-5 text-white" 
                      style={{ maxWidth: '1.25rem', maxHeight: '1.25rem' }}
                    />
                  </div>
                  <div>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-slate-800 to-blue-800 bg-clip-text text-transparent">
                      Magic Analyzer
                    </h1>
                    <p className="text-sm text-slate-500 font-medium">AI-Powered Discovery</p>
                  </div>
                </div>
              </div>

              {/* Modern Navigation */}
              <nav className="mt-2 flex-1 space-y-2 px-4">
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`${
                        isActive
                          ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/25'
                          : 'text-slate-600 hover:bg-white/60 hover:text-slate-800 hover:shadow-md'
                      } group flex items-center px-4 py-3 text-sm font-semibold rounded-2xl transition-all duration-300 hover:-translate-y-0.5 border border-transparent ${
                        !isActive ? 'hover:border-slate-200/60' : ''
                      }`}
                    >
                      <item.icon
                        className={`${
                          isActive ? 'text-white' : 'text-slate-500 group-hover:text-slate-600'
                        } mr-3 h-5 w-5 flex-shrink-0`}
                        style={{ maxWidth: '1.25rem', maxHeight: '1.25rem' }}
                      />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>
            </div>

            {/* Modern Footer */}
            <div className="flex flex-shrink-0 border-t border-slate-200/60 p-6">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-gradient-to-br from-slate-100 to-slate-200 rounded-2xl flex items-center justify-center">
                  <ChartBarIcon 
                    className="w-5 h-5 text-slate-600" 
                    style={{ maxWidth: '1.25rem', maxHeight: '1.25rem' }}
                  />
                </div>
                <div className="ml-3">
                  <p className="text-sm font-semibold text-slate-800">Magic Analyzer</p>
                  <p className="text-xs text-slate-500 font-medium">Version 2.0</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content with modern styling */}
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          {children}
        </main>
      </div>
    </div>
  );
}
