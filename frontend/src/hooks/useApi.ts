import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Site, FilterOptions } from '@/types';

export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: api.health,
    refetchInterval: 30000,
  });
};

export const useSites = () => {
  return useQuery({
    queryKey: ['sites'],
    queryFn: api.getSites,
    refetchInterval: 10000,
  });
};

export const useSite = (id: string) => {
  return useQuery({
    queryKey: ['sites', id],
    queryFn: () => api.getSite(id),
    enabled: !!id,
  });
};

export const useCreateSite = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.createSite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sites'] });
    },
  });
};

export const useUpdateSite = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Site> }) =>
      api.updateSite(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sites'] });
    },
  });
};

export const useDeleteSite = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.deleteSite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sites'] });
    },
  });
};

export const useUptimeMetrics = () => {
  return useQuery({
    queryKey: ['uptime'],
    queryFn: api.getUptimeMetrics,
    refetchInterval: 30000,
  });
};

export const useResponseTimes = (siteId: string, hours: number = 24) => {
  return useQuery({
    queryKey: ['responseTimes', siteId, hours],
    queryFn: () => api.getResponseTimes(siteId, hours),
    enabled: !!siteId,
    refetchInterval: 30000,
  });
};

export const useDowntimeEvents = (siteId?: string) => {
  return useQuery({
    queryKey: ['downtime', siteId],
    queryFn: () => api.getDowntimeEvents(siteId),
    refetchInterval: 30000,
  });
};

export const useDebugEvents = (filters?: FilterOptions) => {
  return useQuery({
    queryKey: ['debugEvents', filters],
    queryFn: () => api.getDebugEvents(filters),
    refetchInterval: 10000,
  });
};

export const useDebugEvent = (id: string) => {
  return useQuery({
    queryKey: ['debugEvents', id],
    queryFn: () => api.getDebugEvent(id),
    enabled: !!id,
  });
};

export const useSLAReports = (period: string = 'month') => {
  return useQuery({
    queryKey: ['sla', period],
    queryFn: () => api.getSLAReports(period),
    refetchInterval: 60000,
  });
};
