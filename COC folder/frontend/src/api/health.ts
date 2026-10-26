import { apiClient } from './client';
import type { HealthResponse, MetadataResponse, DefaultsResponse } from '../types/api';

export async function getHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>('/health');
  return response.data;
}

export async function getMetadata(): Promise<MetadataResponse> {
  const response = await apiClient.get<MetadataResponse>('/metadata');
  return response.data;
}

export async function getDefaults(): Promise<DefaultsResponse> {
  const response = await apiClient.get<DefaultsResponse>('/defaults');
  return response.data;
}
