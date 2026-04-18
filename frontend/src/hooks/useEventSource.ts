import { useEffect, useRef, useCallback } from 'react';
import type { PipelineStatus } from '../api/types';

export function useEventSource(onUpdate: (data: PipelineStatus) => void) {
  const esRef = useRef<EventSource | null>(null);
  const onUpdateRef = useRef(onUpdate);
  onUpdateRef.current = onUpdate;

  const connect = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
    }

    const es = new EventSource('/api/status/stream');
    esRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as PipelineStatus;
        onUpdateRef.current(data);
      } catch {
        // ignore parse errors
      }
    };

    es.onerror = () => {
      es.close();
      setTimeout(connect, 3000);
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      esRef.current?.close();
    };
  }, [connect]);
}
