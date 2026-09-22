import { readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { releaseVersion } from './version.mjs';

export function publishRelease(root = process.cwd(), env = process.env, run = execFileSync) {
  const release = releaseVersion(root, env.GITHUB_REF);
  if (env.GITHUB_EVENT_NAME !== 'push' || env.GITHUB_REF !== `refs/tags/${release.tag}`) {
    throw new Error('Publishing requires a matching pushed version tag');
  }
  const assets = readdirSync(path.join(root, 'release-assets')).sort()
    .map((name) => path.join('release-assets', name));
  if (assets.length !== 6 || !assets.includes(path.join('release-assets', 'SHA256SUMS'))) {
    throw new Error('Expected five verified installers and SHA256SUMS');
  }
  const args = ['release', 'create', release.tag, ...assets, '--verify-tag', '--draft',
    '--title', `hodomia ${release.tag}`, '--notes-file', 'docs/release-notes.md'];
  if (release.prerelease) args.push('--prerelease');
  run('gh', args, { cwd: root, stdio: 'inherit' });
  // Publish only after every asset has been uploaded to the draft.
  run('gh', ['release', 'edit', release.tag, '--draft=false'], { cwd: root, stdio: 'inherit' });
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  publishRelease();
}
