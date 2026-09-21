// Opt-in real-model check. Creates a new harmony run in each explicitly supplied project.
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import path from 'node:path';
import { repository } from '../automation/worker-client.mjs';

const args = process.argv.slice(2);
const scope = args[0] === '--scope' ? args.splice(0, 2)[1] : 'harmony';
assert.ok(['harmony', 'vocal-comparison'].includes(scope), 'Supported scope: harmony or vocal-comparison');
const roots = args.map(p => path.resolve(p));
if (!roots.length) throw new Error('Pass test project folders; a new BTC harmony run is created in each.');
const read = async file => JSON.parse(await readFile(file, 'utf8'));
const hash = async file => createHash('sha256').update(await readFile(file)).digest('hex');
const client = new Client({ name: 'real-model-verification', version: '1.0.0' });
await client.connect(new StdioClientTransport({ command: process.execPath, args: [
  path.join(repository, 'automation/mcp-server.mjs'), ...roots.flatMap(root => ['--allow-root', root]),
], stderr: 'inherit' }));
const call = async (name, args) => {
  const response = await client.callTool({ name, arguments: args });
  assert.equal(response.isError, false, JSON.stringify(response));
  return response.structuredContent.value;
};
try {
  for (const root of roots) {
    const project = await read(path.join(root, 'project.json'));
    const edits = await read(path.join(root, 'edits.json'));
    const original = await hash(path.join(root, project.source.path));
    const audio = await hash(path.join(root, project.audio));
    const before = await read(path.join(root, 'runs', project.currentRun, 'result.json'));
    const job = await call('start_analysis', { root, options: { mode: 'japanese', scope } });
    console.log(JSON.stringify({ root, jobId: job.jobId, state: job.state }));
    let state;
    const deadline = Date.now() + 600_000;
    do {
      await new Promise(resolve => setTimeout(resolve, 1000));
      state = await call('get_job', { jobId: job.jobId, includeLog: true });
    } while (state.running && Date.now() < deadline);
    assert.equal(state.state, 'complete', JSON.stringify(state));
    const after = await read(path.join(root, 'runs', state.runId, 'result.json'));
    for (const [track, rows] of Object.entries(before.tracks)) {
      if (scope === 'vocal-comparison' || (track !== 'chords' && track !== 'key')) assert.deepEqual(after.tracks[track], rows);
    }
    assert.deepEqual(await read(path.join(root, 'edits.json')), edits);
    assert.equal(await hash(path.join(root, project.source.path)), original);
    assert.equal(await hash(path.join(root, project.audio)), audio);
    if (scope === 'vocal-comparison') {
      assert.deepEqual(after.series, before.series);
      assert.deepEqual(after.stems, before.stems);
      const summary = await call('get_vocal_comparison', { root });
      assert.equal(summary.variants.length, before.stems.vocals ? 4 : 2);
      for (const variant of summary.variants) {
        const page = await call('get_vocal_comparison', { root, variantId: variant.id, start: 0, end: 5, limit: 3, expectedRunId: summary.runId });
        assert.equal(page.rows.length, 3);
      }
      console.log(JSON.stringify({ root, jobId: job.jobId, state: state.state, runId: state.runId,
        variants: summary.variants, originalAndEditsPreserved: true }));
    } else {
      const timeline = await call('get_timeline', { root, tracks: ['chords'], start: 0, end: 5, view: 'automatic' });
      assert.ok(timeline.rows.length > 0);
      assert.equal(after.engines.chords.backend, 'chordmini-btc');
      console.log(JSON.stringify({ root, jobId: job.jobId, state: state.state, runId: state.runId,
        chordCount: after.tracks.chords.length, originalAndEditsPreserved: true }));
    }
  }
} finally { await client.close(); }
