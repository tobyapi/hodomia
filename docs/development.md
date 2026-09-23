# 開発環境と検証

[READMEへ戻る](../README.md) · [開発ルール](../AGENTS.md) · [同梱スキル](bundled-skills.md)

OS別の配布ビルドとGitHub Releasesへの公開は[リリース手順](releases.md)を参照してください。

Tauri 2 + React 19 + TypeScriptのデスクトップアプリです。コーディングエージェントはAGENTS.mdと同梱スキルを読み、この手順で環境を準備してください。

## 開発環境の準備

Windowsでの開発にはNode.js 22以上、Rust stable MSVC、Visual Studio C++ Build Tools / Windows SDK、WebView2、[uv](https://docs.astral.sh/uv/getting-started/installation/) が必要です。解析環境はPython3.11、CUDA12.8対応PyTorch。NVIDIA GPUがない場合はCPUを使用し、時間がかかります。8GB GPUでモデルを順次読み込む構成です。

```powershell
npm ci
npm run doctor
npm run setup:analysis
npm run tauri:dev
```

Apple Silicon搭載MacではNode.js 22以上、Rust stable、Xcode Command Line Tools、uv、Gitを用意します。アプリ内の「初回セットアップ」は `scripts/setup-macos.sh` を呼び、Python 3.11、解析依存、モデルをアプリデータ内に準備します。MacではCPUで推論します。開発時に同じセットアップを行う場合は次を実行します。

```sh
npm ci
sh scripts/setup-macos.sh .runtime full
npm run tauri:dev
```

初回セットアップのみモデルをオンライン取得します。音源・歌詞は送信しません。パッケージとモデルのために数十GBの空き容量を用意してください。アプリ内の「初回セットアップ」「環境を再確認・修復」でも同じ処理を実行できます。解析中はPythonのネット接続を禁止し、キャッシュ不足は明示的な失敗になります。

開発時は `.runtime/`、この開発フォルダーがないインストール先ではアプリデータ内の `runtime/` を使います。`HODOMIA_RUNTIME` で保存先を指定できます。モデルはインストーラーに含めません。

## 検証と開発ハーネス

`npm ci` / `npm install` でGitのpre-commitフックを導入します。このチェックアウトで再設定する場合は `npm run hooks:install`。
フックはステージ済みのソース全体、`npm run check:quality` とCIは作業ツリーを検査します。
`npm run setup:quality` で固定版のRust解析ツールを導入します（初回はネット接続が必要）。
pre-commitは複雑度・MIも検査し、pre-pushは `npm run analyze` で全解析を実行します。
既存違反は `.clean/quality-baseline.json` に記録し、新規違反・悪化を禁止します。
改善後は `npm run quality:prune` で許容値を縮めて一緒にコミットします。基準と操作は [品質ゲート](quality-gate.md)。
ソース（テスト・スクリプトを含む）の150行超は警告です。空行・コメントも行数に含めます。
厳格に失敗させたい場合は `npm run check:quality -- --strict-length` を使います。
既存の長いファイルも警告し、例外リストで隠しません。生成物・依存・モデル・音源は対象外です。
依存境界違反とReactソースの循環依存はコミット／CIを失敗させます。詳細は [構成](../.clean/architecture.md)。
凝集度の意味的な良し悪しを自動判定するものではなく、責務の混在を検知する補助です。

| コマンド | 内容 |
| --- | --- |
| `npm run analyze` | 複雑度・MI・依存関係・Rust Clippy。JSONレポートを出力 |
| `npm run check` | UI・編集、Python保存/DSP、型検査、ビルド、Rustテスト/Clippy |
| `npm run tauri:build -- --no-bundle` | 現在のOSの実行ファイルを生成 |
| `npm run tauri:build` | NSISインストーラーの生成 |
| `npm run dev` | localhost:1430のブラウザープレビュー |
| `npm run harness:prepare -- "プロジェクトのパス"` | 実データのブラウザー表示用コピーを作成 |

ハーネスは開発サーバーの `/tests/ui/`。修正保存はメモリー内のみで、解析・外部書き出しは行いません。本番ビルドには入りません。実曲・モデル・ハーネス用データはGit対象外です。CIは合成音と軽量依存で実行し、GPUモデルやユーザー音源を取得しません。

`analysis/requirements.txt` は主要依存、`analysis/requirements.lock.txt` はWindows向け、`analysis/requirements.macos-arm64.lock.txt` はApple Silicon向けの固定依存です。React→`src/api.ts`→Rust→`analysis/cli.py`の順に処理を呼び出します。詳細は [構成](../.clean/architecture.md) と [検証記録](verification.md)。

解析エンジン: Demucs htdemucs_ft、Beat This final0、All-In-One harmonix-all、faster-whisper large-v3、WhisperX、librosa。各モデル・依存のライセンスは配布元に従います。
