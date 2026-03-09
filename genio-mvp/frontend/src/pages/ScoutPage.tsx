import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Telescope, 
  Search, 
  Plus, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Loader2,
  FileText,
  Lightbulb,
  AlertCircle,
  ExternalLink,
  Filter,
  MoreVertical,
  Trash2,
  RefreshCw
} from 'lucide-react';
import { scoutApi } from '../services/scout';

interface ScoutAgent {
  id: string;
  name: string;
  description: string;
  query_template: string;
  sources: string[];
  schedule: string;
  is_active: boolean;
  last_run_at?: string;
  created_at: string;
}

interface ScoutFinding {
  id: string;
  title: string;
  summary: string;
  source_url: string;
  source_name: string;
  relevance_score: number;
  confidence: number;
  is_verified: boolean;
  created_at: string;
}

export const ScoutPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'agents' | 'findings' | 'insights'>('agents');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<ScoutAgent | null>(null);
  const queryClient = useQueryClient();

  const { data: agents, isLoading: loadingAgents } = useQuery({
    queryKey: ['scout-agents'],
    queryFn: scoutApi.getAgents,
  });

  const { data: findings, isLoading: loadingFindings } = useQuery({
    queryKey: ['scout-findings'],
    queryFn: scoutApi.getFindings,
  });

  const runScoutMutation = useMutation({
    mutationFn: scoutApi.runAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scout-findings'] });
    },
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Telescope className="w-8 h-8 text-purple-600" />
              <div>
                <h1 className="text-2xl font-bold">Scout</h1>
                <p className="text-sm text-gray-500">AI-powered research automation</p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              <Plus className="w-4 h-4" />
              <span>New Scout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="flex gap-2 mb-6">
          {(['agents', 'findings', 'insights'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg font-medium capitalize ${
                activeTab === tab
                  ? 'bg-purple-100 text-purple-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {tab}
              {tab === 'findings' && findings?.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-purple-600 text-white text-xs rounded-full">
                  {findings.length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Content */}
        {activeTab === 'agents' && (
          <AgentsTab 
            agents={agents} 
            isLoading={loadingAgents}
            onRun={(id) => runScoutMutation.mutate(id)}
            onSelect={setSelectedAgent}
          />
        )}
        {activeTab === 'findings' && (
          <FindingsTab 
            findings={findings} 
            isLoading={loadingFindings}
          />
        )}
        {activeTab === 'insights' && (
          <InsightsTab />
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <CreateScoutModal onClose={() => setShowCreateModal(false)} />
      )}

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <AgentDetailModal 
          agent={selectedAgent} 
          onClose={() => setSelectedAgent(null)} 
        />
      )}
    </div>
  );
};

// Agents Tab
const AgentsTab: React.FC<{
  agents: ScoutAgent[];
  isLoading: boolean;
  onRun: (id: string) => void;
  onSelect: (agent: ScoutAgent) => void;
}> = ({ agents, isLoading, onRun, onSelect }) => {
  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  if (!agents?.length) {
    return (
      <div className="text-center py-12 bg-white rounded-lg shadow">
        <Telescope className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium">No Scout agents yet</h3>
        <p className="text-gray-500 mt-1">Create your first research agent</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {agents.map((agent) => (
        <div 
          key={agent.id} 
          className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow cursor-pointer"
          onClick={() => onSelect(agent)}
        >
          <div className="flex items-start justify-between mb-4">
            <div className={`p-3 rounded-lg ${agent.is_active ? 'bg-green-100' : 'bg-gray-100'}`}>
              <Telescope className={`w-6 h-6 ${agent.is_active ? 'text-green-600' : 'text-gray-600'}`} />
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRun(agent.id);
              }}
              className="p-2 text-purple-600 hover:bg-purple-50 rounded-lg"
              title="Run now"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
          
          <h3 className="font-semibold text-lg mb-1">{agent.name}</h3>
          <p className="text-gray-500 text-sm mb-4 line-clamp-2">{agent.description}</p>
          
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {agent.schedule}
            </span>
            <span className="flex items-center gap-1">
              <FileText className="w-4 h-4" />
              {agent.sources?.length || 0} sources
            </span>
          </div>
          
          {agent.last_run_at && (
            <p className="text-xs text-gray-400 mt-3">
              Last run: {new Date(agent.last_run_at).toLocaleString()}
            </p>
          )}
        </div>
      ))}
    </div>
  );
};

// Findings Tab
const FindingsTab: React.FC<{ findings: ScoutFinding[]; isLoading: boolean }> = ({ 
  findings, 
  isLoading 
}) => {
  const [filter, setFilter] = useState<'all' | 'verified' | 'unverified'>('all');

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
      </div>
    );
  }

  const filteredFindings = findings?.filter(f => {
    if (filter === 'verified') return f.is_verified;
    if (filter === 'unverified') return !f.is_verified;
    return true;
  });

  return (
    <div>
      {/* Filter */}
      <div className="flex gap-2 mb-4">
        {(['all', 'verified', 'unverified'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium capitalize ${
              filter === f
                ? 'bg-purple-100 text-purple-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Findings List */}
      <div className="space-y-4">
        {filteredFindings?.map((finding) => (
          <div key={finding.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {finding.is_verified ? (
                    <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                      <CheckCircle className="w-3 h-3" />
                      Verified
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                      <AlertCircle className="w-3 h-3" />
                      Unverified
                    </span>
                  )}
                  <span className="text-sm text-gray-500">
                    {Math.round(finding.confidence * 100)}% confidence
                  </span>
                </div>
                
                <h3 className="font-semibold text-lg mb-2">{finding.title}</h3>
                <p className="text-gray-600 mb-3">{finding.summary}</p>
                
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-purple-600">{finding.source_name}</span>
                  <a 
                    href={finding.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-gray-500 hover:text-gray-700"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View source
                  </a>
                </div>
              </div>
              
              <div className="w-16 h-16 flex-shrink-0">
                <div 
                  className="w-full h-full rounded-full flex items-center justify-center text-sm font-bold"
                  style={{
                    background: `conic-gradient(#8b5cf6 ${finding.relevance_score * 360}deg, #e5e7eb 0deg)`
                  }}
                >
                  <span className="bg-white rounded-full w-12 h-12 flex items-center justify-center">
                    {Math.round(finding.relevance_score * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Insights Tab
const InsightsTab: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow p-8 text-center">
      <Lightbulb className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
      <h3 className="text-lg font-medium mb-2">Insights coming soon</h3>
      <p className="text-gray-500">
        Scout is analyzing your research patterns to generate personalized insights.
      </p>
    </div>
  );
};

// Create Scout Modal
const CreateScoutModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    query: '',
    sources: [] as string[],
    schedule: 'daily',
  });
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: scoutApi.createAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scout-agents'] });
      onClose();
    },
  });

  const handleSubmit = () => {
    createMutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
        <div className="p-6 border-b">
          <h2 className="text-xl font-bold">Create Scout Agent</h2>
          <p className="text-gray-500">Step {step} of 3</p>
        </div>

        <div className="p-6">
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., AI Research Monitor"
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="What should this scout monitor?"
                  rows={3}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Research Query</label>
                <textarea
                  value={formData.query}
                  onChange={(e) => setFormData({ ...formData, query: e.target.value })}
                  placeholder="e.g., Latest developments in LLM architecture"
                  rows={4}
                  className="w-full px-3 py-2 border rounded-lg"
                />
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Sources</label>
                <div className="space-y-2">
                  {['My Feeds', 'My Documents', 'Web Search', 'arXiv'].map((source) => (
                    <label key={source} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.sources.includes(source)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({ ...formData, sources: [...formData.sources, source] });
                          } else {
                            setFormData({ 
                              ...formData, 
                              sources: formData.sources.filter(s => s !== source) 
                            });
                          }
                        }}
                        className="rounded"
                      />
                      <span>{source}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Schedule</label>
                <select
                  value={formData.schedule}
                  onChange={(e) => setFormData({ ...formData, schedule: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>
            </div>
          )}
        </div>

        <div className="p-6 border-t flex justify-between">
          <button
            onClick={step === 1 ? onClose : () => setStep(step - 1)}
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            {step === 1 ? 'Cancel' : 'Back'}
          </button>
          <button
            onClick={step === 3 ? handleSubmit : () => setStep(step + 1)}
            disabled={createMutation.isPending}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            {createMutation.isPending 
              ? 'Creating...' 
              : step === 3 ? 'Create Scout' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Agent Detail Modal
const AgentDetailModal: React.FC<{ agent: ScoutAgent; onClose: () => void }> = ({ 
  agent, 
  onClose 
}) => {
  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
        <div className="p-6 border-b flex items-center justify-between">
          <h2 className="text-xl font-bold">{agent.name}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XCircle className="w-6 h-6" />
          </button>
        </div>
        <div className="p-6 space-y-4">
          <p className="text-gray-600">{agent.description}</p>
          
          <div>
            <h4 className="font-medium mb-2">Query Template</h4>
            <code className="block bg-gray-100 p-3 rounded-lg text-sm">
              {agent.query_template}
            </code>
          </div>
          
          <div>
            <h4 className="font-medium mb-2">Sources</h4>
            <div className="flex flex-wrap gap-2">
              {agent.sources?.map((source) => (
                <span key={source} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                  {source}
                </span>
              ))}
            </div>
          </div>
          
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              Runs {agent.schedule}
            </span>
            <span className={`flex items-center gap-1 ${agent.is_active ? 'text-green-600' : 'text-gray-400'}`}>
              {agent.is_active ? '● Active' : '○ Inactive'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
