interface Props {
  videoFile: string | null;
}

export function VideoPreview({ videoFile }: Props) {
  if (!videoFile) {
    return (
      <div className="video-preview empty">
        <p>No video generated yet. Run the pipeline to create a video.</p>
      </div>
    );
  }

  const src = `/api/output/${videoFile}?t=${Date.now()}`;

  return (
    <div className="video-preview">
      <h3>Video Preview</h3>
      <video
        key={src}
        controls
        className="video-player"
        src={src}
      >
        Your browser does not support video playback.
      </video>
    </div>
  );
}
