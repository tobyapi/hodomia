import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { repository } from '../worker-client.mjs';

test('real stdio MCP: import, bounded reads, CAS edits, clips, exports and permission errors', { timeout: 60_000 }, async () => {
  const folder = await mkdtemp(path.join(os.tmpdir(), 'hodomia-mcp-'));
  const wav = Buffer.alloc(44 + 32000);
  wav.write('RIFF'); wav.writeUInt32LE(wav.length - 8, 4); wav.write('WAVEfmt ', 8);
  wav.writeUInt32LE(16, 16); wav.writeUInt16LE(1, 20); wav.writeUInt16LE(1, 22);
  wav.writeUInt32LE(16000, 24); wav.writeUInt32LE(32000, 28); wav.writeUInt16LE(2, 32); wav.writeUInt16LE(16, 34);
  wav.write('data', 36); wav.writeUInt32LE(32000, 40);
  const source = path.join(folder, 'input.wav'); await writeFile(source, wav);
  const transport = new StdioClientTransport({ command: process.execPath, args: [path.join(repository, 'automation/mcp-server.mjs'),
    '--runtime', path.join(folder, 'runtime'), '--projects', path.join(folder, 'projects'),
    '--registry', path.join(folder, 'registry'), '--allow-root', folder], stderr: 'pipe',
    env: { ...process.env, HODOMIA_PYTHON: process.env.HODOMIA_PYTHON ?? path.join(repository, '.runtime/venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python') } });
  const client = new Client({ name: 'integration-test', version: '1.0.0' });
  try {
    await client.connect(transport);
    assert.ok((await client.listTools()).tools.some(t => t.name === 'update_segments'));
    const unavailable = await client.callTool({ name: 'capture_app', arguments: { timeoutSeconds: 1 } });
    assert.equal(unavailable.isError, true);
    assert.equal(unavailable.structuredContent.error.code, 'GUI_TIMEOUT');
    const call = async (name, args = {}) => {
      const result = await client.callTool({ name, arguments: args });
      assert.equal(result.isError, false, JSON.stringify(result));
      return result.structuredContent.value;
    };
    const imported = await call('import_audio', { source });
    const root = imported.root;
    assert.equal((await call('list_projects')).projects.length, 1);
    assert.equal((await call('get_project', { root })).revision, 0);
    const display = await call('show_in_app', { root, start: 0.1, end: 0.4, track: 'lyrics' });
    assert.equal((await call('get_ui_request', { requestId: display.requestId })).state, 'queued');
    const request = { root, expectedRevision: 0, expectedRunId: null, requestId: 'mcp-edit',
      operations: [{ op: 'add', track: 'lyrics', changes: { start: 0.1, end: 0.8, label: 'テスト', reviewed: true } }] };
    const result = await call('update_segments', request);
    assert.equal(result.revision, 1);
    assert.equal((await call('update_segments', request)).replayed, true);
    const rows = await call('get_timeline', { root, start: 0, end: 1, tracks: ['lyrics'], limit: 1 });
    assert.equal(rows.rows[0].label, 'テスト');
    const stale = await client.callTool({ name: 'update_segments', arguments: { ...request, requestId: 'stale' } });
    assert.equal(stale.isError, true); assert.equal(stale.structuredContent.error.code, 'CONFLICT');
    const clip = await call('extract_audio_clip', { root, start: 0.1, end: 0.3 });
    const audio = await client.readResource({ uri: clip.artifact.uri });
    assert.equal(Buffer.from(audio.contents[0].blob, 'base64').toString('ascii', 0, 4), 'RIFF');
    const exported = await call('export_project', { root });
    assert.equal(exported.artifacts.length, 3);
    const csv = await client.readResource({ uri: exported.artifacts.find(a => a.mimeType === 'text/csv').uri });
    assert.match(csv.contents[0].text, /テスト/);
    const denied = await client.callTool({ name: 'get_project', arguments: { root: path.dirname(folder) } });
    assert.equal(denied.structuredContent.error.code, 'ACCESS_DENIED');
    const invalid = await client.callTool({ name: 'get_timeline', arguments: { root, limit: 501 } });
    assert.equal(invalid.isError, true);
  } finally {
    await client.close();
    await rm(folder, { recursive: true, force: true });
  }
});
