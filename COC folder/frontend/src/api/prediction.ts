import { apiClient } from './client';
import type { PredictionRequest, PredictionResponse } from '../types/api';

export async function predictCost(req: PredictionRequest): Promise<PredictionResponse> {
  const response = await apiClient.post<PredictionResponse>('/predict', req);
  return response.data;
}

export async function predictBatch(
  rows: PredictionRequest[],
  onProgress?: (completed: number, total: number) => void
): Promise<PredictionResponse[]> {
  const results: PredictionResponse[] = [];
  for (let i = 0; i < rows.length; i++) {
    const res = await predictCost(rows[i]);
    results.push(res);
    if (onProgress) {
      onProgress(i + 1, rows.length);
    }
    // Small polite delay between requests
    if (i < rows.length - 1) {
      await new Promise((resolve) => setTimeout(resolve, 80));
    }
  }
  return results;
}

export async function getCropDistrictMatrix(): Promise<import('../types/api').CropDistrictMatrixResponse> {
  const response = await apiClient.get<import('../types/api').CropDistrictMatrixResponse>('/crop_district_matrix');
  return response.data;
}
