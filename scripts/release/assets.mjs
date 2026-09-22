import { createHash } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { copyFile, lstat, mkdir, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const formats = new Map([
  ['release-windows-x64', ['.exe']],
  ['release-macos-arm64', ['.dmg']],
  ['release-macos-x64', ['.dmg']],
  ['release-linux-x64', ['.deb', '.AppImage']],
]);

async function filesIn(folder) {
  const status = await lstat(folder);
  if (status.isSymbolicLink()) throw new Error(`Symbolic links are not allowed: ${folder}`);
  if (!status.isDirectory()) throw new Error(`Expected artifact directory: ${folder}`);
  const files = [];
  for (const entry of await readdir(folder, { withFileTypes: true })) {
    const location = path.join(folder, entry.name);
    if (entry.isSymbolicLink()) throw new Error(`Symbolic links are not allowed: ${location}`);
    if (entry.isDirectory()) files.push(...await filesIn(location));
    else if (entry.isFile()) files.push(location);
    else throw new Error(`Unexpected release file: ${location}`);
  }
  return files;
}

async function artifactFiles(input) {
  const root = await lstat(input);
  if (root.isSymbolicLink()) throw new Error(`Symbolic links are not allowed: ${input}`);
  const entries = await readdir(input);
  for (const name of entries) {
    if (!formats.has(name)) throw new Error(`Unexpected artifact: ${name}`);
  }
  const files = [];
  for (const [name, extensions] of formats) {
    if (!entries.includes(name)) throw new Error(`Missing artifact: ${name}`);
    const candidates = await filesIn(path.join(input, name));
    for (const file of candidates) {
      if (!extensions.includes(path.extname(file))) throw new Error(`Unexpected release file: ${file}`);
    }
    for (const extension of extensions) {
      if (candidates.filter(file => path.extname(file) === extension).length !== 1) {
        throw new Error(`Expected one ${extension} installer in ${name}`);
      }
    }
    files.push(...candidates);
  }
  return files;
}

async function validatedAssets(input) {
  const assets = new Map();
  const filenames = new Set();
  for (const file of await artifactFiles(input)) {
    const name = path.basename(file);
    if (/[\r\n\\]/.test(name)) throw new Error(`Invalid release filename: ${name}`);
    if (filenames.has(name.toLowerCase())) throw new Error(`Duplicate release filename: ${name}`);
    if ((await lstat(file)).size === 0) throw new Error(`Empty release file: ${file}`);
    filenames.add(name.toLowerCase());
    const hash = createHash('sha256');
    for await (const chunk of createReadStream(file)) hash.update(chunk);
    assets.set(name, { file, checksum: hash.digest('hex') });
  }
  return assets;
}

async function assertEmptyOutput(output) {
  try {
    const status = await lstat(output);
    if (status.isSymbolicLink()) throw new Error(`Symbolic links are not allowed: ${output}`);
    if (!status.isDirectory() || (await readdir(output)).length !== 0) {
      throw new Error(`Output directory must be empty: ${output}`);
    }
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
}

export async function collectAssets(downloadRoot, outputRoot) {
  const input = path.resolve(downloadRoot);
  const output = path.resolve(outputRoot);
  const assets = await validatedAssets(input);
  await assertEmptyOutput(output);
  await mkdir(output, { recursive: true });
  const names = [...assets.keys()].sort();
  const checksums = [];
  for (const name of names) {
    const asset = assets.get(name);
    await copyFile(asset.file, path.join(output, name));
    checksums.push(`${asset.checksum}  ${name}\n`);
  }
  await writeFile(path.join(output, 'SHA256SUMS'), checksums.join(''), 'utf8');
  return names;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  collectAssets(process.argv[2] ?? 'downloaded-artifacts', process.argv[3] ?? 'release-assets')
    .then(names => console.log(`Prepared ${names.length} installers and SHA256SUMS.`))
    .catch(error => { console.error(error.message); process.exitCode = 1; });
}
