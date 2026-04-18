import type {
  BookInfo,
  ScriptData,
  SeoData,
  PipelineStatus,
  SettingsData,
  GenerateScriptRequest,
  RunPipelineRequest,
} from './types';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchBooks(): Promise<{ books: BookInfo[]; current_book: string | null }> {
  return request('/api/books');
}

export async function generateScript(params: GenerateScriptRequest): Promise<{
  status: string;
  script: ScriptData;
  seo_data: SeoData;
}> {
  return request('/api/generate-script', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function fetchScript(): Promise<{ script: ScriptData; seo_data: SeoData }> {
  return request('/api/script');
}

export async function updateScript(script: ScriptData, seo_data: SeoData): Promise<{ status: string }> {
  return request('/api/script', {
    method: 'PUT',
    body: JSON.stringify({ script, seo_data }),
  });
}

export async function generateVoiceover(): Promise<{
  status: string;
  sections: { name: string; duration_seconds: number; size_kb: number }[];
  total_duration: number;
}> {
  return request('/api/generate-voiceover', { method: 'POST' });
}

export async function generateVideo(): Promise<{
  status: string;
  video_file: string;
  duration_seconds: number;
  size_mb: number;
}> {
  return request('/api/generate-video', { method: 'POST' });
}

export async function generateThumbnail(): Promise<{
  status: string;
  thumbnail_file: string;
  size_kb: number;
}> {
  return request('/api/generate-thumbnail', { method: 'POST' });
}

export async function uploadVideo(params?: {
  publish_time_utc?: string;
  privacy_status?: string;
}): Promise<{ status: string; video_id: string; video_url: string }> {
  return request('/api/upload', {
    method: 'POST',
    body: JSON.stringify(params || {}),
  });
}

export async function runPipeline(params: RunPipelineRequest): Promise<{ status: string }> {
  return request('/api/run-pipeline', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function cancelPipeline(): Promise<{ status: string }> {
  return request('/api/cancel-pipeline', { method: 'POST' });
}

export async function resetPipeline(): Promise<{ status: string }> {
  return request('/api/reset', { method: 'POST' });
}

export async function fetchStatus(): Promise<PipelineStatus> {
  return request('/api/status');
}

export async function fetchSettings(): Promise<SettingsData> {
  return request('/api/settings');
}

export async function updateSettings(settings: SettingsData): Promise<{ status: string }> {
  return request('/api/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
}
