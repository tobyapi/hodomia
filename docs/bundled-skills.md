# 同梱する文章スキル

文章の執筆・編集に使うスキルを `.agents/skills/` に実ファイルとして保存する。
サブモジュールや個人環境へのリンクは使わず、このリポジトリだけで参照できる。
実行コードや文章lintではないため、Gitフックで文体を自動採点する機能はない。
適用対象はAGENTS.mdで指定する。

| スキル | 取得元 | 固定コミット | ライセンス |
| --- | --- | --- | --- |
| stop-ai-slop-jp | https://github.com/iKora128/stop-ai-slop-jp | e09d32796f253a62693885757cea484c275d06f2 | MIT |
| stop-slop | https://github.com/hardikpandya/stop-slop | 8da1f030185bdfe8471220585162991eaeb970e9 | MIT |

取得日: 2026-09-21。各配布元のSKILL.md、references、README、CHANGELOG、LICENSEを保持している。
上流の本文は変更していない。著作権表示はそれぞれのLICENSEに含まれる。

更新時は上流コミットを指定して別の一時ディレクトリへ取得し、差分を確認する。
採用するファイルを同梱先へ反映し、この表のコミットを更新して一緒にコミットする。
参照ファイルが揃っていることと `npm run check` の成功を確認する。
