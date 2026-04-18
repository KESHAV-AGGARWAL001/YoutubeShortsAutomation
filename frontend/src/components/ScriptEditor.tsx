import type { ScriptData } from '../api/types';

interface Props {
  script: ScriptData;
  onChange: (script: ScriptData) => void;
  onSave: () => void;
  saving: boolean;
}

function wordCount(text: string): number {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

export function ScriptEditor({ script, onChange, onSave, saving }: Props) {
  const totalWords = wordCount(script.hook) + wordCount(script.body) + wordCount(script.cta);

  return (
    <div className="script-editor">
      <div className="script-header">
        <h3>Script</h3>
        <div className="word-count">
          <span className={totalWords > 70 ? 'over-limit' : ''}>{totalWords}/70 words</span>
        </div>
      </div>

      <div className="script-field">
        <label className="field-label">Hook</label>
        <textarea
          className="input-field"
          value={script.hook}
          onChange={(e) => onChange({ ...script, hook: e.target.value })}
          rows={2}
          placeholder="Opening hook line..."
        />
        <span className="field-count">{wordCount(script.hook)} words</span>
      </div>

      <div className="script-field">
        <label className="field-label">Body</label>
        <textarea
          className="input-field"
          value={script.body}
          onChange={(e) => onChange({ ...script, body: e.target.value })}
          rows={5}
          placeholder="Main script content..."
        />
        <span className="field-count">{wordCount(script.body)} words</span>
      </div>

      <div className="script-field">
        <label className="field-label">CTA / Loop Ending</label>
        <textarea
          className="input-field"
          value={script.cta}
          onChange={(e) => onChange({ ...script, cta: e.target.value })}
          rows={2}
          placeholder="Call to action / rewatch trigger..."
        />
        <span className="field-count">{wordCount(script.cta)} words</span>
      </div>

      <button className="btn btn-primary" onClick={onSave} disabled={saving}>
        {saving ? 'Saving...' : 'Save Script'}
      </button>
    </div>
  );
}
