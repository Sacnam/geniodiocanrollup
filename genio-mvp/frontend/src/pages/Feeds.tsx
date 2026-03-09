import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, Upload, Loader2 } from 'lucide-react';
import { feedsApi } from '../services/api';
import toast from 'react-hot-toast';
import type { Feed } from '../types';

export default function FeedsPage() {
  const [newFeedUrl, setNewFeedUrl] = useState('');
  const queryClient = useQueryClient();

  const { data: feeds, isLoading } = useQuery({
    queryKey: ['feeds'],
    queryFn: () => feedsApi.list().then(r => r.data as Feed[]),
  });

  const addMutation = useMutation({
    mutationFn: (url: string) => feedsApi.add(url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
      setNewFeedUrl('');
      toast.success('Feed added');
    },
    onError: (error: any) => toast.error(error.response?.data?.detail || 'Failed to add feed'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => feedsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
      toast.success('Feed removed');
    },
  });

  const importMutation = useMutation({
    mutationFn: (file: File) => feedsApi.importOpml(file),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
      toast.success(`Imported ${data.data.imported} feeds`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newFeedUrl) addMutation.mutate(newFeedUrl);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) importMutation.mutate(file);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Manage Feeds</h1>

      <div className="card space-y-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="url"
            value={newFeedUrl}
            onChange={(e) => setNewFeedUrl(e.target.value)}
            placeholder="https://example.com/feed.xml"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
          />
          <button type="submit" disabled={addMutation.isPending} className="btn-primary flex items-center gap-2">
            {addMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            Add
          </button>
        </form>

        <div className="flex items-center gap-2">
          <label className="btn-secondary flex items-center gap-2 cursor-pointer">
            <Upload className="w-4 h-4" />
            Import OPML
            <input type="file" accept=".opml,.xml" onChange={handleFileUpload} className="hidden" />
          </label>
          {importMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-8"><Loader2 className="w-8 h-8 animate-spin mx-auto" /></div>
      ) : (
        <div className="space-y-2">
          {feeds?.map((feed) => (
            <div key={feed.id} className="card flex justify-between items-center">
              <div>
                <h3 className="font-medium">{feed.custom_title || feed.title || 'Untitled'}</h3>
                <p className="text-sm text-gray-500 truncate max-w-md">{feed.url}</p>
              </div>
              <button
                onClick={() => deleteMutation.mutate(feed.id)}
                disabled={deleteMutation.isPending}
                className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
          {feeds?.length === 0 && <p className="text-center text-gray-500 py-8">No feeds yet. Add your first feed above.</p>}
        </div>
      )}
    </div>
  );
}
