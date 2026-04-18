import { useState } from 'react';
import type { SeoData } from '../api/types';

interface Props {
  seoData: SeoData;
  onChange: (seo: SeoData) => void;
  onSave: () => void;
  saving: boolean;
}

export function SeoEditor({ seoData, onChange, onSave, saving }: Props) {
  const [tagInput, setTagInput] = useState('');

  const addTag = () => {
    const tag = tagInput.trim();
    if (tag && !seoData.tags.includes(tag)) {
      onChange({ ...seoData, tags: [...seoData.tags, tag] });
      setTagInput('');
    }
  };

  const removeTag = (index: number) => {
    onChange({ ...seoData, tags: seoData.tags.filter((_, i) => i !== index) });
  };

  return (
    <div className="seo-editor">
      <h3>SEO Metadata</h3>

      <div className="seo-field">
        <label className="field-label">
          YouTube Title
          <span className="field-count">{seoData.youtube_title.length}/100</span>
        </label>
        <input
          type="text"
          className="input-field"
          value={seoData.youtube_title}
          onChange={(e) => onChange({ ...seoData, youtube_title: e.target.value })}
          maxLength={100}
        />
      </div>

      <div className="seo-field">
        <label className="field-label">Description</label>
        <textarea
          className="input-field"
          value={seoData.description}
          onChange={(e) => onChange({ ...seoData, description: e.target.value })}
          rows={6}
        />
      </div>

      <div className="seo-field">
        <label className="field-label">Tags ({seoData.tags.length})</label>
        <div className="tags-container">
          {seoData.tags.map((tag, i) => (
            <span key={i} className="tag-chip">
              {tag}
              <button className="tag-remove" onClick={() => removeTag(i)}>&times;</button>
            </span>
          ))}
        </div>
        <div className="tag-input-row">
          <input
            type="text"
            className="input-field tag-input"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
            placeholder="Add tag..."
          />
          <button className="btn btn-secondary" onClick={addTag}>Add</button>
        </div>
      </div>

      <div className="seo-field">
        <label className="field-label">Category</label>
        <select
          className="input-field"
          value={seoData.category_id}
          onChange={(e) => onChange({ ...seoData, category_id: e.target.value })}
        >
          <option value="22">People & Blogs (Shorts)</option>
          <option value="27">Education</option>
          <option value="24">Entertainment</option>
          <option value="26">Howto & Style</option>
        </select>
      </div>

      <button className="btn btn-primary" onClick={onSave} disabled={saving}>
        {saving ? 'Saving...' : 'Save SEO Data'}
      </button>
    </div>
  );
}
