import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
const local = process.platform === 'win32' ? '.runtime/venv/Scripts/python.exe' : '.runtime/venv/bin/python';
const python = process.env.MUSIC_SWEEPER_PYTHON || (existsSync(local) ? local : 'python');
const result = spawnSync(python, ['-m', 'unittest', 'discover', '-s', 'analysis/tests', '-v'], {
  stdio: 'inherit', env: { ...process.env, PYTHONUTF8: '1' }, windowsHide: true,
});
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);
