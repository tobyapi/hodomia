import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const runtimeIndex = args.indexOf('--runtime');
const runtime = runtimeIndex >= 0 ? args[runtimeIndex + 1] : args.find(a => a.startsWith('--runtime='))?.slice(10)
  ?? process.env.HODOMIA_RUNTIME ?? path.join(root, '.runtime');
const python = process.env.HODOMIA_PYTHON ?? path.join(runtime, 'venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const child = spawn(python, [path.join(root, 'analysis/headless.py'), ...args], {
  stdio: 'inherit', windowsHide: true, env: { ...process.env, PYTHONUTF8: '1' },
});
child.on('error', error => { console.error(error.message); process.exitCode = 1; });
child.on('exit', code => { process.exitCode = code ?? 1; });
