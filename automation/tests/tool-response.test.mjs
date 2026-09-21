import { test } from 'node:test';
import assert from 'node:assert/strict';
import { toolResponse } from '../tool-response.mjs';

test('screenshot is an MCP image without duplicating base64 into JSON', () => {
  const response = toolResponse({ schemaVersion: 1, ok: true, value: { blob: 'cG5n', mimeType: 'image/png', width: 20 } });
  assert.deepEqual(response.content[1], { type: 'image', mimeType: 'image/png', data: 'cG5n' });
  assert.equal(response.structuredContent.value.blob, undefined);
  assert.equal(response.structuredContent.value.width, 20);
  assert.ok(!response.content[0].text.includes('cG5n'));
});

test('errors and artifact links retain their MCP representation', () => {
  const error = { schemaVersion: 1, ok: false, error: { code: 'GUI_TIMEOUT' } };
  assert.deepEqual(toolResponse(error).structuredContent, error);
  assert.equal(toolResponse(error).isError, true);
  const artifact = { uri: 'hodomia://artifact/example', artifactId: 'example', mimeType: 'audio/wav' };
  const result = toolResponse({ ok: true, value: { artifact } });
  assert.equal(result.content[1].type, 'resource_link');
  assert.equal(result.content[1].uri, artifact.uri);
});
