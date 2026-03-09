import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Bookmark, 
  CheckCircle, 
  Archive, 
  Trash2, 
  ExternalLink, 
  Search,
  Filter,
  Plus,
  Clock,
  Tag,
  MoreVertical,
  BookOpen
} from 'lucide-react';
import { readingListApi } from '../services/readingList';

export const ReadingListPage: React.FC = () => {
  const [filter, setFilter] = useState<'all' | 'unread' | 'read' | 'archived'>('all');
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const queryClient = useQueryClient();

  const { data: items, isLoading } = useQuery({
    queryKey: ['reading-list', filter, search],
    queryFn: () => readingListApi.getItems({ filter, search }),
  });

  const { data: stats } = useQuery({
    queryKey: ['reading-list-stats'],
    queryFn: readingListApi.getStats,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: any }) =>
      readingListApi.updateItem(id, updates),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reading-list'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: readingListApi.deleteItem,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reading-list'] }),
  });

  const markAsRead = (id: string) => {
    updateMutation.mutate({ id, updates: { is_read: true } });
  };

  const archiveItem = (id: string) => {
    updateMutation.mutate({ id, updates: { is_archived: true } });
  };

  const getFilterBadge = () => {
    switch (filter) {
      case 'unread': return { label: 'Unread', color: 'bg-blue-100 text-blue-700' };
      case 'read': return { label: 'Read', color: 'bg-green-100 text-green-700' };
      case 'archived': return { label: 'Archived', color: 'bg-gray-100 text-gray-700' };
      default: return { label: 'All', color: 'bg-purple-100 text-purple-700' };
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bookmark className="w-7 h-7 text-purple-600" />
              <div>
                <h1 className="text-xl font-bold">Reading List</h1>
                <p className="text-sm text-gray-500">
                  {stats?.unread || 0} unread · {stats?.total || 0} total
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              <Plus className="w-4 h-4" />
              <span>Save Page</span>
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow mb-6 p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Filter Tabs */}
            <div className="flex gap-2">
              {(['all', 'unread', 'read', 'archived'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium capitalize ${
                    filter === f
                      ? 'bg-purple-100 text-purple-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {f}
                  {f === 'unread' && stats?.unread > 0 && (
                    <span className="ml-2 px-2 py-0.5 bg-purple-600 text-white text-xs rounded-full">
                      {stats.unread}
                    </span>
                  )}
                </button>
              ))}
            </div>

            {/* Search */}
            <div className="flex-1 relative">
              <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search saved items..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
              />
            </div>
          </div>
        </div>

        {/* Items List */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          </div>
        ) : items?.length === 0 ? (
          <div className="text-center py-12">
            <Bookmark className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900">No items found</h3>
            <p className="text-gray-500 mt-1">
              {filter === 'all' 
                ? 'Start saving articles to read later' 
                : `No ${filter} items`}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {items?.map((item: any) => (
              <div
                key={item.id}
                className={`bg-white rounded-lg shadow p-4 transition-all ${
                  item.is_read ? 'opacity-75' : ''
                }`}
              >
                <div className="flex gap-4">
                  {/* Image */}
                  {item.image_url && (
                    <img
                      src={item.image_url}
                      alt=""
                      className="w-24 h-24 object-cover rounded-lg flex-shrink-0"
                    />
                  )}

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className={`font-semibold text-lg ${
                          item.is_read ? 'text-gray-600' : 'text-gray-900'
                        }`}>
                          {item.title}
                        </h3>
                        {item.source_name && (
                          <p className="text-sm text-purple-600">{item.source_name}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {!item.is_read && (
                          <button
                            onClick={() => markAsRead(item.id)}
                            className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                            title="Mark as read"
                          >
                            <CheckCircle className="w-5 h-5" />
                          </button>
                        )}
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                        >
                          <ExternalLink className="w-5 h-5" />
                        </a>
                        <button
                          onClick={() => archiveItem(item.id)}
                          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                          title="Archive"
                        >
                          <Archive className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => deleteMutation.mutate(item.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                          title="Delete"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </div>

                    {item.excerpt && (
                      <p className="text-gray-600 mt-2 line-clamp-2">{item.excerpt}</p>
                    )}

                    {/* Meta */}
                    <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {new Date(item.created_at).toLocaleDateString()}
                      </span>
                      {item.word_count && (
                        <span>{item.word_count} words</span>
                      )}
                      {item.tags && (
                        <span className="flex items-center gap-1">
                          <Tag className="w-4 h-4" />
                          {item.tags}
                        </span>
                      )}
                      {item.is_read && (
                        <span className="text-green-600 flex items-center gap-1">
                          <CheckCircle className="w-4 h-4" />
                          Read
                        </span>
                      )}
                    </div>

                    {/* Notes */}
                    {item.notes && (
                      <div className="mt-3 p-3 bg-yellow-50 rounded-lg text-sm">
                        <p className="font-medium text-yellow-800">Notes:</p>
                        <p className="text-yellow-700">{item.notes}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <AddToReadingListModal onClose={() => setShowAddModal(false)} />
      )}
    </div>
  );
};

// Add Modal Component
const AddToReadingListModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [notes, setNotes] = useState('');
  const [extractContent, setExtractContent] = useState(true);
  const queryClient = useQueryClient();

  const saveMutation = useMutation({
    mutationFn: readingListApi.saveItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reading-list'] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    saveMutation.mutate({
      url,
      title: title || url,
      notes,
    }, {
      onSuccess: () => {
        if (extractContent) {
          // Trigger extraction in background
        }
      }
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4">Save to Reading List</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">URL</label>
              <input
                type="url"
                required
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://..."
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Title (optional)</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Will auto-extract if empty"
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={extractContent}
                onChange={(e) => setExtractContent(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm">Extract full content for offline reading</span>
            </label>
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saveMutation.isPending}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                {saveMutation.isPending ? 'Saving...' : 'Save'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
