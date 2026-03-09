import React from 'react';

interface SkeletonProps {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '' }) => (
  <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
);

export const ArticleCardSkeleton: React.FC = () => (
  <div className="bg-white rounded-lg shadow-sm p-4 space-y-3">
    <div className="flex items-start gap-4">
      <Skeleton className="w-12 h-12 rounded-lg flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    </div>
    <div className="flex items-center gap-4 pt-2">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-4 w-16" />
    </div>
  </div>
);

export const FeedCardSkeleton: React.FC = () => (
  <div className="bg-white rounded-lg shadow-sm p-4 flex items-center gap-4">
    <Skeleton className="w-10 h-10 rounded-full" />
    <div className="flex-1 space-y-2">
      <Skeleton className="h-5 w-48" />
      <Skeleton className="h-4 w-32" />
    </div>
    <Skeleton className="h-8 w-8 rounded" />
  </div>
);

export const DocumentCardSkeleton: React.FC = () => (
  <div className="bg-white rounded-lg shadow-sm p-4 space-y-3">
    <div className="flex items-start justify-between">
      <div className="flex items-center gap-3">
        <Skeleton className="w-10 h-10 rounded" />
        <div className="space-y-2">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
    <Skeleton className="h-4 w-full" />
    <div className="flex gap-2">
      <Skeleton className="h-6 w-16 rounded-full" />
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
  </div>
);

export const StatsCardSkeleton: React.FC = () => (
  <div className="bg-white rounded-lg shadow-sm p-6 space-y-3">
    <Skeleton className="h-4 w-24" />
    <Skeleton className="h-8 w-16" />
    <Skeleton className="h-3 w-32" />
  </div>
);

export const ListSkeleton: React.FC<{ count?: number }> = ({ count = 5 }) => (
  <div className="space-y-3">
    {Array.from({ length: count }).map((_, i) => (
      <ArticleCardSkeleton key={i} />
    ))}
  </div>
);
