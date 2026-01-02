/**
 * UI Config Loader
 *
 * STEP NEXT-79-FE: Load ui_config.json for example buttons
 *
 * RULES:
 * - Fetch /ui_config.json once at app startup
 * - Cache in memory
 * - Provide typed access to categories/examples
 */

import { UIConfig } from './types';

let cachedConfig: UIConfig | null = null;

export async function loadUIConfig(): Promise<UIConfig> {
  if (cachedConfig) {
    return cachedConfig;
  }

  try {
    const response = await fetch('/ui_config.json');
    if (!response.ok) {
      throw new Error(`Failed to load ui_config.json: ${response.status}`);
    }

    const config = await response.json();
    cachedConfig = config;
    return config;
  } catch (error) {
    console.error('Failed to load UI config:', error);
    // Return minimal config as fallback
    return {
      categories: [],
      available_insurers: [],
      common_coverages: [],
      ui_settings: {
        default_llm_mode: 'OFF',
        evidence_collapsed_by_default: true,
        max_insurers_per_query: 4,
        enable_forbidden_phrase_check: true,
      },
    };
  }
}

export function getCachedConfig(): UIConfig | null {
  return cachedConfig;
}
