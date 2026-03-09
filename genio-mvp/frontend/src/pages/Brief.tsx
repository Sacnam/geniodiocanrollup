import { useQuery } from '@tanstack/react-query';
import { BookOpen, Loader2 } from 'lucide-react';
import { briefsApi } from '../services/api';
import type { Brief } from '../types';

export default function BriefPage() {
  const { data: brief, isLoading, error } = useQuery({
    queryKey: ['brief', 'today'],
    queryFn: () => briefsApi.today().then(r => r.data as Brief),
    retry: false,
  });

  if (isLoading) {
    return <div className="text-center py-12"><Loader2 className="w-8 h-8 animate-spin mx-auto" /></div>;
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h2 className="text-xl font-medium">No brief yet today</h2>
        <p className="text-gray-600 mt-2">Your daily brief is being prepared</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="text-center pb-6 border-b border-gray-200">
        <h1 className="text-3xl font-bold">{brief?.title}</h1>
        <p className="text-gray-600 mt-2">{brief?.subtitle}</p>
        {brief?.executive_summary && (
          <p className="mt-4 text-lg text-gray-700">{brief.executive_summary}</p>
        )}
      </div>

      <div className="space-y-8">
        {brief?.sections.map((section, idx) => (
          <section key={idx}>
            <h2 className="text-xl font-semibold mb-3">{section.title}</h2>
            <p className="text-gray-700 mb-4">{section.summary}</p>
            <div className="space-y-3">
              {section.articles?.map((article) => (
                <a
                  key={article.id}
                  href={article.url}
                  target="_blank"
                  rel="noopener"
                  className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <h3 className="font-medium">{article.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{article.source}</p>
                </a>
              ))}
            </div>
          </section>
        ))}
      </div>

      {brief?.ai_generated && (
        <div className="text-center text-sm text-gray-500 pt-6 border-t border-gray-200">
          AI-generated brief • {brief?.article_count} articles from {brief?.sources_count} sources
        </div>
      )}
    </div>
  );
}
