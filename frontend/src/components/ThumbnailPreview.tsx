interface Props {
  thumbnailFile: string | null;
  onRegenerate: () => void;
  loading: boolean;
}

export function ThumbnailPreview({ thumbnailFile, onRegenerate, loading }: Props) {
  return (
    <div className="thumbnail-preview">
      <h3>Thumbnail</h3>
      {thumbnailFile ? (
        <img
          src={`/api/output/${thumbnailFile}?t=${Date.now()}`}
          alt="Video thumbnail"
          className="thumbnail-image"
        />
      ) : (
        <div className="thumbnail-placeholder">No thumbnail generated yet</div>
      )}
      <button
        className="btn btn-secondary"
        onClick={onRegenerate}
        disabled={loading}
      >
        {loading ? 'Generating...' : 'Regenerate Thumbnail'}
      </button>
    </div>
  );
}
