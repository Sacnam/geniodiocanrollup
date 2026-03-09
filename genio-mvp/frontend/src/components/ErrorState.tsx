import React from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface ErrorStateProps {
  title?: string;
  message?: string;
  error?: Error | string;
  onRetry?: () => void;
  showHome?: boolean;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message = 'We encountered an error while loading this content.',
  error,
  onRetry,
  showHome = true,
  className = '',
}) => {
  const navigate = useNavigate();

  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center ${className}`}>
      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
        <AlertCircle className="w-8 h-8 text-red-600" />
      </div>
      
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {title}
      </h3>
      
      <p className="text-gray-600 max-w-md mb-2">
        {message}
      </p>
      
      {error && (
        <p className="text-sm text-gray-500 font-mono bg-gray-100 px-3 py-1 rounded mb-6 max-w-md overflow-hidden text-ellipsis">
          {typeof error === 'string' ? error : error.message}
        </p>
      )}
      
      <div className="flex gap-3">
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        )}
        
        {showHome && (
          <button
            onClick={() => navigate('/feeds')}
            className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Home className="w-4 h-4" />
            Go Home
          </button>
        )}
      </div>
    </div>
  );
};
