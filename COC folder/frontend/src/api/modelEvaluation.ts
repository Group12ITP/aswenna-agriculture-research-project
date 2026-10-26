import { apiClient } from './client';
import type { ModelEvaluationResponse } from '../types/api';

export async function fetchModelEvaluation(): Promise<ModelEvaluationResponse> {
  const response = await apiClient.get<ModelEvaluationResponse>('/model-evaluation');
  return response.data;
}
