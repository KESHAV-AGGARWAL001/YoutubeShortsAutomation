import { useState } from 'react';

interface Props {
  onUpload: (publishTime: string | undefined) => void;
  loading: boolean;
  videoReady: boolean;
}

export function UploadPanel({ onUpload, loading, videoReady }: Props) {
  const [scheduleMode, setScheduleMode] = useState<'now' | 'scheduled'>('now');
  const [publishDate, setPublishDate] = useState('');
  const [publishTime, setPublishTime] = useState('09:00');

  const handleUpload = () => {
    if (scheduleMode === 'scheduled' && publishDate) {
      const utc = new Date(`${publishDate}T${publishTime}:00`).toISOString();
      onUpload(utc);
    } else {
      onUpload(undefined);
    }
  };

  return (
    <div className="upload-panel">
      <h3>Upload to YouTube</h3>

      <div className="schedule-toggle">
        <label className={scheduleMode === 'now' ? 'active' : ''}>
          <input
            type="radio"
            name="schedule"
            checked={scheduleMode === 'now'}
            onChange={() => setScheduleMode('now')}
          />
          Publish in 15 min
        </label>
        <label className={scheduleMode === 'scheduled' ? 'active' : ''}>
          <input
            type="radio"
            name="schedule"
            checked={scheduleMode === 'scheduled'}
            onChange={() => setScheduleMode('scheduled')}
          />
          Schedule
        </label>
      </div>

      {scheduleMode === 'scheduled' && (
        <div className="schedule-inputs">
          <input
            type="date"
            className="input-field"
            value={publishDate}
            onChange={(e) => setPublishDate(e.target.value)}
          />
          <input
            type="time"
            className="input-field"
            value={publishTime}
            onChange={(e) => setPublishTime(e.target.value)}
          />
        </div>
      )}

      <button
        className="btn btn-upload"
        onClick={handleUpload}
        disabled={loading || !videoReady}
      >
        {loading ? 'Uploading...' : 'Upload to YouTube'}
      </button>

      {!videoReady && (
        <p className="upload-hint">Generate a video first before uploading.</p>
      )}
    </div>
  );
}
