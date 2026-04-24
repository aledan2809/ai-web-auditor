/**
 * AI Router — WebAuditor preset configuration
 *
 * Centralizes all AI calls through AIRouter with smart routing:
 * free providers first (Gemini, Mistral, Cohere, etc.), Claude as fallback.
 */

import { AIRouter, getProjectPreset } from "ai-router";
import type { AIRequest, AIResponse } from "ai-router";

const preset = getProjectPreset("webauditor");

const router = new AIRouter({
  ...preset,
  maxRetries: 2,
  retryDelayMs: 2000,
  maxInputChars: 4000,
});

/**
 * Route an AI request through the WebAuditor preset.
 * Uses free providers first (Gemini, Mistral, Cohere, Together, Fireworks, Groq),
 * then falls back to OpenAI and Claude.
 *
 * @param request - AI request with messages and optional overrides
 * @returns AI response with content, provider info, and latency
 */
export async function routeAI(request: AIRequest): Promise<AIResponse> {
  return router.chat(request);
}

/** Get health status of all configured providers */
export function getProviderHealth() {
  return router.getHealth();
}

/** Get list of providers that have API keys configured */
export function getAvailableProviders() {
  return router.getAvailableProviders();
}

export { router };
export type { AIRequest, AIResponse };
