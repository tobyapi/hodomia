#!/bin/sh
set -eu

# Apps launched from Finder do not inherit the user's shell startup PATH.
PATH="${HOME}/.local/bin:${HOME}/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"
export PATH

if ! command -v uv >/dev/null 2>&1; then
  echo 'uv が見つかりません。uv をインストールしてからセットアップを再実行してください。' >&2
  exit 1
fi
if ! command -v git >/dev/null 2>&1; then
  echo 'Git が見つかりません。Git をインストールしてからセットアップを再実行してください。' >&2
  exit 1
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python=$(uv python find --managed-python 3.11)
exec "$python" "$script_dir/../analysis/setup_macos.py" "$@"
