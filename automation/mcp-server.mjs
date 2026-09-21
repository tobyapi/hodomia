import { McpServer, ResourceTemplate } from '@modelcontextprotocol/server';
import { StdioServerTransport } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';
import { configuration, workerClient } from './worker-client.mjs';
import { definitions } from './tool-definitions.mjs';

const call = workerClient(configuration());
const server = new McpServer({ name: 'music-sweeper', version: '0.1.0' });
for (const [name, description, shape, readOnly] of definitions) {
  server.registerTool(name, {
    description, inputSchema: z.strictObject(shape),
    annotations: { readOnlyHint: readOnly, destructiveHint: name === 'update_segments', openWorldHint: false },
  }, async args => {
    let response;
    try { response = await call(name, args); }
    catch (error) { response = { schemaVersion: 1, ok: false, error: { code: 'BRIDGE_ERROR', message: error.message } }; }
    const artifacts = response.ok ? response.value.artifacts ?? (response.value.artifact ? [response.value.artifact] : []) : [];
    return {
      isError: !response.ok, structuredContent: response,
      content: [{ type: 'text', text: JSON.stringify(response) }, ...artifacts.map(item => ({
        type: 'resource_link', uri: item.uri, name: item.artifactId, mimeType: item.mimeType,
      }))],
    };
  });
}
server.registerResource('artifact', new ResourceTemplate('music-sweeper://artifact/{artifactId}', { list: undefined }),
  { description: 'Generated clips and exports only. Local file paths cannot be read through this resource.' }, async (_uri, { artifactId }) => {
    const response = await call('read_artifact', { artifactId });
    if (!response.ok) throw new Error(`${response.error.code}: ${response.error.message}`);
    return { contents: [response.value] };
  });
await server.connect(new StdioServerTransport());
