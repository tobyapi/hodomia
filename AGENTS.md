# 開発手順
- このプロジェクトは Tauri 2 + React 19 + TypeScript。
- 作業前に README.md と .clean/architecture.md を読む。
- コードの作成・変更・レビュー・テスト・リファクタリングでは `.agents/skills/clean-code/SKILL.md` と必要な参照資料を読む。このプロジェクトの開発手順と品質ゲートを優先する。
- UI は src/、Tauri 呼び出しは src/api.ts、Rust は src-tauri/src/、解析ワーカーは analysis/ に置く。
- ブラウザーのプレビューと実際の Tauri IPC を区別する。テストのモックを製品コードに入れない。
- 変更後は npm run check。ネイティブ設定を変えた場合は npm run tauri:build -- --no-bundle も実行する。
- 1ファイル150行を目安に、責務単位で構成する。check:qualityは行数超過を警告し依存境界違反をエラーにする。pre-commitはステージ済み内容を検査する。警告回避のために行を圧縮しない。
- 複雑度・MIの新規違反と悪化は禁止。既存違反は .clean/quality-baseline.json に記録する。改善時は npm run quality:prune で記録を縮める。基準を緩めたり記録を増やしたりして回避しない。詳細は docs/quality-gate.md。
- 1曲・15分以内のローカル解析。日本語歌唱、多言語、インストに対応する。Audio2Face/OSC 機能は対象外。
- 解析中はネット接続しない。モデル取得は初回セットアップだけ。モデル・音源・実曲テスト結果をGitに追加しない。
- runs/ の自動結果と edits.json の手修正を分離する。未確定時刻は null、未確認の自動推定は reviewed=false とする。

## 文章の執筆・編集
- 日本語の説明、UI文言、ドキュメントを書く際は `.agents/skills/stop-ai-slop-jp/SKILL.md` と必要な参照資料を読む。
- 英語の文章には `.agents/skills/stop-slop/SKILL.md` を使う。言語が混在する場合は該当部分ごとに適用する。
- 意味、技術的な正確さ、引用原文を優先し、文体を整えるために事実や体験を作らない。
- スキルはリポジトリに同梱している。取得元・固定コミット・更新方法は `docs/bundled-skills.md`。
