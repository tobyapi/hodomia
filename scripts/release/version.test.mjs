import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { releaseVersion } from './version.mjs';

function fixture(t, version = '1.2.3') {
  const root = mkdtempSync(path.join(tmpdir(), 'hodomia-release-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  mkdirSync(path.join(root, 'src-tauri'));
  const write = (name, text) => writeFileSync(path.join(root, name), text);
  write('package.json', JSON.stringify({ version }));
  write('package-lock.json', JSON.stringify({ version, packages: { '': { version } } }));
  write('src-tauri/tauri.conf.json', JSON.stringify({ version }));
  write('src-tauri/Cargo.toml', `[package]\nname = "hodomia"\nversion = "${version}"\n[lib]\n`);
  write('src-tauri/Cargo.lock', `[[package]]\nname = "hodomia"\nversion = "${version}"\n[[package]]\nname = "other"\nversion = "9.9.9"\n`);
  return { root, write };
}

test('release tags match all package versions', (t) => {
  const { root } = fixture(t);
  assert.deepEqual(releaseVersion(root, 'refs/tags/v1.2.3'), {
    version: '1.2.3', tag: 'v1.2.3', prerelease: false,
  });
  assert.throws(() => releaseVersion(root, 'refs/tags/v9.9.9'), /must match/);
});

test('manual branch builds accept prerelease versions', (t) => {
  const { root } = fixture(t, '1.2.3-beta.1');
  assert.equal(releaseVersion(root, 'refs/heads/main').prerelease, true);
});

test('stale native or npm lock versions block release', (t) => {
  const { root, write } = fixture(t);
  write('src-tauri/Cargo.lock', '[[package]]\nname = "hodomia"\nversion = "1.2.2"\n');
  assert.throws(() => releaseVersion(root), /Cargo.lock/);
  write('package-lock.json', JSON.stringify({ version: '1.2.2', packages: { '': { version: '1.2.2' } } }));
  assert.throws(() => releaseVersion(root), /package-lock.json/);
});

test('invalid versions cannot enter release command arguments', (t) => {
  const { root } = fixture(t, '1.2.3\nmalformed');
  assert.throws(() => releaseVersion(root), /Unsupported/);
});
