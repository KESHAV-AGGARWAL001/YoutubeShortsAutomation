interface Props {
  value: string;
  onChange: (text: string) => void;
}

export function PromptEditor({ value, onChange }: Props) {
  return (
    <div className="prompt-editor">
      <label className="field-label">
        Custom AI Prompt <span className="optional">(optional)</span>
      </label>
      <textarea
        className="input-field prompt-textarea"
        placeholder="Override the default prompt. E.g., 'Write a motivational short about morning routines, make it intense and direct...'"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={4}
      />
    </div>
  );
}
