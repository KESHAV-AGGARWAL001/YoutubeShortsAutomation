import { useEffect, useRef } from 'react';

interface Props {
  logs: string[];
}

export function LogViewer({ logs }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="log-viewer">
      <h4>Logs</h4>
      <div className="log-container" ref={containerRef}>
        {logs.length === 0 ? (
          <span className="log-empty">No logs yet</span>
        ) : (
          logs.map((line, i) => (
            <div key={i} className="log-line">{line}</div>
          ))
        )}
      </div>
    </div>
  );
}
