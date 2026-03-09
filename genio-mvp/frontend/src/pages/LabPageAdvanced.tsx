/**
 * Advanced Lab Page - Scout Agent Management
 * Lab Module v3.0
 * 
 * Features:
 * - Scout creation with PKG context
 * - Interactive findings with verification
 * - Insight cards
 * - Scout-User interaction (verify this, dwell detection)
 */
import React, { useState, useEffect } from 'react';
import { 
  Bot, 
  Plus, 
  Search, 
  Clock, 
  Filter, 
  Bookmark, 
  Trash2, 
  Play,
  CheckCircle,
  AlertTriangle,
  Lightbulb,
  Sparkles,
  X,
  MessageSquare,
  Zap
} from 'lucide-react';
import { useScouts, useCreateScout, useDeleteScout, useRunScout } from '../hooks/useScouts';
import { useScoutFindings, useScoutInsights } from '../hooks/useScoutFindings';
import { Scout } from '../services/scouts';

interface Finding {
  id: string;
  source_title: string;
  source_url: string;
  source_type: string;
  relevance_score: number;
  explanation: string;
  matched_keywords: string[];
  key_insights: string[];
  contradictions?: string;
  is_read: boolean;
  is_saved: boolean;
  created_at: string;
}

interface Insight {
  id: string;
  insight_type: string;
  title: string;
  description: string;
  confidence_score: number;
  created_at: string;
}

