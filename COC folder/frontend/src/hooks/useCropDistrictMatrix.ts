import { useQuery } from '@tanstack/react-query';
import { getCropDistrictMatrix } from '../api/prediction';
import type { CropDistrictMatrixResponse } from '../types/api';

export function useCropDistrictMatrix() {
  return useQuery<CropDistrictMatrixResponse>({
    queryKey: ['cropDistrictMatrix'],
    queryFn: getCropDistrictMatrix,
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: 2,
  });
}
