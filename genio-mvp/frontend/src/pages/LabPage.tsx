import React, { useState } from 'react';
import { 
  Bot, 
  Plus, 
  Search, 
  Clock, 
  Filter, 
  Bookmark, 
  Trash2, 
  Play,
  Pause,
  MoreVertical,
  Sparkles,
  FileText,
  Lightbulb,
  X
} from 'lucide-react';
import { useScouts, useCreateScout, useDeleteScout, useRunScout } from '../hooks/useScouts';
import { Scout } from '../services/scouts';

const SOURCES = [
  { id: 'feeds', name: 'My Feeds', icon: FileText },
  { id: 'documents', name: 'My Library', icon: Bookmark },
  { id: 'arxiv', name: 'arXiv', icon: FileText },
  { id: 'web', name: 'Web Search', icon: Search },
];

const SCHEDULES = [
  { id: 'hourly', name: 'Hourly' },
  { id: 'daily', name: 'Daily' },
  { id: 'weekly', name: 'Weekly' },
];

export const LabPage: React.FC = () => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedScout, setSelectedScout] = useState<Scout | null>(null);
  const { data: scouts, isLoading } = useScouts();
  const createScout = useCreateScout();
  const deleteScout = useDeleteScout();
  const runScout = useRunScout();

  const handleCreate = (data: {
    name: string;
    research_question: string;
    keywords: string[];
    sources: string[];
    schedule: string;
  }) => {
    createScout.mutate(data, {
      onSuccess: () => setShowCreateModal(false),
    });
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this Scout?')) {
      deleteScout.mutate(id);
    }
  };

  const handleRun = (id: string) => {
    runScout.mutate(id);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bot className="w-8 h-8 text-purple-600" />
              <div>
                <h1 className="text-2xl font-bold">Lab</h1>
                <p className="text-sm text-gray-500">AI Research Scouts</p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
              New Scout
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin w-8 h-8 border-2 border-purple-600 border-t-transparent rounded-full mx-auto" />
          </div>
        ) : scouts?.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-lg shadow">
            <Bot className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              No Scout Agents yet
            </h2>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              Create your first Scout to automatically monitor your feeds, 
              documents, and external sources for relevant information.
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 mx-auto"
            >
              <Plus className="w-5 h-5" />
              Create Your First Scout
            </button>
          </div>
        ) : (
          <div className="grid gap-6">
            {scouts?.map((scout) => (
              <div
                key={scout.id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold">{scout.name}</h3>
                        <span className={`
                          px-2 py-0.5 rounded text-xs font-medium
                          ${scout.status === 'running' ? 'bg-yellow-100 text-yellow-700' : ''}
                          ${scout.status === 'idle' ? 'bg-green-100 text-green-700' : ''}
                          ${scout.status === 'error' ? 'bg-red-100 text-red-700' : ''}
                          ${!scout.is_active ? 'bg-gray-100 text-gray-600' : ''}
                        `}>
                          {scout.is_active ? scout.status : 'paused'}
                        </span>
                        {scout.unread_findings > 0 && (
                          <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                            {scout.unread_findings} new
                          </span>
                        )}
                      </div>
                      
                      <p className="text-gray-600 mb-4">{scout.research_question}</p>
                      
                      <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                        <div className="flex items-center gap-1">
                          <Search className="w-4 h-4" />
                          {scout.keywords.length} keywords
                        </div>
                        <div className="flex items-center gap-1">
                          <Filter className="w-4 h-4" />
                          {scout.sources.length} sources
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {scout.schedule}
                        </div>
                        <div className="flex items-center gap-1">
                          <Bookmark className="w-4 h-4" />
                          {scout.total_findings} findings
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => handleRun(scout.id)}
                        disabled={scout.status === 'running'}
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg disabled:opacity-50"
                        title="Run now"
                      >
                        <Play className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => setSelectedScout(scout)}
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                        title="View findings"
                      >
                        <Search className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDelete(scout.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                        title="Delete"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <CreateScoutModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreate}
          isLoading={createScout.isPending}
        />
      )}

      {/* Findings Modal */}
      {selectedScout && (
        <ScoutFindingsModal
          scout={selectedScout}
          onClose={() => setSelectedScout(null)}
        />
      )}
    </div>
  );
};

// Create Scout Modal
const CreateScoutModal: React.FC<{
  onClose: () => void;
  onCreate: (data: any) => void;
  isLoading: boolean;
}> = ({ onClose, onCreate, isLoading }) => {
  const [form, setForm] = useState({
    name: '',
    research_question: '',
    keywords: '',
    sources: ['feeds'],
    schedule: 'daily',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onCreate({
      ...form,
      keywords: form.keywords.split(',').map(k => k.trim()).filter(Boolean),
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b flex items-center justify-between">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            Create New Scout
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name
            </label>
            <input
              type="text"
              required
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
              placeholder="e.g., AI Research Monitor"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Research Question
            </label>
            <textarea
              required
              rows={3}
              value={form.research_question}
              onChange={e => setForm({ ...form, research_question: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
              placeholder="What are you researching?"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Keywords (comma-separated)
            </label>
            <input
              type="text"
              value={form.keywords}
              onChange={e => setForm({ ...form, keywords: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
              placeholder="e.g., machine learning, neural networks, AI safety"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Data Sources
            </label>
            <div className="space-y-2">
              {SOURCES.map((source) => (
                <label key={source.id} className="flex items-center gap-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.sources.includes(source.id)}
                    onChange={e => {
                      if (e.target.checked) {
                        setForm({ ...form, sources: [...form.sources, source.id] });
                      } else {
                        setForm({ ...form, sources: form.sources.filter(s => s !== source.id) });
                      }
                    }}
                    className="w-4 h-4 text-purple-600"
                  />
                  <source.icon className="w-5 h-5 text-gray-400" />
                  <span>{source.name}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Schedule
            </label>
            <select
              value={form.schedule}
              onChange={e => setForm({ ...form, schedule: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              {SCHEDULES.map(s => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

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
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
            >
              {isLoading ? 'Creating...' : 'Create Scout'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Findings Modal
const ScoutFindingsModal: React.FC<{
  scout: Scout;
  onClose: () => void;
}> = ({ scout, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">{scout.name}</h2>
            <p className="text-sm text-gray-500">{scout.research_question}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[60vh]">
          <div className="text-center py-12 text-gray-500">
            <Lightbulb className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Findings will appear here after the Scout runs</p>
            <p className="text-sm mt-2">Run the Scout to search for relevant content</p>
          </div>
        </div>
      </div>
    </div>
  );
};
