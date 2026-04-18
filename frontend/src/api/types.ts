export interface ScriptData {
  hook: string;
  body: string;
  cta: string;
}

export interface SeoData {
  youtube_title: string;
  description: string;
  tags: string[];
  keywords: string[];
  category: string;
  category_id: string;
  angle_type: string;
}

export interface BookInfo {
  filename: string;
  display_name: string;
  total_pages: number;
  current_page: number;
  end_page: number;
}

export interface PipelineStep {
  id: string;
  label: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  error?: string | null;
}

export interface PipelineStatus {
  pipeline_status: 'idle' | 'running' | 'completed' | 'error';
  current_step: string | null;
  steps: PipelineStep[];
  script: ScriptData | null;
  seo_data: SeoData | null;
  output_files: Record<string, string>;
  logs: string[];
}

export interface SettingsData {
  voice: string;
  voice_rate: string;
  voice_pitch: string;
  script_version: string;
  gemini_model: string;
}

export interface GenerateScriptRequest {
  source: 'book' | 'custom';
  custom_content?: string;
  custom_prompt?: string;
  book_filename?: string;
  video_number?: number;
}

export interface RunPipelineRequest {
  source: 'book' | 'custom';
  custom_content?: string;
  custom_prompt?: string;
  video_number?: number;
  skip_upload?: boolean;
  publish_time_utc?: string;
}
