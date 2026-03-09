import React, { useState, useRef, useEffect } from 'react';
import { 
  Search, 
  Loader2, 
  BookOpen, 
  GitBranch, 
  Quote, 
  ChevronDown, 
  ChevronUp,
  Filter,
  Sparkles,
  Link2,
  AlertCircle,
  CheckCircle2,
  X
} from 'lucide-react';
import { useGraphRAG } from '../../hooks/useLibrary';
import { GraphRAGResult } from '../../services/library';

interface GraphRAGSearchProps {
  className?: string;
}

interface SearchFilters {
  includeDocuments: boolean;
  includeConcepts: boolean;
  includeAtoms: boolean;
  minConfidence: number;
  maxResults: number;
}

interface Citation {
  id: string;
  text: string;
  source: string;
  relevance: number;
}

export const GraphRAGSearch: React.FC<GraphRAGSearchProps> = ({ className = '' }) => {
  const [query, setQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [result, setResult] = useState<GraphRAGResult | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [expandedSource, setExpandedSource] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFilters>({
    includeDocuments: true,
    includeConcepts: true,
    includeAtoms: true,
    minConfidence: 0.7,
    maxResults: 10,
  });
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const graphRAGMutation = useGraphRAG();

  // Load search history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('graphrag_history');
    if (saved) {
      setSearchHistory(JSON.parse(saved));
    }
  }, []);

  const saveToHistory = (q: string) => {
    if (!q.trim()) return;
    const newHistory = [q, ...searchHistory.filter(h => h !== q)].slice(0, 10);
    setSearchHistory(newHistory);
    localStorage.setItem('graphrag_history', JSON.stringify(newHistory));
  };

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim()) return;

    setSubmittedQuery(query);
    setShowHistory(false);
    saveToHistory(query);

    try {
      const data = await graphRAGMutation.mutateAsync(query);
      setResult(data);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const handleHistoryClick = (historyQuery: string) => {
    setQuery(historyQuery);
    setShowHistory(false);
    inputRef.current?.focus();
  };

  const clearHistory = () => {
    setSearchHistory([]);
    localStorage.removeItem('graphrag_history');
  };

  // Extract citations from answer text
  const extractCitations = (answer: string): { text: string; citations: Citation[] } => {
    const citationRegex = /\[(\d+)\]/g;
    const citations: Citation[] = [];
    let match;

    while ((match = citationRegex.exec(answer)) !== null) {
      const id = match[1];
      if (result?.sources[parseInt(id) - 1]) {
        const source = result.sources[parseInt(id) - 1];
        if (!citations.find(c => c.id === id)) {
          citations.push({
            id,
            text: source.excerpt,
            source: source.title,
            relevance: source.relevance_score,
          });
        }
      }
    }

    // Replace citation markers with styled spans
    const textWithStyledCitations = answer.replace(
      citationRegex,
      (match, id) => `<span class="citation-marker" data-id="${id}">${match}</span>`
    );

    return { text: textWithStyledCitations, citations };
  };

  const { text: processedAnswer, citations } = result 
    ? extractCitations(result.answer) 
    : { text: '', citations: [] };

  return (
    <div className={`w-full max-w-4xl mx-auto ${className}`}>
      {/* Search Header */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold mb-2 flex items-center justify-center gap-2">
          <Sparkles className="w-6 h-6 text-purple-600" />
          Knowledge Graph Search
        </h2>
        <p className="text-gray-600">
          Ask questions across your documents using semantic + graph search
        </p>
      </div>

      {/* Search Input */}
      <div className="relative mb-6">
        <form onSubmit={handleSearch}>
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setShowHistory(true)}
              placeholder="Ask anything about your documents..."
              className="w-full pl-12 pr-24 py-4 border-2 border-gray-200 rounded-xl text-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all"
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
              <button
                type="button"
                onClick={() => setShowFilters(!showFilters)}
                className={`p-2 rounded-lg transition-colors ${
                  showFilters ? 'bg-purple-100 text-purple-700' : 'hover:bg-gray-100'
                }`}
              >
                <Filter className="w-5 h-5" />
              </button>
              <button
                type="submit"
                disabled={graphRAGMutation.isPending || !query.trim()}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {graphRAGMutation.isPending ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  'Search'
                )}
              </button>
            </div>
          </div>
        </form>

        {/* Search History Dropdown */}
        {showHistory && searchHistory.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-lg border z-10">
            <div className="flex items-center justify-between p-3 border-b">
              <span className="text-sm font-medium text-gray-600">Recent Searches</span>
              <button
                onClick={clearHistory}
                className="text-xs text-red-600 hover:text-red-700"
              >
                Clear
              </button>
            </div>
            {searchHistory.map((historyQuery, idx) => (
              <button
                key={idx}
                onClick={() => handleHistoryClick(historyQuery)}
                className="w-full text-left px-4 py-3 hover:bg-gray-50 flex items-center gap-2"
              >
                <Search className="w-4 h-4 text-gray-400" />
                <span className="text-sm">{historyQuery}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filters.includeDocuments}
                onChange={(e) => setFilters(f => ({ ...f, includeDocuments: e.target.checked }))}
                className="rounded"
              />
              <span className="text-sm">Documents</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filters.includeConcepts}
                onChange={(e) => setFilters(f => ({ ...f, includeConcepts: e.target.checked }))}
                className="rounded"
              />
              <span className="text-sm">Concepts</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filters.includeAtoms}
                onChange={(e) => setFilters(f => ({ ...f, includeAtoms: e.target.checked }))}
                className="rounded"
              />
              <span className="text-sm">Atoms</span>
            </label>
            <div className="flex items-center gap-2">
              <span className="text-sm whitespace-nowrap">Min Confidence:</span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={filters.minConfidence}
                onChange={(e) => setFilters(f => ({ ...f, minConfidence: parseFloat(e.target.value) }))}
                className="w-20"
              />
              <span className="text-sm w-8">{Math.round(filters.minConfidence * 100)}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {graphRAGMutation.isPending && (
        <div className="text-center py-12">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-purple-600 mb-4" />
          <p className="text-gray-600">Searching across your knowledge graph...</p>
          <p className="text-sm text-gray-500 mt-1">This may take a few seconds</p>
        </div>
      )}

      {result && !graphRAGMutation.isPending && (
        <div className="space-y-6">
          {/* Answer Card */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-purple-600" />
              <h3 className="font-semibold">Answer</h3>
              {result.concepts.length > 0 && (
                <span className="text-sm text-gray-500">
                  ({result.concepts.length} concepts referenced)
                </span>
              )}
            </div>
            
            <div 
              className="prose max-w-none text-gray-800 leading-relaxed"
              dangerouslySetInnerHTML={{ __html: processedAnswer }}
            />

            {/* Citations */}
            {citations.length > 0 && (
              <div className="mt-6 pt-4 border-t">
                <h4 className="text-sm font-medium text-gray-600 mb-3">Citations</h4>
                <div className="space-y-2">
                  {citations.map((citation) => (
                    <div
                      key={citation.id}
                      onClick={() => setExpandedSource(expandedSource === citation.id ? null : citation.id)}
                      className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                    >
                      <span className="flex-shrink-0 w-6 h-6 bg-purple-100 text-purple-700 rounded flex items-center justify-center text-sm font-medium">
                        {citation.id}
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">{citation.source}</p>
                        {expandedSource === citation.id ? (
                          <p className="text-sm text-gray-600 mt-1">{citation.text}</p>
                        ) : (
                          <p className="text-sm text-gray-500 truncate">{citation.text}</p>
                        )}
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
                            {Math.round(citation.relevance * 100)}% match
                          </span>
                          {expandedSource === citation.id ? (
                            <ChevronUp className="w-4 h-4 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sources Panel */}
          <div className="bg-white rounded-xl shadow-sm border">
            <div className="p-4 border-b flex items-center justify-between">
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold">Sources</h3>
              </div>
              <span className="text-sm text-gray-500">
                {result.sources.length} documents found
              </span>
            </div>
            
            <div className="divide-y">
              {result.sources.map((source, idx) => (
                <div
                  key={source.document_id}
                  className="p-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-400">[{idx + 1}]</span>
                        <h4 className="font-medium">{source.title}</h4>
                      </div>
                      <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                        "{source.excerpt}"
                      </p>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <div 
                        className="w-12 h-12 rounded-full flex items-center justify-center text-sm font-medium"
                        style={{
                          background: `conic-gradient(#8b5cf6 ${source.relevance_score * 360}deg, #e5e7eb 0deg)`
                        }}
                      >
                        <span className="bg-white rounded-full w-10 h-10 flex items-center justify-center">
                          {Math.round(source.relevance_score * 100)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Concepts Used */}
          {result.concepts.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border p-4">
              <div className="flex items-center gap-2 mb-3">
                <GitBranch className="w-5 h-5 text-green-600" />
                <h3 className="font-semibold">Concepts Used</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {result.concepts.map((concept, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm"
                  >
                    {concept}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!result && !graphRAGMutation.isPending && !submittedQuery && (
        <div className="text-center py-12 text-gray-500">
          <Search className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-lg font-medium">Start searching your knowledge</p>
          <p className="mt-2">Try asking questions like:</p>
          <div className="mt-4 space-y-2">
            {[
              "What are the main themes in my documents?",
              "How does concept X relate to concept Y?",
              "Summarize the key findings about Z",
              "What contradictions exist in my sources?",
            ].map((example, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuery(example);
                  inputRef.current?.focus();
                }}
                className="block w-full text-left px-4 py-2 text-sm text-purple-600 hover:bg-purple-50 rounded-lg max-w-md mx-auto"
              >
                "{example}"
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