export const LabPageAdvanced: React.FC = () => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedScout, setSelectedScout] = useState<Scout | null>(null);
  const [activeTab, setActiveTab] = useState<'findings' | 'insights' | 'verify'>('findings');
  const [verificationQuery, setVerificationQuery] = useState('');
  
  const { data: scouts, isLoading } = useScouts();
  const createScout = useCreateScout();
  const deleteScout = useDeleteScout();
  const runScout = useRunScout();

  const { data: findings } = useScoutFindings(
    selectedScout?.id || '',
    { unread_only: false }
  );
  
  const { data: insights } = useScoutInsights(selectedScout?.id || '');

  const handleVerify = () => {
    if (verificationQuery.trim() && selectedScout) {
      // Trigger verification task
      console.log('Verifying:', verificationQuery);
      setVerificationQuery('');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <Bot className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Lab</h1>
                <p className="text-purple-100">AI Research Agents with PKG Integration</p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-white text-purple-600 rounded-lg hover:bg-purple-50 transition-colors font-medium"
            >
              <Plus className="w-5 h-5" />
              New Scout
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Scout List */}
          <div className="col-span-4 space-y-4">
            <h2 className="font-semibold text-gray-700 flex items-center gap-2">
              <Zap className="w-5 h-5" />
              Your Scouts
            </h2>
            
            {isLoading ? (
              <div className="text-center py-8">
                <div className="animate-spin w-8 h-8 border-2 border-purple-600 border-t-transparent rounded-full mx-auto" />
              </div>
            ) : scouts?.length === 0 ? (
              <div className="text-center py-8 bg-white rounded-lg shadow">
                <Bot className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No Scouts yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {scouts?.map((scout) => (
                  <div
                    key={scout.id}
                    onClick={() => setSelectedScout(scout)}
                    className={`
                      p-4 rounded-lg cursor-pointer transition-all
                      ${selectedScout?.id === scout.id 
                        ? 'bg-purple-50 border-2 border-purple-500 shadow-md' 
                        : 'bg-white border-2 border-transparent hover:border-purple-200 shadow'}
                    `}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-900 truncate">
                          {scout.name}
                        </h3>
                        <p className="text-sm text-gray-500 truncate mt-1">
                          {scout.research_question}
                        </p>
                        
                        <div className="flex items-center gap-3 mt-3 text-xs">
                          <span className={`
                            px-2 py-1 rounded-full
                            ${scout.status === 'running' ? 'bg-yellow-100 text-yellow-700' : ''}
                            ${scout.status === 'idle' ? 'bg-green-100 text-green-700' : ''}
                            ${scout.status === 'error' ? 'bg-red-100 text-red-700' : ''}
                          `}>
                            {scout.status}
                          </span>
                          
                          {scout.unread_findings > 0 && (
                            <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                              {scout.unread_findings} new
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          runScout.mutate(scout.id);
                        }}
                        disabled={scout.status === 'running'}
                        className="p-2 text-gray-400 hover:text-purple-600 disabled:opacity-50"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Scout Detail */}
          <div className="col-span-8">
            {selectedScout ? (
              <div className="bg-white rounded-lg shadow">
                {/* Scout Header */}
                <div className="p-6 border-b">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-xl font-bold">{selectedScout.name}</h2>
                      <p className="text-gray-600 mt-1">{selectedScout.research_question}</p>
                      
                      <div className="flex flex-wrap gap-2 mt-3">
                        {selectedScout.keywords?.map((kw) => (
                          <span key={kw} className="px-2 py-1 bg-gray-100 text-gray-600 text-sm rounded">
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">
                        {selectedScout.total_findings} findings
                      </span>
                      <button
                        onClick={() => deleteScout.mutate(selectedScout.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Tabs */}
                  <div className="flex gap-4 mt-6">
                    <button
                      onClick={() => setActiveTab('findings')}
                      className={`pb-2 border-b-2 font-medium ${
                        activeTab === 'findings' 
                          ? 'border-purple-600 text-purple-600' 
                          : 'border-transparent text-gray-500'
                      }`}
                    >
                      Findings ({findings?.length || 0})
                    </button>
                    <button
                      onClick={() => setActiveTab('insights')}
                      className={`pb-2 border-b-2 font-medium ${
                        activeTab === 'insights' 
                          ? 'border-purple-600 text-purple-600' 
                          : 'border-transparent text-gray-500'
                      }`}
                    >
                      Insights ({insights?.length || 0})
                    </button>
                    <button
                      onClick={() => setActiveTab('verify')}
                      className={`pb-2 border-b-2 font-medium flex items-center gap-1 ${
                        activeTab === 'verify' 
                          ? 'border-purple-600 text-purple-600' 
                          : 'border-transparent text-gray-500'
                      }`}
                    >
                      <Sparkles className="w-4 h-4" />
                      Verify This
                    </button>
                  </div>
                </div>

                {/* Tab Content */}
                <div className="p-6">
                  {activeTab === 'findings' && (
                    <div className="space-y-4">
                      {findings?.length === 0 ? (
                        <p className="text-gray-500 text-center py-8">
                          No findings yet. Run the Scout to search.
                        </p>
                      ) : (
                        findings?.map((finding: Finding) => (
                          <FindingCard 
                            key={finding.id} 
                            finding={finding} 
                          />
                        ))
                      )}
                    </div>
                  )}

                  {activeTab === 'insights' && (
                    <div className="space-y-4">
                      {insights?.length === 0 ? (
                        <p className="text-gray-500 text-center py-8">
                          No insights yet. Run the Scout to analyze patterns.
                        </p>
                      ) : (
                        insights?.map((insight: Insight) => (
                          <InsightCard key={insight.id} insight={insight} />
                        ))
                      )}
                    </div>
                  )}

                  {activeTab === 'verify' && (
                    <div className="space-y-4">
                      <div className="bg-purple-50 p-4 rounded-lg">
                        <h3 className="font-medium text-purple-900 flex items-center gap-2">
                          <Sparkles className="w-5 h-5" />
                          Ask Scout to Verify
                        </h3>
                        <p className="text-sm text-purple-700 mt-1">
                          Enter a claim or question and Scout will verify it against your Personal Knowledge Graph.
                        </p>
                      </div>
                      
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={verificationQuery}
                          onChange={(e) => setVerificationQuery(e.target.value)}
                          placeholder="Enter a claim to verify..."
                          className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                          onKeyDown={(e) => e.key === 'Enter' && handleVerify()}
                        />
                        <button
                          onClick={handleVerify}
                          disabled={!verificationQuery.trim()}
                          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                        >
                          Verify
                        </button>
                      </div>
                      
                      <div className="text-sm text-gray-500">
                        <p className="font-medium mb-2">Examples:</p>
                        <ul className="list-disc list-inside space-y-1">
                          <li>"Is climate change accelerating faster than predicted?"</li>
                          <li>"What are the counter-arguments to this thesis?"</li>
                          <li>"Verify: AI will replace 50% of jobs by 2030"</li>
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <Bot className="w-16 h-16 text-gray-200 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900">Select a Scout</h3>
                <p className="text-gray-500 mt-2">
                  Choose a Scout from the list to view findings and insights
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create Scout Modal */}
      {showCreateModal && (
        <CreateScoutModal
          onClose={() => setShowCreateModal(false)}
          onCreate={(data) => {
            createScout.mutate(data);
            setShowCreateModal(false);
          }}
        />
      )}
    </div>
  );
};

// Finding Card Component
const FindingCard: React.FC<{ finding: Finding }> = ({ finding }) => {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className={`
      p-4 rounded-lg border transition-all
      ${finding.is_saved ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'}
      ${finding.contradictions ? 'border-l-4 border-l-red-500' : ''}
    `}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-gray-900">{finding.source_title}</h4>
            <span className="text-xs px-2 py-0.5 bg-gray-200 rounded">
              {finding.source_type}
            </span>
            {finding.contradictions && (
              <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                Contradiction
              </span>
            )}
          </div>
          
          <p className="text-sm text-gray-600 mt-1">{finding.explanation}</p>
          
          {/* Relevance Score */}
          <div className="flex items-center gap-2 mt-2">
            <div className="flex-1 max-w-xs">
              <div className="h-2 bg-gray-200 rounded-full">
                <div 
                  className="h-2 bg-purple-500 rounded-full"
                  style={{ width: `${finding.relevance_score * 100}%` }}
                />
              </div>
            </div>
            <span className="text-xs text-gray-500">
              {Math.round(finding.relevance_score * 100)}% relevant
            </span>
          </div>
          
          {/* Keywords */}
          {finding.matched_keywords.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {finding.matched_keywords.map((kw) => (
                <span key={kw} className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded">
                  {kw}
                </span>
              ))}
            </div>
          )}
          
          {/* Contradiction Warning */}
          {finding.contradictions && (
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-800">
              <strong>⚠️ Contradiction Detected:</strong> {finding.contradictions}
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-1 ml-4">
          <button className="p-2 text-gray-400 hover:text-yellow-600">
            <Bookmark className={`w-4 h-4 ${finding.is_saved ? 'fill-yellow-500 text-yellow-500' : ''}`} />
          </button>
        </div>
      </div>
    </div>
  );
};

// Insight Card Component
const InsightCard: React.FC<{ insight: Insight }> = ({ insight }) => {
  const icons = {
    trend: <Zap className="w-5 h-5 text-blue-500" />,
    pattern: <Lightbulb className="w-5 h-5 text-yellow-500" />,
    gap: <AlertTriangle className="w-5 h-5 text-orange-500" />,
    opportunity: <Sparkles className="w-5 h-5 text-green-500" />,
  };
  
  return (
    <div className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-white rounded-lg shadow-sm">
          {icons[insight.insight_type as keyof typeof icons] || <Lightbulb className="w-5 h-5" />}
        </div>
        <div className="flex-1">
          <h4 className="font-medium text-gray-900">{insight.title}</h4>
          <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <CheckCircle className="w-3 h-3" />
              {Math.round(insight.confidence_score * 100)}% confidence
            </span>
            <span>{new Date(insight.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Create Scout Modal
const CreateScoutModal: React.FC<{
  onClose: () => void;
  onCreate: (data: any) => void;
}> = ({ onClose, onCreate }) => {
  const [form, setForm] = useState({
    name: '',
    research_question: '',
    keywords: '',
    sources: ['feeds', 'documents'],
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
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-600" />
            Create Research Scout
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Scout Name
            </label>
            <input
              type="text"
              required
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
              placeholder="e.g., Climate Change Monitor"
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
              placeholder="e.g., climate change, global warming, carbon emissions"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Data Sources
            </label>
            <div className="space-y-2">
              {[
                { id: 'feeds', name: 'My RSS Feeds' },
                { id: 'documents', name: 'My Library Documents' },
                { id: 'web', name: 'Web Search' },
                { id: 'arxiv', name: 'arXiv Papers' },
              ].map((source) => (
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
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
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
              className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              Create Scout
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
