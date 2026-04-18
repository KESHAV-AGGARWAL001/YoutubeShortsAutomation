import { useState } from 'react';
import type { PipelineStatus as PipelineStatusType, ScriptData, SeoData } from '../api/types';
import {
  generateScript,
  updateScript as apiUpdateScript,
  generateVoiceover,
  generateVideo,
  generateThumbnail,
  uploadVideo,
  runPipeline,
  cancelPipeline,
  resetPipeline,
} from '../api/client';
import { PipelineStatus } from '../components/PipelineStatus';
import { ContentInput } from '../components/ContentInput';
import { PromptEditor } from '../components/PromptEditor';
import { ScriptEditor } from '../components/ScriptEditor';
import { SeoEditor } from '../components/SeoEditor';
import { VideoPreview } from '../components/VideoPreview';
import { ThumbnailPreview } from '../components/ThumbnailPreview';
import { UploadPanel } from '../components/UploadPanel';
import { LogViewer } from '../components/LogViewer';

interface Props {
  pipelineState: PipelineStatusType;
}

type Tab = 'script' | 'preview' | 'seo';

export function DashboardPage({ pipelineState }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('script');
  const [source, setSource] = useState<'book' | 'custom'>('book');
  const [customContent, setCustomContent] = useState('');
  const [customPrompt, setCustomPrompt] = useState('');
  const [selectedBook, setSelectedBook] = useState('');
  const [loading, setLoading] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);

  const [script, setScript] = useState<ScriptData>(
    pipelineState.script || { hook: '', body: '', cta: '' }
  );
  const [seoData, setSeoData] = useState<SeoData>(
    pipelineState.seo_data || {
      youtube_title: '', description: '', tags: [], keywords: [],
      category: 'Education', category_id: '27', angle_type: '',
    }
  );

  if (pipelineState.script && pipelineState.script !== script) {
    const ps = pipelineState.script;
    if (ps.hook !== script.hook || ps.body !== script.body || ps.cta !== script.cta) {
      if (!saving) {
        setScript(ps);
      }
    }
  }
  if (pipelineState.seo_data && pipelineState.seo_data !== seoData) {
    const ps = pipelineState.seo_data;
    if (ps.youtube_title !== seoData.youtube_title && !saving) {
      setSeoData(ps);
    }
  }

  const setStepLoading = (step: string, val: boolean) =>
    setLoading((prev) => ({ ...prev, [step]: val }));

  const handleGenerateScript = async () => {
    setStepLoading('script', true);
    try {
      const result = await generateScript({
        source,
        custom_content: source === 'custom' ? customContent : undefined,
        custom_prompt: customPrompt || undefined,
        video_number: 1,
      });
      setScript(result.script);
      setSeoData(result.seo_data);
    } catch (e: any) {
      alert(`Script generation failed: ${e.message}`);
    }
    setStepLoading('script', false);
  };

  const handleSaveScript = async () => {
    setSaving(true);
    try {
      await apiUpdateScript(script, seoData);
    } catch (e: any) {
      alert(`Save failed: ${e.message}`);
    }
    setSaving(false);
  };

  const handleGenerateVoiceover = async () => {
    setStepLoading('voiceover', true);
    try {
      await generateVoiceover();
    } catch (e: any) {
      alert(`Voiceover failed: ${e.message}`);
    }
    setStepLoading('voiceover', false);
  };

  const handleGenerateVideo = async () => {
    setStepLoading('video', true);
    try {
      await generateVideo();
    } catch (e: any) {
      alert(`Video assembly failed: ${e.message}`);
    }
    setStepLoading('video', false);
  };

  const handleGenerateThumbnail = async () => {
    setStepLoading('thumbnail', true);
    try {
      await generateThumbnail();
    } catch (e: any) {
      alert(`Thumbnail failed: ${e.message}`);
    }
    setStepLoading('thumbnail', false);
  };

  const handleUpload = async (publishTime: string | undefined) => {
    setStepLoading('upload', true);
    try {
      const result = await uploadVideo({
        publish_time_utc: publishTime,
      });
      if (result.video_url) {
        alert(`Uploaded! ${result.video_url}`);
      }
    } catch (e: any) {
      alert(`Upload failed: ${e.message}`);
    }
    setStepLoading('upload', false);
  };

  const handleRunAll = async () => {
    try {
      await runPipeline({
        source,
        custom_content: source === 'custom' ? customContent : undefined,
        custom_prompt: customPrompt || undefined,
        video_number: 1,
        skip_upload: false,
      });
    } catch (e: any) {
      alert(`Pipeline start failed: ${e.message}`);
    }
  };

  const handleCancel = async () => {
    try {
      await cancelPipeline();
    } catch {}
  };

  const handleReset = async () => {
    try {
      await resetPipeline();
      setScript({ hook: '', body: '', cta: '' });
      setSeoData({
        youtube_title: '', description: '', tags: [], keywords: [],
        category: 'Education', category_id: '27', angle_type: '',
      });
    } catch {}
  };

  const isRunning = pipelineState.pipeline_status === 'running';
  const videoReady = !!pipelineState.output_files?.video;

  return (
    <div className="dashboard">
      <div className="dashboard-sidebar">
        <PipelineStatus
          steps={pipelineState.steps}
          pipelineStatus={pipelineState.pipeline_status}
          onRunAll={handleRunAll}
          onCancel={handleCancel}
          onReset={handleReset}
        />
        <LogViewer logs={pipelineState.logs} />
      </div>

      <div className="dashboard-main">
        <div className="tab-bar">
          <button className={`tab ${activeTab === 'script' ? 'active' : ''}`} onClick={() => setActiveTab('script')}>Script</button>
          <button className={`tab ${activeTab === 'preview' ? 'active' : ''}`} onClick={() => setActiveTab('preview')}>Preview</button>
          <button className={`tab ${activeTab === 'seo' ? 'active' : ''}`} onClick={() => setActiveTab('seo')}>SEO</button>
        </div>

        <div className="tab-content">
          {activeTab === 'script' && (
            <div className="script-tab">
              <ContentInput
                source={source}
                onSourceChange={setSource}
                customContent={customContent}
                onCustomContentChange={setCustomContent}
                selectedBook={selectedBook}
                onBookChange={setSelectedBook}
              />
              <PromptEditor value={customPrompt} onChange={setCustomPrompt} />
              <button
                className="btn btn-primary generate-btn"
                onClick={handleGenerateScript}
                disabled={loading.script || isRunning}
              >
                {loading.script ? 'Generating...' : 'Generate Script'}
              </button>

              {(script.hook || script.body || script.cta) && (
                <ScriptEditor
                  script={script}
                  onChange={setScript}
                  onSave={handleSaveScript}
                  saving={saving}
                />
              )}
            </div>
          )}

          {activeTab === 'preview' && (
            <div className="preview-tab">
              <VideoPreview videoFile={pipelineState.output_files?.video || null} />
              <ThumbnailPreview
                thumbnailFile={pipelineState.output_files?.thumbnail || null}
                onRegenerate={handleGenerateThumbnail}
                loading={!!loading.thumbnail}
              />
            </div>
          )}

          {activeTab === 'seo' && (
            <SeoEditor
              seoData={seoData}
              onChange={setSeoData}
              onSave={handleSaveScript}
              saving={saving}
            />
          )}
        </div>

        <div className="action-bar">
          <button className="btn btn-action" onClick={handleGenerateVoiceover} disabled={loading.voiceover || isRunning}>
            {loading.voiceover ? 'Generating...' : 'Generate Voiceover'}
          </button>
          <button className="btn btn-action" onClick={handleGenerateVideo} disabled={loading.video || isRunning}>
            {loading.video ? 'Assembling...' : 'Assemble Video'}
          </button>
          <button className="btn btn-action" onClick={handleGenerateThumbnail} disabled={loading.thumbnail || isRunning}>
            {loading.thumbnail ? 'Generating...' : 'Thumbnail'}
          </button>
          <UploadPanel
            onUpload={handleUpload}
            loading={!!loading.upload}
            videoReady={videoReady}
          />
        </div>
      </div>
    </div>
  );
}
