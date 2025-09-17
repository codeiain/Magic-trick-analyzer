import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface PaginationProps {
  currentPage: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ currentPage, totalItems, itemsPerPage, onPageChange }: PaginationProps) {
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  if (totalPages <= 1) return null;

  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 7;
    
    if (totalPages <= maxPagesToShow) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 4) {
        for (let i = 1; i <= 5; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 3) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 4; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      }
    }
    
    return pages;
  };

  return (
    <div className="flex items-center justify-between bg-white/60 backdrop-blur-sm rounded-2xl px-6 py-4 border border-slate-200/60 shadow-sm">
      <div className="flex flex-1 justify-between sm:hidden">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="relative inline-flex items-center rounded-xl border border-slate-200 bg-white/80 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-white hover:shadow-md disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          Previous
        </button>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="relative ml-3 inline-flex items-center rounded-xl border border-slate-200 bg-white/80 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-white hover:shadow-md disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          Next
        </button>
      </div>
      
      <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-slate-600 font-medium">
            Showing <span className="font-bold text-slate-800">{startItem}</span> to{' '}
            <span className="font-bold text-slate-800">{endItem}</span> of{' '}
            <span className="font-bold text-slate-800">{totalItems}</span> results
          </p>
        </div>
        
        <div>
          <nav className="isolate inline-flex space-x-1 rounded-xl" aria-label="Pagination">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="relative inline-flex items-center rounded-xl px-3 py-2 text-slate-500 bg-white/60 border border-slate-200/60 hover:bg-white hover:text-slate-700 hover:shadow-md focus:z-20 focus:outline-offset-0 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
            >
              <span className="sr-only">Previous</span>
              <ChevronLeftIcon className="h-4 w-4" aria-hidden="true" />
            </button>
            
            {getPageNumbers().map((page, index) => (
              page === '...' ? (
                <span
                  key={index}
                  className="relative inline-flex items-center px-3 py-2 text-sm font-semibold text-slate-600"
                >
                  ...
                </span>
              ) : (
                <button
                  key={index}
                  onClick={() => onPageChange(page as number)}
                  className={`relative inline-flex items-center px-3 py-2 text-sm font-semibold rounded-xl transition-all duration-200 focus:z-20 focus:outline-offset-0 ${
                    currentPage === page
                      ? 'z-10 bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/25 border border-transparent'
                      : 'text-slate-700 bg-white/60 border border-slate-200/60 hover:bg-white hover:shadow-md hover:text-slate-900'
                  }`}
                >
                  {page}
                </button>
              )
            ))}
            
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="relative inline-flex items-center rounded-xl px-3 py-2 text-slate-500 bg-white/60 border border-slate-200/60 hover:bg-white hover:text-slate-700 hover:shadow-md focus:z-20 focus:outline-offset-0 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
            >
              <span className="sr-only">Next</span>
              <ChevronRightIcon className="h-4 w-4" aria-hidden="true" />
            </button>
          </nav>
        </div>
      </div>
    </div>
  );
}