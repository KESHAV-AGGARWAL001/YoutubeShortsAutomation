import { useState, useCallback } from 'react';
import type { PipelineStatus } from '../api/types';
import { useEventSource } from './useEventSource';

const INITIAL_STATE: PipelineStatus = {
  pipeline_status: 'idle',
  current_step: null,
  steps: [
    { id: 'generate_script', label: 'Generate Script', status: 'pending' },
    { id: 'generate_voiceover', label: 'Voiceover', status: 'pending' },
    { id: 'assemble_video', label: 'Assemble Video', status: 'pending' },
    { id: 'generate_thumbnail', label: 'Thumbnail', status: 'pending' },
    { id: 'upload', label: 'Upload', status: 'pending' },
  ],
  script: null,
  seo_data: null,
  output_files: {},
  logs: [],
};

export function usePipeline() {
  const [state, setState] = useState<PipelineStatus>(INITIAL_STATE);

  const handleUpdate = useCallback((data: PipelineStatus) => {
    setState(data);
  }, []);

  useEventSource(handleUpdate);

  return { state, setState };
}
