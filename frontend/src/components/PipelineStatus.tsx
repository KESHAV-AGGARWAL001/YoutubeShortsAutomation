import type { PipelineStep } from '../api/types';

interface Props {
  steps: PipelineStep[];
  pipelineStatus: string;
  onRunAll: () => void;
  onCancel: () => void;
  onReset: () => void;
}

const STATUS_ICONS: Record<string, string> = {
  pending: '\u25CB',
  running: '\u25CF',
  completed: '\u2713',
  error: '\u2717',
};

export function PipelineStatus({ steps, pipelineStatus, onRunAll, onCancel, onReset }: Props) {
  return (
    <div className="pipeline-status">
      <h3>Pipeline</h3>
      <ul className="step-list">
        {steps.map((step) => (
          <li key={step.id} className={`step-item step-${step.status}`}>
            <span className="step-icon">{STATUS_ICONS[step.status] || '\u25CB'}</span>
            <span className="step-label">{step.label}</span>
            {step.error && <span className="step-error" title={step.error}>!</span>}
          </li>
        ))}
      </ul>
      <div className="pipeline-actions">
        {pipelineStatus === 'running' ? (
          <button className="btn btn-danger" onClick={onCancel}>Cancel</button>
        ) : (
          <>
            <button className="btn btn-primary" onClick={onRunAll}>Run All</button>
            <button className="btn btn-secondary" onClick={onReset}>Reset</button>
          </>
        )}
      </div>
      {pipelineStatus !== 'idle' && (
        <div className={`pipeline-badge badge-${pipelineStatus}`}>
          {pipelineStatus.toUpperCase()}
        </div>
      )}
    </div>
  );
}
