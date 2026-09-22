import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, readdir, rename, rm, symlink, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { collectAssets } from './assets.mjs';

const installers = [
  ['windows-x64', 'nsis/hodomia_x64-setup.exe'],
  ['macos-arm64', 'dmg/hodomia_aarch64.dmg'],
  ['macos-x64', 'dmg/hodomia_x64.dmg'],
  ['linux-x64', 'deb/hodomia_amd64.deb'],
  ['linux-x64', 'appimage/hodomia_amd64.AppImage'],
];

async function fixture(t) {
  const home = await mkdtemp(path.join(os.tmpdir(), 'hodomia-release-'));
  t.after(() => rm(home, { recursive: true, force: true }));
  const input = path.join(home, 'downloaded');
  const output = path.join(home, 'release');
  const source = (platform, file = '') => path.join(input, `release-${platform}`, file);
  for (const [platform, file] of installers) {
    await mkdir(path.dirname(source(platform, file)), { recursive: true });
    await writeFile(source(platform, file), 'abc');
  }
  return { home, input, output, source };
}

async function rejectedWithoutOutput(context, expected) {
  await assert.rejects(collectAssets(context.input, context.output), expected);
  await assert.rejects(readdir(context.output), { code: 'ENOENT' });
}

test('collects all platform installers into a flat directory with verified checksums', async t => {
  const context = await fixture(t);
  await collectAssets(context.input, context.output);
  const names = installers.map(([, file]) => path.basename(file)).sort();
  assert.deepEqual((await readdir(context.output)).sort(), ['SHA256SUMS', ...names].sort());
  for (const name of names) assert.equal(await readFile(path.join(context.output, name), 'utf8'), 'abc');
  const digest = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad';
  assert.equal(await readFile(path.join(context.output, 'SHA256SUMS'), 'utf8'),
    names.map(name => `${digest}  ${name}\n`).join(''));
});

test('rejects a missing architecture before copying installers', async t => {
  const context = await fixture(t);
  await rm(context.source('macos-arm64'), { recursive: true });
  await rejectedWithoutOutput(context, /Missing artifact: release-macos-arm64/);
});

test('rejects an unexpected file inside a valid artifact', async t => {
  const context = await fixture(t);
  await writeFile(context.source('linux-x64', 'private.wav'), 'audio');
  await rejectedWithoutOutput(context, /Unexpected release file/);
});

test('rejects an unexpected artifact directory', async t => {
  const context = await fixture(t);
  await mkdir(path.join(context.input, 'quality-reports'));
  await rejectedWithoutOutput(context, /Unexpected artifact/);
});

test('rejects duplicate names across architectures', async t => {
  const context = await fixture(t);
  await rename(context.source('macos-arm64', 'dmg/hodomia_aarch64.dmg'),
    context.source('macos-arm64', 'dmg/hodomia_x64.dmg'));
  await rejectedWithoutOutput(context, /Duplicate release filename/);
});

test('rejects an empty installer', async t => {
  const context = await fixture(t);
  await writeFile(context.source('windows-x64', 'nsis/hodomia_x64-setup.exe'), '');
  await rejectedWithoutOutput(context, /Empty release file/);
});

test('rejects two installers of the same format in one artifact', async t => {
  const context = await fixture(t);
  await writeFile(context.source('windows-x64', 'nsis/extra.exe'), 'extra');
  await rejectedWithoutOutput(context, /Expected one \.exe/);
});

test('rejects missing Linux package formats', async t => {
  const context = await fixture(t);
  await rm(context.source('linux-x64', 'deb/hodomia_amd64.deb'));
  await rejectedWithoutOutput(context, /Expected one \.deb/);
});

test('rejects symlinked artifact trees', async t => {
  const context = await fixture(t);
  const original = context.source('macos-arm64');
  const outside = path.join(context.home, 'outside');
  await rename(original, outside);
  await symlink(outside, original, process.platform === 'win32' ? 'junction' : 'dir');
  await rejectedWithoutOutput(context, /Symbolic links are not allowed/);
});

test('refuses an output directory containing stale assets', async t => {
  const context = await fixture(t);
  await mkdir(context.output);
  await writeFile(path.join(context.output, 'stale.exe'), 'old');
  await assert.rejects(collectAssets(context.input, context.output), /Output directory must be empty/);
  assert.deepEqual(await readdir(context.output), ['stale.exe']);
});
