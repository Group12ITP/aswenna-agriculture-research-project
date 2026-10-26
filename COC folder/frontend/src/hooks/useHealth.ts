import { useQuery } from '@tanstack/react-query';
import { getHealth } from '../api/health';
import type { HealthResponse } from '../types/api';

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 30000, // 30 seconds
    retry: 1,
  });
}
