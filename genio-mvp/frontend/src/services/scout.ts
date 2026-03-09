import { api } from './api';

export const scoutApi = {
  getAgents: async () => {
    const { data } = await api.get('/lab/scouts');
    return data;
  },

  createAgent: async (agent: {
    name: string;
    description: string;
    query: string;
    sources: string[];
    schedule: string;
  }) => {
    const { data } = await api.post('/lab/scouts', agent);
    return data;
  },

  runAgent: async (id: string) => {
    const { data } = await api.post(`/lab/scouts/${id}/run`);
    return data;
  },

  getFindings: async () => {
    const { data } = await api.get('/lab/findings');
    return data;
  },

  verifyFinding: async (id: string) => {
    const { data } = await api.post(`/lab/findings/${id}/verify`);
    return data;
  },
};
