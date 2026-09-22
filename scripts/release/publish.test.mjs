import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { publishRelease } from './publish.mjs';

function fixture(t, version = '1.2.3') {
  const root = mkdtempSync(path.join(os.tmpdir(), 'hodomia-publish-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const folder of ['src-tauri', 'docs', 'release-assets']) mkdirSync(path.join(root, folder));
  const write = (name, text) => writeFileSync(path.join(root, name), text);
  write('package.json', JSON.stringify({ version }));
  write('package-lock.json', JSON.stringify({ version, packages: { '': { version } } }));
  write('src-tauri/tauri.conf.json', JSON.stringify({ version }));
  write('src-tauri/Cargo.toml', `[package]\nname = "hodomia"\nversion = "${version}"\n`);
  write('src-tauri/Cargo.lock', `[[package]]\nname = "hodomia"\nversion = "${version}"\n`);
  write('docs/release-notes.md', 'Release fixture.');
  for (const file of ['windows.exe', 'arm64.dmg', 'x64.dmg', 'linux.deb', 'linux.AppImage', 'SHA256SUMS']) {
    write(`release-assets/${file}`, 'fixture');
  }
  const env = { GITHUB_EVENT_NAME: 'push', GITHUB_REF: `refs/tags/v${version}` };
  const calls = [];
  const run = (command, args, options) => calls.push({ command, args, options });
  return { root, env, calls, run };
}

test('publishes a complete draft only after create and upload succeed', t => {
  const { root, env, calls, run } = fixture(t);
  publishRelease(root, env, run);
  assert.equal(calls.length, 2);
  const [create, publish] = calls;
  assert.equal(create.command, 'gh');
  assert.deepEqual(create.args.slice(0, 3), ['release', 'create', 'v1.2.3']);
  assert.deepEqual(create.args.slice(3, 9).sort(),
    ['SHA256SUMS', 'arm64.dmg', 'linux.AppImage', 'linux.deb', 'windows.exe', 'x64.dmg']
      .map(name => path.join('release-assets', name)).sort());
  assert.deepEqual(create.args.slice(9), ['--verify-tag', '--draft', '--title', 'hodomia v1.2.3',
    '--notes-file', 'docs/release-notes.md']);
  assert.deepEqual(create.options, { cwd: root, stdio: 'inherit' });
  assert.deepEqual(publish, { command: 'gh', args: ['release', 'edit', 'v1.2.3', '--draft=false'],
    options: { cwd: root, stdio: 'inherit' } });
});

test('manual runs cannot create a release even when their tag matches', t => {
  const { root, env, calls, run } = fixture(t);
  env.GITHUB_EVENT_NAME = 'workflow_dispatch';
  assert.throws(() => publishRelease(root, env, run), /Publishing requires a matching pushed version tag/);
  assert.deepEqual(calls, []);
});

test('mismatched tags cannot invoke GitHub', t => {
  const { root, env, calls, run } = fixture(t);
  env.GITHUB_REF = 'refs/tags/v9.9.9';
  assert.throws(() => publishRelease(root, env, run), /must match/);
  assert.deepEqual(calls, []);
});

test('branch pushes cannot publish a release', t => {
  const { root, env, calls, run } = fixture(t);
  env.GITHUB_REF = 'refs/heads/main';
  assert.throws(() => publishRelease(root, env, run), /Publishing requires/);
  assert.deepEqual(calls, []);
});

for (const reason of ['upload failed', 'release already exists']) {
  test(`does not make a release public when gh reports ${reason}`, t => {
    const { root, env, calls, run } = fixture(t);
    const failure = new Error(reason);
    const failCreate = (...args) => { run(...args); throw failure; };
    assert.throws(() => publishRelease(root, env, failCreate), error => error === failure);
    assert.equal(calls.length, 1);
    assert.deepEqual(calls[0].args.slice(0, 3), ['release', 'create', 'v1.2.3']);
  });
}

test('missing assets prevent creation of a draft', t => {
  const { root, env, calls, run } = fixture(t);
  rmSync(path.join(root, 'release-assets', 'linux.deb'));
  assert.throws(() => publishRelease(root, env, run), /Expected five verified installers/);
  assert.deepEqual(calls, []);
});

test('prerelease versions create a prerelease draft', t => {
  const { root, env, calls, run } = fixture(t, '1.2.3-beta.1');
  publishRelease(root, env, run);
  assert.ok(calls[0].args.includes('--prerelease'));
  assert.deepEqual(calls[1].args, ['release', 'edit', 'v1.2.3-beta.1', '--draft=false']);
});
