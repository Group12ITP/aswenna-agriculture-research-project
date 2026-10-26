export interface PredictionRequest {
  district: string;
  crop: string;
  season: 'Maha' | 'Yala';
  irrigation_type: 'Irrigated' | 'Rainfed' | 'Unspecified';
  reference_year?: number;
  usd_lkr_rate?: number;
  prev_season_cost: number | null;
  allow_extrapolation?: boolean;
}

export interface TopDriver {
  feature: string;
  contribution_pct: number;
  direction: '+' | '-';
}

export interface CostBreakdownItem {
  percent: number;
  estimated_cost: number;
}

export type CostBreakdown = Record<string, CostBreakdownItem>;

export interface PredictionResponse {
  request_id: string;
  timestamp: string;
  predicted_cost: number;
  interval_low: number;
  interval_high: number;
  low_confidence: boolean;
  low_confidence_reason?: string | null;
  reference_note?: string;
  top_drivers: TopDriver[];
  model_version: string;
  reference_year: number;
  prediction_target: string;
  warning?: string | null;
  cost_breakdown?: CostBreakdown;
  breakdown_source?: 'historical_district_crop_ratio' | 'national_crop_fallback' | 'aliased_district_crop_ratio' | string;
  breakdown_note?: string;
  breakdown_alias_note?: string | null;
  lag_saturation_detected?: boolean;
  lag_saturation_threshold?: number | null;
  lag_saturation_note?: string | null;
}

export interface DefaultsResponse {
  reference_year: number;
  usd_lkr_rate_default: number;
  latest_available_costs: Record<string, number>;
}

export interface MetadataResponse {
  model_version: string;
  crops_supported: string[];
  districts_supported: string[];
  seasons_supported: string[];
  irrigation_types_supported: string[];
  training_year_range: [number, number];
  training_usd_lkr_mean: number;
  training_usd_lkr_range?: [number, number];
  low_confidence_threshold_pct?: number;
}

export interface HealthResponse {
  status: string;
  model_version: string;
  pipeline_loaded: boolean;
  uptime_seconds: number;
}

export interface StoredPrediction {
  request_id: string;
  timestamp: string;
  crop: string;
  district: string;
  season: string;
  reference_year: number;
  predicted_cost: number;
  interval_low: number;
  interval_high: number;
  low_confidence: boolean;
  warning?: string | null;
}

export interface CropInfo {
  irrigation_types: ('Irrigated' | 'Rainfed' | 'Unspecified')[];
  seasons: ('Maha' | 'Yala')[];
}

export interface DistrictInfo {
  crops: Record<string, CropInfo>;
}

export interface CropDistrictMatrixResponse {
  districts: Record<string, DistrictInfo>;
  all_crops: string[];
  all_districts: string[];
  total_combinations: number;
  total_samples: number;
}

export interface ParsedInput {
  district: string | null;
  crop: string | null;
  season: string | null;
  irrigation_type: string | null;
  field_size_acres: number | null;
  prev_season_cost: number | null;
  prev_season_cost_source?: 'auto_filled_from_history' | 'officer_provided' | 'unavailable' | string;
  prev_season_cost_source_year?: number | null;
  prev_season_cost_source_season?: string | null;
  usd_lkr_rate?: number | null;
  usd_lkr_rate_source?: string;
  season_inferred?: boolean;
}

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  request_id: string;
  timestamp: string;
  parsed_input: ParsedInput;
  prediction: PredictionResponse;
  narrative: string;
  model_version: string;
  prev_season_cost_used?: number | null;
  prev_season_cost_source?: 'auto_filled_from_history' | 'officer_provided' | 'unavailable' | string;
  prev_season_cost_source_year?: number | null;
  prev_season_cost_source_season?: string | null;
}

export interface ModelEvaluationRow {
  Model_Family: 'Shallow' | 'Deep' | string;
  Model_Name: string;
  GKF_MAE: number;
  GKF_RMSE: number;
  GKF_R2: number;
  LOSO_MAE: number;
  LOSO_RMSE: number;
  LOSO_R2: number;
  Training_Time_Seconds: number;
  Inference_Time_ms: number;
}

export interface ModelEvaluationResponse {
  rows: ModelEvaluationRow[];
  message?: string;
}



