import React, { useState } from 'react';
import { useMetadata } from '../hooks/useMetadata';
import { useDefaults } from '../hooks/useDefaults';
import { usePrediction } from '../hooks/usePrediction';
import { PredictionForm } from '../components/predict/PredictionForm';
import { PredictionResult } from '../components/predict/PredictionResult';
import type { PredictionRequest, PredictionResponse } from '../types/api';
import { addStoredPrediction } from '../lib/storage';

export const PredictPage: React.FC = () => {
  const { data: metadata } = useMetadata();
  const { data: defaults } = useDefaults();
  const predictionMutation = usePrediction();

  const [activeRequest, setActiveRequest] = useState<PredictionRequest | null>(null);
  const [predictionResult, setPredictionResult] = useState<PredictionResponse | null>(null);

  const handlePredict = async (data: PredictionRequest) => {
    setActiveRequest(data);
    try {
      const res = await predictionMutation.mutateAsync(data);
      setPredictionResult(res);

      // Auto-save to recent predictions in localStorage
      addStoredPrediction({
        request_id: res.request_id,
        timestamp: res.timestamp,
        crop: data.crop,
        district: data.district,
        season: data.season,
        reference_year: res.reference_year,
        predicted_cost: res.predicted_cost,
        interval_low: res.interval_low,
        interval_high: res.interval_high,
        low_confidence: res.low_confidence,
        warning: res.warning,
      });
    } catch {
      // Error is captured by mutation state and displayed in PredictionResult
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Form (5 Cols on Large Screen) */}
        <div className="lg:col-span-6 xl:col-span-5">
          <PredictionForm
            metadata={metadata}
            defaults={defaults}
            isLoading={predictionMutation.isPending}
            onSubmit={handlePredict}
          />
        </div>

        {/* Right Column: Prediction & SHAP Output (7 Cols on Large Screen) */}
        <div className="lg:col-span-6 xl:col-span-7">
          <PredictionResult
            result={predictionResult}
            requestParams={activeRequest}
            isLoading={predictionMutation.isPending}
            error={predictionMutation.error}
          />
        </div>
      </div>
    </div>
  );
};
