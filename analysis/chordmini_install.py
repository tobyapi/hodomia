"""Record a verified, pinned ChordMini installation after online setup."""
import json
import subprocess
import sys
from pathlib import Path
from chordmini import COMMIT, digest


def main(home):
    repo = home / 'repo'
    commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    changes = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain', '--untracked-files=no'], text=True)
    if commit != COMMIT or changes.strip():
        raise ValueError('ChordMini repository must be an unmodified checkout of ' + COMMIT)
    paths = sorted(repo.glob('src/**/*.py')) + [repo / 'config/ChordMini.yaml']
    paths.append(repo / 'checkpoints/btc_model_best.pth')
    data = dict(commit=commit, files={p.relative_to(repo).as_posix(): digest(p) for p in paths})
    (home / 'installation.json').write_text(json.dumps(data, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
