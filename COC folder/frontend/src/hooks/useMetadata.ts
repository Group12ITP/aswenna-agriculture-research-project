import { useQuery } from '@tanstack/react-query';
import { getMetadata } from '../api/health';
import type { MetadataResponse } from '../types/api';

export function useMetadata() {
  return useQuery<MetadataResponse>({
    queryKey: ['metadata'],
    queryFn: getMetadata,
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 2,
  });
}
