import { apiClient } from './client';
import type { ChatResponse } from '../types/api';

/**
 * Sends a natural language message to the /chat endpoint.
 *
 * @param message The user's natural language question
 * @returns Parsed fields, prediction output, and plain-language narrative
 */
export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>(
    '/chat',
    { message },
    { timeout: 300000 } // 5-minute timeout for local LLM inference
  );
  return response.data;
}
