import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

export const repository = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export function configuration(args = process.argv.slice(2)) {
  const values = { runtime: process.env.MUSIC_SWEEPER_RUNTIME ?? path.join(repository, '.runtime'), allowedRoots: [] };
  const flags = { '--runtime': 'runtime', '--projects': 'projects', '--registry': 'registry', '--allow-root': 'allowedRoots' };
  for (let i = 0; i < args.length; i += 2) {
    const key = flags[args[i]];
    if (!key || !args[i + 1] || args[i + 1].startsWith('--')) throw new Error('Unknown or incomplete option: ' + args[i]);
    if (key === 'allowedRoots') values.allowedRoots.push(path.resolve(args[i + 1]));
    else values[key] = path.resolve(args[i + 1]);
  }
  return values;
}

export function workerClient(config) {
  const python = process.env.MUSIC_SWEEPER_PYTHON ?? path.join(config.runtime, 'venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
  const flags = ['--runtime', config.runtime];
  for (const key of ['projects', 'registry']) if (config[key]) flags.push('--' + key, config[key]);
  for (const root of config.allowedRoots) flags.push('--allow-root', root);
  return (operation, args = {}) => new Promise((resolve, reject) => {
    const child = spawn(python, [path.join(repository, 'analysis/headless.py'), ...flags], {
      windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'], env: { ...process.env, PYTHONUTF8: '1' },
    });
    let output = '', diagnostic = '', size = 0;
    const timer = setTimeout(() => { child.kill(); reject(new Error('Headless operation timed out')); }, 120_000);
    child.stdout.setEncoding('utf8'); child.stderr.setEncoding('utf8');
    child.stdout.on('data', data => {
      size += Buffer.byteLength(data);
      if (size > 24 * 1024 * 1024) { child.kill(); reject(new Error('Headless response exceeds limit')); }
      else output += data;
    });
    child.stderr.on('data', data => { diagnostic = (diagnostic + data).slice(-3000); });
    child.on('error', error => { clearTimeout(timer); reject(error); });
    child.stdin.on('error', () => {}); // Spawn failure is reported by the child error event.
    child.on('close', code => {
      clearTimeout(timer);
      try {
        const response = JSON.parse(output);
        if (response.schemaVersion !== 1 || typeof response.ok !== 'boolean') throw new Error('Invalid headless response');
        if (code !== 0 && response.ok) throw new Error('Worker exited unsuccessfully');
        resolve(response);
      } catch (error) { reject(new Error(`${error.message}: ${diagnostic}`)); }
    });
    child.stdin.end(JSON.stringify({ operation, args }));
  });
}
