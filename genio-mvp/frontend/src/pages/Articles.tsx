import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Star, Archive, ExternalLink, Loader2 } from 'lucide-react';
import { articlesApi } from '../services/api';
import type { Article } from '../types';

export default function ArticlesPage() {
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['articles'],
    queryFn: () => articlesApi.list({ per_page: 50 }).then(r => r.data),
  });

  const starMutation = useMutation({
    mutationFn: (id: string) => articlesApi.star(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['articles'] }),
  });

  const articles = data?.items || [];

  const getDeltaBadge = (status: string) => {
    switch (status) {
      case 'novel': return <span className="delta-badge-novel">Novel</span>;
      case 'related': return <span className="delta-badge-related">Related</span>;
      default: return null;
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Articles</h1>

      {isLoading ? (
        <div className="text-center py-8"><Loader2 className="w-8 h-8 animate-spin mx-auto" /></div>
      ) : (
        <div className="grid gap-4">
          {articles.map((article: Article) => (
            <div key={article.id} className={`card ${article.is_read ? 'opacity-75' : ''}`}>
              <div className="flex justify-between items-start">
                <div className="flex-1" onClick={() => setSelectedArticle(article)}>
                  <div className="flex items-center gap-2 mb-1">
                    {getDeltaBadge(article.delta_status)}
                    <span className="text-sm text-gray-500">{article.source}</span>
                  </div>
                  <h3 className={`font-medium ${article.is_read ? 'text-gray-600' : 'text-gray-900'}`}>
                    {article.title || 'Untitled'}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1 line-clamp-2">{article.excerpt}</p>
                </div>
                <div className="flex gap-1 ml-4">
                  <button
                    onClick={() => starMutation.mutate(article.id)}
                    className={`p-2 rounded-lg ${article.is_starred ? 'text-amber-500 bg-amber-50' : 'text-gray-400 hover:bg-gray-100'}`}
                  >
                    <Star className={`w-4 h-4 ${article.is_starred ? 'fill-current' : ''}`} />
                  </button>
                  <a href={article.url} target="_blank" rel="noopener" className="p-2 text-gray-400 hover:bg-gray-100 rounded-lg">
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            </div>
          ))}
          {articles.length === 0 && <p className="text-center text-gray-500 py-8">No articles yet. Add feeds to see content.</p>}
        </div>
      )}

      {selectedArticle && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedArticle(null)}>
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-auto p-6" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-xl font-bold mb-2">{selectedArticle.title}</h2>
            <p className="text-sm text-gray-500 mb-4">{selectedArticle.source}</p>
            <div className="prose max-w-none">
              <p>{selectedArticle.excerpt}</p>
            </div>
            <a href={selectedArticle.url} target="_blank" rel="noopener" className="btn-primary inline-block mt-4">
              Read full article
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
