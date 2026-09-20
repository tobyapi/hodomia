# Music Sweeper

<参照プロジェクト> の構成を参考にした Tauri 2 + React 19 + TypeScript の開発基盤です。現在は実行環境を確認する最小画面のみで、音楽処理機能は未実装です。

## セットアップ（Windows）

Node.js 22 LTS 以上、Rust stable（MSVC）、Visual Studio の C++ Build Tools と Windows SDK、WebView2 Runtime が必要です。

```powershell
# クローンしたリポジトリのルートで実行
npm ci
npm run doctor
npm run tauri:dev
```

`npm run doctor` はツールのバージョンと Tauri の環境診断を出力します。不足するシステム依存は診断結果を確認してください。

## 開発と検証

| コマンド | 内容 |
| --- | --- |
| `npm run dev` | ブラウザープレビュー（http://127.0.0.1:1430） |
| `npm run tauri:dev` | Rust バックエンドを含むデスクトップ起動 |
| `npm test` | Vitest / Testing Library の UI・IPC モックテスト |
| `npm run test:watch` | テストを監視実行 |
| `npm run build` | TypeScript 型検査と Vite ビルド |
| `npm run check` | UI テスト、ビルド、Rust 書式・テスト・Clippy |
| `npm run tauri:build -- --no-bundle` | Windows 実行ファイルをビルド |
| `npm run tauri:build` | NSIS インストーラーを生成 |

ハーネスは UI の正常応答・失敗表示・ブラウザープレビュー、Rust のレスポンス契約を検証します。UI テストは [Tauri 公式 mockIPC](https://v2.tauri.app/develop/tests/mocking/) を使用します。実際の WebView2 を操作する E2E テストではありません。ネイティブ動作はデスクトップの「接続確認」で `Music Sweeper / 0.1.0 / Tauri` が出ることを確認してください。

## 構成

- `src/App.tsx`: 最小 UI
- `src/runtime.ts`: Tauri IPC とブラウザープレビューの境界
- `src/test/`: テスト初期化と後片付け
- `src-tauri/src/`: Rust コマンドとアプリ起動
- `scripts/doctor.mjs`: 環境診断
- `.github/workflows/check.yml`: Windows 上の検証とネイティブビルド
- `AGENTS.md` / `.clean/`: 次回開発用の手順と構成記録

Tauri・React・Vite は参照元と同じメジャー世代を使い、Vitest は脆弱性修正済みの 4 に更新しています。解決したバージョンは package-lock.json と src-tauri/Cargo.lock に固定します。参照元専用の CUDA・Audio2Face・OSC 依存は含みません。アイコンは app-icon.svg から `npm run tauri -- icon app-icon.svg` で再生成できます。
