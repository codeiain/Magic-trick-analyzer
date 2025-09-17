import { useParams } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

export default function TrickDetailPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg">
                    <ArrowLeftIcon className="h-5 w-5" style={{ maxWidth: '1.25rem', maxHeight: '1.25rem' }} />
        </button>
        <h1 className="text-2xl font-bold text-gray-900">Trick Details</h1>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p className="text-gray-600">
          Trick detail page for ID: {id}
        </p>
        <p className="text-sm text-gray-500 mt-2">
          This page will show detailed information about a specific magic trick.
        </p>
      </div>
    </div>
  );
}
