import * as z from 'zod/v4';

const root = z.string().min(1).describe('Absolute project folder returned by list_projects or import_audio');
const seconds = z.number().nonnegative();
const track = z.enum(['beats', 'sections', 'lyrics', 'words', 'vocalEvents', 'chords', 'key']);
const revision = z.number().int().nonnegative();
const runId = z.string().nullable();
const options = z.strictObject({
  mode: z.enum(['japanese', 'multilingual', 'instrumental']),
  scope: z.enum(['harmony', 'vocal-events', 'vocal-comparison', 'separation-comparison']).optional(),
  region: z.strictObject({ start: seconds, end: seconds, language: z.enum(['ja', 'en']) }).optional(),
  lyrics: z.string().max(100000).optional(),
  eventSensitivity: z.enum(['standard', 'sensitive']).optional(), beatboxRecall: z.boolean().optional(),
});

export const definitions = [
  ['show_in_app', 'Queue a song/time range for display in Music Sweeper. Open the desktop app to receive it. No auto-play. Unsaved GUI edits defer it. Expires after 10 minutes; use get_ui_request to confirm applied status.', { root, start: seconds.optional(), end: seconds.optional(), stem: z.string().optional(), track: track.optional() }, false],
  ['get_ui_request', 'Check whether show_in_app was applied, remains queued, failed or expired.', { requestId: z.string() }, true],
  ['list_projects', 'List saved songs. No audio or complete timeline is returned.', {}, true],
  ['import_audio', 'Copy an allowed local MP3/MP4/M4A/WAV/FLAC into a new project. Source is preserved. No analysis starts.', { source: z.string().min(1) }, false],
  ['get_project', 'Read summary, currentRun, edit revision, track counts and analysis provenance.', { root }, true],
  ['start_analysis', 'Start a durable local analysis job. Poll get_job until terminal. scope=harmony runs BTC chords/key only; vocal-events detects voice events only; vocal-comparison compares AST and YAMNet on original and existing vocal stem without replacing tracks. separation-comparison adds Mel-Band vocals/instrumental from the original and compares AST/YAMNet on all vocal sources. separation-comparison adds Mel-Band vocals/instrumental from the original and compares AST/YAMNet on all vocal sources. Omit scope for full analysis. No network/model downloads.', { root, options }, false],
  ['get_vocal_comparison', 'Read saved AST/YAMNet source-specific voice scores and candidates. Omit variantId for summaries; otherwise read frames or candidates with bounded pagination. Scores are uncalibrated and not comparable probabilities; window ranges are not precise voice boundaries.', {
    root, variantId: z.string().optional(), category: z.enum(['beatbox', 'breath', 'humming']).optional(),
    start: seconds.optional(), end: seconds.optional(), kind: z.enum(['frames', 'candidates']).optional(),
    offset: revision.optional(), limit: z.number().int().min(1).max(500).optional(), expectedRunId: z.string().optional(),
  }, true],
  ['get_job', 'Read job state/progress. complete, partial, failed, cancelled and interrupted are terminal. includeLog returns a bounded diagnostic tail.', { jobId: z.string(), includeLog: z.boolean().optional() }, true],
  ['cancel_job', 'Request cooperative cancellation at the next checkpoint; poll get_job. Completed results are retained.', { jobId: z.string() }, false],
  ['get_timeline', 'Read at most 500 overlapping rows in seconds, with original scores and reviewed flags. Wait for analysis to finish before paging. Use returned revision/runId on subsequent pages and edits. Untimed rows are opt-in.', {
    root, tracks: z.array(track).min(1).optional(), start: seconds.optional(), end: seconds.optional(),
    view: z.enum(['effective', 'automatic', 'manual']).optional(), offset: revision.optional(), limit: z.number().int().min(1).max(500).optional(),
    includeUntimed: z.boolean().optional(), expectedRevision: revision.optional(), expectedRunId: runId.optional(),
  }, true],
  ['update_segments', 'Apply or preview an atomic batch to manual edits; automatic runs and source audio stay intact. Send current revision/runId and a unique requestId; reuse identical args on retry. CONFLICT means reread first. reviewed=true is an explicit review decision, not model confidence.', {
    root, expectedRevision: revision, expectedRunId: runId, requestId: z.string().regex(/^[A-Za-z0-9_-]{1,128}$/), dryRun: z.boolean().optional(),
    operations: z.array(z.strictObject({ op: z.enum(['add', 'update', 'delete']), track, id: z.string().optional(), changes: z.strictObject({
      start: seconds.nullable().optional(), end: seconds.nullable().optional(), label: z.string().optional(), reviewed: z.boolean().optional(),
      language: z.string().max(16).optional(), category: z.enum(['beatbox', 'breath', 'humming', 'other', 'rap', 'spoken']).optional(),
    }).optional() })).min(1).max(100),
  }, false],
  ['extract_audio_clip', 'Create a WAV clip of up to 30 seconds from original or an available separated stem. Returns a registered resource URI; no source file is changed.', { root, start: seconds, end: seconds, stem: z.string().optional() }, false],
  ['export_project', 'Export effective results as JSON, CSV and lyric SRT. Returns registered resource URIs. Untimed lyrics are excluded from SRT.', { root }, false],
];
