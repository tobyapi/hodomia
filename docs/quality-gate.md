# 品質ゲート

Music Sweeperの品質基準を定める。凝集度の点数そのものではなく、
複雑度、保守容易性、依存方向を組み合わせて責務の混在を見つける。

| 指標 | TypeScript / React | Rust |
| --- | --- | --- |
| ファイル行数 | 150行を目安に警告 | 150行を目安に警告 |
| 関数行数 | 空行・コメントを除き50行 | sloc 80行 |
| 認知的複雑度 | 10以下 | 15以下 |
| 循環的複雑度 | 10以下 | 10以下 |
| ネスト | 3以下 | 個別上限なし |
| 文の数 | 20以下 | 個別上限なし |
| 引数 / 終了点 | 個別上限なし | 各5以下 |
| 保守容易性指数（MI Visual Studio） | 対象外 | 40以上 |

数値はquality-gate.config.mjsで管理する。40ちょうどは通る。
TS測定はsrcのテストも含む。Rust測定はsrc-tauri/srcの全.rsファイルを対象にする。
行数警告は既存どおりPython・CSS・スクリプトも対象。Pythonの複雑度は今回の対象外。

## 既存違反

導入時の45件を `.clean/quality-baseline.json` に保存した。
ファイル・関数・指標ごとに照合し、新しい違反、件数増加、数値の悪化を失敗とする。
同じ名前の匿名関数は同一グループ内で悪い値から比較するため、匿名関数単位の識別には限界がある。
違反を改善・解消した場合も、古い許容値を残したままでは通らない。

```powershell
npm run quality:prune
git add .clean/quality-baseline.json
```

pruneは記録を縮めるだけで、新規違反や悪化を取り込まない。
HEADより記録を増やす編集も拒否する。関数名を変えた場合は新しい関数として扱う。
`npm run check:metrics -- --strict` は既存違反もすべてエラーにする。
既存コードを今回一括で整理したわけではない。

## 実行とフック

```powershell
npm ci
npm run setup:quality
npm run analyze
```

- pre-commit: ステージ済みの行数・依存境界・TS/Rustメトリクスを検査する。
- pre-push: 作業ツリーに対して全解析を実行する。pushするコミットの最終検証はCIでも行う。
- npm run check: 全解析に加え既存のテスト・型検査・ビルド・rustfmtを実行する。
- CI: push / pull_requestでcheckを実行し、JSONレポートを添付する。

測定コード・設定に未ステージ変更がある場合はpre-commitを止める。
検査ツールは作業ツリーのnode_modulesから読み、解析対象と比較記録はGitのindexから読む。
dependency-cruiser、cargo-modules、Clippyはpre-pushとCIで実行する。
ツール未導入、版の不一致、測定欠落、解析失敗はエラーにする。

レポートはtest-results/quality-gate.jsonとquality-metrics.json。
コミット時の測定はquality-metrics-staged.json。レポート内に既存違反も残す。
低速なRustモジュール検査は毎コミット実行しない。

## 依存検査

dependency-cruiserで循環依存・孤立ファイル・解決できないimportと、現在のUI境界を検査する。
main.tsx、テスト、型宣言は起点になり得るため孤立判定から除く。
UIのTauri呼び出しはapi.ts / useCloseSave.tsへ限定し、componentsは操作をpropsで受け取る。
types/editingからUIへの逆依存は禁止する。既存の字句検査も残す。
Rustはcargo-modulesでライブラリの循環依存と孤立モジュールを検査する。
循環判定は出力されたuses辺を所属モジュールへ集約する。owns辺や同一モジュール内の
型とDrop実装の関係は除く。cargo-modulesの全アイテム向けacyclicをそのまま使うと、
この所有関係も循環と判定されるため。ツールが報告しない動的な呼び出しは対象外。

Rustツールはcargo-modules 0.27.0、rust-code-analysis-cli 0.0.25に固定する。
JSツールはpackage-lock.jsonで固定。更新時は測定差を確認し、記録の再生成で違反を隠さない。
