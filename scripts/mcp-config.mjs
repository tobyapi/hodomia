import { configuration, repository } from '../automation/worker-client.mjs';
import path from 'node:path';
const config = configuration();
const args = [path.join(repository, 'automation/mcp-server.mjs'), '--runtime', config.runtime];
for (const key of ['projects', 'registry']) if (config[key]) args.push('--' + key, config[key]);
for (const root of config.allowedRoots) args.push('--allow-root', root);
console.log(JSON.stringify({ mcpServers: { 'hodomia': { command: process.execPath, args } } }, null, 2));
