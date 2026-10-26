import { useQuery } from '@tanstack/react-query';
import { getDefaults } from '../api/health';
import type { DefaultsResponse } from '../types/api';

export function useDefaults() {
  return useQuery<DefaultsResponse>({
    queryKey: ['defaults'],
    queryFn: getDefaults,
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 2,
  });
}
