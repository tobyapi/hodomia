import { readFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const versionPattern = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([a-zA-Z0-9]+(?:[.-][a-zA-Z0-9]+)*))?$/;

function tomlVersion(text, heading) {
  const section = text.split(heading)[1]?.split(/\r?\n\[/)[0];
  return section?.match(/^version\s*=\s*"([^"]+)"/m)?.[1];
}

export function releaseVersion(root, ref = '') {
  const read = (name) => readFileSync(path.join(root, name), 'utf8');
  const pkg = JSON.parse(read('package.json'));
  const lock = JSON.parse(read('package-lock.json'));
  const versions = {
    'package.json': pkg.version,
    'package-lock.json': lock.version,
    'package-lock.json root': lock.packages[''].version,
    'tauri.conf.json': JSON.parse(read('src-tauri/tauri.conf.json')).version,
    'Cargo.toml': tomlVersion(read('src-tauri/Cargo.toml'), '[package]'),
    'Cargo.lock': tomlVersion(read('src-tauri/Cargo.lock'), 'name = "hodomia"'),
  };
  if (!versionPattern.test(pkg.version)) throw new Error(`Unsupported release version: ${pkg.version}`);
  for (const [file, version] of Object.entries(versions)) {
    if (version !== pkg.version) throw new Error(`${file} version ${version} differs from ${pkg.version}`);
  }
  const tag = `v${pkg.version}`;
  if (ref.startsWith('refs/tags/') && ref !== `refs/tags/${tag}`) {
    throw new Error(`Tag ${ref} must match ${tag}`);
  }
  return { version: pkg.version, tag, prerelease: pkg.version.includes('-') };
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  console.log(JSON.stringify(releaseVersion(process.cwd(), process.env.GITHUB_REF)));
}
