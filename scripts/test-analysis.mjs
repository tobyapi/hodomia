import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
const local = process.platform === 'win32' ? '.runtime/venv/Scripts/python.exe' : '.runtime/venv/bin/python';
const python = process.env.HODOMIA_PYTHON || (existsSync(local) ? local : 'python');
// The separation comparison tests need only numpy and soundfile, like the analysis tests.
let status = 0;
for (const folder of ['analysis/tests', 'scripts/separation/tests']) {
  const result = spawnSync(python, ['-m', 'unittest', 'discover', '-s', folder, '-v'], {
    stdio: 'inherit', env: { ...process.env, PYTHONUTF8: '1' }, windowsHide: true,
  });
  if (result.error) console.error(result.error.message);
  status ||= result.status ?? 1;
}
process.exit(status);
