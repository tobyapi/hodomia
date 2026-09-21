# hodomia

Tauri 2 + React 19 のローカル音楽解析アプリ。MP3 / MP4 / M4A / WAV / FLAC を1曲ずつ読み込み、拍、曲構成、歌詞、コード、音高を同じ時間軸で確認・修正できます。1曲15分まで。MP4は最初の音声トラックを使います。

## ドキュメント

- [使い方](docs/usage.md)：曲の読み込み、解析、再生、テーマ切り替え、編集、保存・削除、推定の限界
- [出力JSONとプロジェクト形式](docs/json-format.md)：保存構成、フィールド、単位、具体例
- [CLI・MCPによる自動操作](docs/automation.md)
- [品質ゲート](docs/quality-gate.md) / [構成](.clean/architecture.md) / [検証記録](docs/verification.md)

初回セットアップ後の解析はローカルで実行します。自動推定には誤りや未確定の情報が含まれるため、試聴して確認・修正してください。

## 画面

公開用デモデータをブラウザーハーネスで表示した画面です。実曲の解析結果ではありません。[ライトモードと画面の説明](docs/usage.md#画面の見方)も掲載しています。

![ダークモードの解析画面](docs/images/dark-mode.jpg)

## MCPとヘッドレスモード

GUIに加えて、**MCPサーバーとヘッドレスCLI**を利用できます。AIクライアントやスクリプトから、保存曲の取得、非同期解析、区間検索・編集、音声クリップの切り出し、JSON/CSV/SRTの書き出しを操作できます。解析環境とプロジェクト形式はGUIと共通です。

- **ヘッドレスCLI**：GUIを開かずに操作し、結果をJSONで受け取ります。例：`node scripts/headless.mjs list_projects`。
- **MCP**：`node automation/mcp-server.mjs`で標準入出力のサーバーを起動します。クライアント用の接続設定は`node scripts/mcp-config.mjs`で生成できます。
- **スクリーンショット**：`capture_app`で起動中のWindowsアプリをPNG撮影できます。MCPには画像として、CLIには保存先とbase64を返します。[撮影方法](docs/automation.md#アプリのスクリーンショット)を参照してください。

初回の解析環境セットアップは必要です。GUIで開始した解析もアプリ終了後に継続するため、中止にはキャンセル操作を使ってください。許可フォルダーの指定、接続設定、各操作の引数は[CLI・MCPによる自動操作](docs/automation.md)を参照してください。

## 開発環境の準備

Node.js 22以上、Rust stable MSVC、Visual Studio C++ Build Tools / Windows SDK、WebView2、[uv](https://docs.astral.sh/uv/getting-started/installation/) が必要です。解析環境はPython3.11、CUDA12.8対応PyTorch。NVIDIA GPUがない場合はCPUを使用し、時間がかかります。8GB GPUでモデルを順次読み込む構成です。

```powershell
npm ci
npm run doctor
npm run setup:analysis
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
改善後は `npm run quality:prune` で許容値を縮めて一緒にコミットします。基準と操作は [品質ゲート](docs/quality-gate.md)。
ソース（テスト・スクリプトを含む）の150行超は警告です。空行・コメントも行数に含めます。
厳格に失敗させたい場合は `npm run check:quality -- --strict-length` を使います。
既存の長いファイルも警告し、例外リストで隠しません。生成物・依存・モデル・音源は対象外です。
依存境界違反とReactソースの循環依存はコミット／CIを失敗させます。詳細は `.clean/architecture.md`。
凝集度の意味的な良し悪しを自動判定するものではなく、責務の混在を検知する補助です。

| コマンド | 内容 |
| --- | --- |
| `npm run analyze` | 複雑度・MI・依存関係・Rust Clippy。JSONレポートを出力 |
| `npm run check` | UI・編集、Python保存/DSP、型検査、ビルド、Rustテスト/Clippy |
| `npm run tauri:build -- --no-bundle` | Windows実行ファイルの生成 |
| `npm run tauri:build` | NSISインストーラーの生成 |
| `npm run dev` | localhost:1430のブラウザープレビュー |
| `npm run harness:prepare -- "プロジェクトのパス"` | 実データのブラウザー表示用コピーを作成 |

ハーネスは開発サーバーの `/tests/ui/`。修正保存はメモリー内のみで、解析・外部書き出しは行いません。本番ビルドには入りません。実曲・モデル・ハーネス用データはGit対象外です。CIは合成音と軽量依存で実行し、GPUモデルやユーザー音源を取得しません。

`analysis/requirements.txt` は主要依存、`analysis/requirements.lock.txt` は検証した全依存です。インストール時にはlockを使います。React→`src/api.ts`→Rust→`analysis/cli.py`の順に処理を呼び出します。詳細は `.clean/architecture.md` と `docs/verification.md`。

解析エンジン: Demucs htdemucs_ft、Beat This final0、All-In-One harmonix-all、faster-whisper large-v3、WhisperX、librosa。各モデル・依存のライセンスは配布元に従います。

## 改名後の保存データ

アプリIDは app.hodomia.desktop、保存先はドキュメント内の hodomia/Projects です。以前の保存データは自動移行しません。引き継ぐ場合はバックアップを取り、project.json の kind を hodomia に変更して、新しい保存先にコピーしてください。テーマと音量設定は新しい設定キーで保存します。
