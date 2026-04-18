import { useState, useEffect } from 'react';
import { fetchSettings, updateSettings } from '../api/client';
import type { SettingsData } from '../api/types';

export function SettingsPanel() {
  const [settings, setSettings] = useState<SettingsData>({
    voice: 'en-US-GuyNeural',
    voice_rate: '-5%',
    voice_pitch: '-3Hz',
    script_version: 'v1',
    gemini_model: 'gemini-2.5-flash',
  });
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');

  useEffect(() => {
    fetchSettings().then(setSettings).catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateSettings(settings);
      setStatus('Settings saved!');
      setTimeout(() => setStatus(''), 3000);
    } catch {
      setStatus('Failed to save');
    }
    setSaving(false);
  };

  return (
    <div className="settings-panel">
      <h2>Settings</h2>

      <div className="settings-group">
        <h3>Voice Configuration</h3>
        <div className="settings-field">
          <label className="field-label">TTS Voice</label>
          <select
            className="input-field"
            value={settings.voice}
            onChange={(e) => setSettings({ ...settings, voice: e.target.value })}
          >
            <option value="en-US-GuyNeural">Guy (Male, Deep)</option>
            <option value="en-US-ChristopherNeural">Christopher (Male, Warm)</option>
            <option value="en-US-EricNeural">Eric (Male, Clear)</option>
            <option value="en-US-AndrewNeural">Andrew (Male, Conversational)</option>
            <option value="en-US-JennyNeural">Jenny (Female, Professional)</option>
            <option value="en-US-AriaNeural">Aria (Female, Expressive)</option>
          </select>
        </div>

        <div className="settings-field">
          <label className="field-label">Speech Rate</label>
          <input
            type="text"
            className="input-field"
            value={settings.voice_rate}
            onChange={(e) => setSettings({ ...settings, voice_rate: e.target.value })}
            placeholder="-5%"
          />
        </div>

        <div className="settings-field">
          <label className="field-label">Voice Pitch</label>
          <input
            type="text"
            className="input-field"
            value={settings.voice_pitch}
            onChange={(e) => setSettings({ ...settings, voice_pitch: e.target.value })}
            placeholder="-3Hz"
          />
        </div>
      </div>

      <div className="settings-group">
        <h3>AI Configuration</h3>
        <div className="settings-field">
          <label className="field-label">Script Version</label>
          <select
            className="input-field"
            value={settings.script_version}
            onChange={(e) => setSettings({ ...settings, script_version: e.target.value })}
          >
            <option value="v1">V1 — Standard</option>
            <option value="v2">V2 — Retention-Optimized</option>
          </select>
        </div>

        <div className="settings-field">
          <label className="field-label">Gemini Model</label>
          <input
            type="text"
            className="input-field"
            value={settings.gemini_model}
            onChange={(e) => setSettings({ ...settings, gemini_model: e.target.value })}
          />
        </div>
      </div>

      <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
        {saving ? 'Saving...' : 'Save Settings'}
      </button>
      {status && <span className="settings-status">{status}</span>}
    </div>
  );
}
