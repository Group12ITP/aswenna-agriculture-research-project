import { useQuery } from '@tanstack/react-query';
import { fetchModelEvaluation } from '../api/modelEvaluation';
import type { ModelEvaluationResponse } from '../types/api';

export function useModelEvaluation() {
  return useQuery<ModelEvaluationResponse>({
    queryKey: ['model-evaluation'],
    queryFn: fetchModelEvaluation,
    staleTime: 5 * 60 * 1000,
  });
}
