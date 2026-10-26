import { useMutation } from '@tanstack/react-query';
import { predictCost } from '../api/prediction';
import type { PredictionRequest, PredictionResponse } from '../types/api';

export function usePrediction() {
  return useMutation<PredictionResponse, Error, PredictionRequest>({
    mutationFn: (requestData: PredictionRequest) => predictCost(requestData),
  });
}
